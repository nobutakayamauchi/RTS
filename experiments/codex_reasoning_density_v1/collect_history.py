#!/usr/bin/env python3
"""Read-only Codex history inventory and normalization.

The collector intentionally avoids auth/config secret files and does not copy raw
prompt/response text by default. It is designed for historical-baseline work, not
for modifying Codex state.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import re
import socket
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

USAGE_KEYS = {
    "input_tokens",
    "cached_input_tokens",
    "cache_write_input_tokens",
    "output_tokens",
    "reasoning_output_tokens",
    "total_tokens",
}

SENSITIVE_BASENAMES = {
    "auth.json",
    "config.toml",
    "credentials.json",
    "secrets.json",
    ".env",
}

BENCHMARK_NAMES = (
    ".benchmark-results",
    "EXP-005-HOST",
    "WISH-KILL",
)

TEXT_KEYS = ("text", "content", "message", "prompt", "input")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def safe_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return None


def walk_dicts(obj: Any) -> Iterable[dict[str, Any]]:
    if isinstance(obj, dict):
        yield obj
        for value in obj.values():
            yield from walk_dicts(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from walk_dicts(value)


def first_value(obj: Any, keys: tuple[str, ...]) -> Any:
    for mapping in walk_dicts(obj):
        for key in keys:
            if key in mapping and mapping[key] not in (None, "", [], {}):
                return mapping[key]
    return None


def extract_event_type(obj: dict[str, Any]) -> str:
    direct = obj.get("type") or obj.get("event") or obj.get("kind")
    if isinstance(direct, str):
        return direct
    payload = obj.get("payload")
    if isinstance(payload, dict):
        nested = payload.get("type") or payload.get("event") or payload.get("kind")
        if isinstance(nested, str):
            return nested
    return ""


def normalize_usage(mapping: Any) -> dict[str, int]:
    if not isinstance(mapping, dict):
        return {}
    out: dict[str, int] = {}
    for key in USAGE_KEYS:
        value = safe_int(mapping.get(key))
        if value is not None and value >= 0:
            out[key] = value
    return out


def extract_usage(obj: dict[str, Any]) -> dict[str, int]:
    best: dict[str, int] = {}
    for mapping in walk_dicts(obj):
        candidate = normalize_usage(mapping)
        if len(candidate) > len(best):
            best = candidate
    return best


def extract_token_count_snapshot(obj: dict[str, Any]) -> tuple[dict[str, int], dict[str, int]] | None:
    """Extract Codex session event_msg/token_count total + last-turn usage.

    Observed Codex session schema:
      payload.type == token_count
      payload.info.total_token_usage
      payload.info.last_token_usage

    total_token_usage is cumulative for the session; last_token_usage is the
    immediately preceding turn. We preserve both instead of summing snapshots.
    """
    for mapping in walk_dicts(obj):
        if mapping.get("type") != "token_count":
            continue
        info = mapping.get("info")
        if not isinstance(info, dict):
            continue
        total = normalize_usage(info.get("total_token_usage"))
        last = normalize_usage(info.get("last_token_usage"))
        if total:
            return total, last
    return None


def usage_delta_matches(previous: dict[str, int], current: dict[str, int], last: dict[str, int]) -> bool:
    """Return true when cumulative delta exactly reproduces last_token_usage.

    Only keys present in last_token_usage are checked. This is evidence that the
    session stream is cumulative rather than a collection of independent usage
    rows; it is not a claim about billing semantics outside the observed stream.
    """
    if not previous or not current or not last:
        return False
    checked = 0
    for key, last_value in last.items():
        if key not in previous or key not in current:
            continue
        if current[key] - previous[key] != last_value:
            return False
        checked += 1
    return checked >= 2


def extract_text(obj: dict[str, Any]) -> str | None:
    for mapping in walk_dicts(obj):
        role = mapping.get("role")
        if role not in (None, "user", "developer"):
            continue
        for key in TEXT_KEYS:
            value = mapping.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return None


def detect_version() -> str | None:
    try:
        proc = subprocess.run(
            ["codex", "--version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    text = (proc.stdout or proc.stderr).strip()
    return text or None


@dataclass
class SessionRow:
    session_file: str
    modified_at: str
    size_bytes: int
    session_id: str | None
    started_at: str | None
    ended_at: str | None
    model: str | None
    cwd: str | None
    provider: str | None
    token_count_events: int
    token_count_delta_verified: bool | None
    turn_completed_events: int
    generic_usage_events: int
    input_tokens: int | None
    cached_input_tokens: int | None
    cache_write_input_tokens: int | None
    output_tokens: int | None
    reasoning_output_tokens: int | None
    total_tokens: int | None
    last_input_tokens: int | None
    last_cached_input_tokens: int | None
    last_cache_write_input_tokens: int | None
    last_output_tokens: int | None
    last_reasoning_output_tokens: int | None
    last_total_tokens: int | None
    usage_method: str
    usage_confidence: str
    task_sha256: str | None
    task_chars: int | None
    task_preview: str | None
    approval_like_events: int
    error_like_events: int
    parse_errors: int


def sum_usage(events: list[dict[str, int]]) -> dict[str, int]:
    totals = {key: 0 for key in USAGE_KEYS}
    seen = {key: False for key in USAGE_KEYS}
    for event in events:
        for key, value in event.items():
            if key in totals:
                totals[key] += value
                seen[key] = True
    return {key: totals[key] for key in USAGE_KEYS if seen[key]}


def parse_session(path: Path, include_preview: bool) -> SessionRow:
    token_count_totals: list[dict[str, int]] = []
    token_count_last: list[dict[str, int]] = []
    turn_usage: list[dict[str, int]] = []
    generic_usage: list[dict[str, int]] = []
    session_id = started_at = ended_at = model = cwd = provider = None
    first_task = None
    approval_like = error_like = parse_errors = 0

    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for raw in handle:
            raw = raw.strip()
            if not raw:
                continue
            try:
                obj = json.loads(raw)
            except json.JSONDecodeError:
                parse_errors += 1
                continue
            if not isinstance(obj, dict):
                continue

            event_type = extract_event_type(obj)
            event_lower = event_type.lower()
            if any(word in event_lower for word in ("approval", "permission", "confirm")):
                approval_like += 1
            if any(word in event_lower for word in ("error", "failed", "failure")):
                error_like += 1

            session_id = session_id or first_value(obj, ("session_id", "thread_id", "conversation_id", "id"))
            model = model or first_value(obj, ("model", "model_id"))
            cwd = cwd or first_value(obj, ("cwd", "workdir", "working_directory"))
            provider = provider or first_value(obj, ("provider", "model_provider"))

            timestamp = first_value(obj, ("timestamp", "created_at", "time"))
            if isinstance(timestamp, str):
                started_at = started_at or timestamp
                ended_at = timestamp

            if first_task is None:
                first_task = extract_text(obj)

            token_snapshot = extract_token_count_snapshot(obj)
            if token_snapshot:
                total, last = token_snapshot
                token_count_totals.append(total)
                token_count_last.append(last)
                continue

            usage = extract_usage(obj)
            if usage:
                normalized_type = event_lower.replace("_", ".").replace("-", ".")
                if "turn.completed" in normalized_type or ("turn" in normalized_type and "complete" in normalized_type):
                    turn_usage.append(usage)
                else:
                    generic_usage.append(usage)

    delta_verified: bool | None = None
    last_totals: dict[str, int] = {}
    if token_count_totals:
        totals = token_count_totals[-1]
        last_totals = token_count_last[-1] if token_count_last else {}
        if len(token_count_totals) >= 2 and last_totals:
            delta_verified = usage_delta_matches(token_count_totals[-2], token_count_totals[-1], last_totals)
        method = "FINAL_TOKEN_COUNT_TOTAL"
        confidence = "HIGH"
    elif turn_usage:
        totals = sum_usage(turn_usage)
        method = "SUM_TURN_COMPLETED"
        confidence = "HIGH"
    elif generic_usage:
        # Generic events may be cumulative snapshots. Use the final snapshot instead
        # of summing to avoid obvious double counting.
        totals = generic_usage[-1]
        method = "FINAL_GENERIC_USAGE_SNAPSHOT"
        confidence = "LOW"
    else:
        totals = {}
        method = "NO_USAGE_FOUND"
        confidence = "NONE"

    stat = path.stat()
    preview = None
    task_hash = None
    task_chars = None
    if first_task:
        task_hash = sha256_text(first_task)
        task_chars = len(first_task)
        if include_preview:
            preview = re.sub(r"\s+", " ", first_task)[:160]

    def scalar(value: Any) -> str | None:
        if value is None:
            return None
        if isinstance(value, (str, int, float, bool)):
            return str(value)
        return None

    return SessionRow(
        session_file=str(path),
        modified_at=datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
        size_bytes=stat.st_size,
        session_id=scalar(session_id),
        started_at=scalar(started_at),
        ended_at=scalar(ended_at),
        model=scalar(model),
        cwd=scalar(cwd),
        provider=scalar(provider),
        token_count_events=len(token_count_totals),
        token_count_delta_verified=delta_verified,
        turn_completed_events=len(turn_usage),
        generic_usage_events=len(generic_usage),
        input_tokens=totals.get("input_tokens"),
        cached_input_tokens=totals.get("cached_input_tokens"),
        cache_write_input_tokens=totals.get("cache_write_input_tokens"),
        output_tokens=totals.get("output_tokens"),
        reasoning_output_tokens=totals.get("reasoning_output_tokens"),
        total_tokens=totals.get("total_tokens"),
        last_input_tokens=last_totals.get("input_tokens"),
        last_cached_input_tokens=last_totals.get("cached_input_tokens"),
        last_cache_write_input_tokens=last_totals.get("cache_write_input_tokens"),
        last_output_tokens=last_totals.get("output_tokens"),
        last_reasoning_output_tokens=last_totals.get("reasoning_output_tokens"),
        last_total_tokens=last_totals.get("total_tokens"),
        usage_method=method,
        usage_confidence=confidence,
        task_sha256=task_hash,
        task_chars=task_chars,
        task_preview=preview,
        approval_like_events=approval_like,
        error_like_events=error_like,
        parse_errors=parse_errors,
    )


def discover_sessions(codex_home: Path) -> list[Path]:
    root = codex_home / "sessions"
    if not root.exists():
        return []
    return sorted(path for path in root.rglob("*.jsonl") if path.is_file())


def inventory_codex_files(codex_home: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not codex_home.exists():
        return rows
    for path in codex_home.rglob("*"):
        if not path.is_file():
            continue
        if path.name in SENSITIVE_BASENAMES:
            continue
        try:
            rel = path.relative_to(codex_home)
            stat = path.stat()
        except OSError:
            continue
        rows.append(
            {
                "path": str(rel),
                "size_bytes": stat.st_size,
                "modified_at": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
            }
        )
    rows.sort(key=lambda row: row["path"])
    return rows


def discover_benchmark_paths(home: Path) -> list[dict[str, Any]]:
    candidates: list[Path] = []
    roots = [home / "WITNESS", home / "TRACE", home / "RTS", home]
    seen: set[str] = set()

    for root in roots:
        if not root.exists():
            continue
        iterator = root.iterdir() if root == home else root.rglob("*")
        try:
            for path in iterator:
                name = path.name
                if name in BENCHMARK_NAMES or name.startswith("EXP-") or name == "WISH-KILL":
                    key = str(path.resolve())
                    if key not in seen:
                        seen.add(key)
                        candidates.append(path)
        except (OSError, PermissionError):
            continue

    output: list[dict[str, Any]] = []
    for path in sorted(candidates):
        try:
            stat = path.stat()
            output.append(
                {
                    "path": str(path),
                    "is_dir": path.is_dir(),
                    "size_bytes": stat.st_size if path.is_file() else None,
                    "modified_at": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
                }
            )
        except OSError:
            continue
    return output


def write_csv(path: Path, rows: list[SessionRow]) -> None:
    fieldnames = list(SessionRow.__dataclass_fields__.keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex-home", type=Path, default=Path.home() / ".codex")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--include-task-preview",
        action="store_true",
        help="Include at most 160 chars of the first user/developer text. Off by default.",
    )
    args = parser.parse_args()

    codex_home = args.codex_home.expanduser().resolve()
    output = args.output.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)

    sessions: list[SessionRow] = []
    for session_path in discover_sessions(codex_home):
        try:
            sessions.append(parse_session(session_path, args.include_task_preview))
        except (OSError, PermissionError) as exc:
            print(f"WARN: failed to parse {session_path}: {exc}", file=sys.stderr)

    inventory = {
        "schema": "codex-history-inventory/v2",
        "generated_at": utc_now(),
        "host": {
            "hostname": socket.gethostname(),
            "platform": platform.platform(),
            "python": platform.python_version(),
        },
        "codex": {
            "version": detect_version(),
            "home": str(codex_home),
            "session_count": len(sessions),
        },
        "privacy": {
            "raw_prompt_response_copied": bool(args.include_task_preview),
            "task_preview_max_chars": 160 if args.include_task_preview else 0,
            "sensitive_files_excluded": sorted(SENSITIVE_BASENAMES),
        },
        "usage_semantics": {
            "token_count_total": "final total_token_usage is treated as session cumulative usage",
            "token_count_last": "last_token_usage is preserved as the immediately preceding turn",
            "delta_verified": "true only when previous cumulative total delta reproduces last_token_usage on >=2 comparable fields",
            "generic_usage": "final generic snapshot only; confidence remains LOW",
        },
        "files": inventory_codex_files(codex_home),
        "benchmark_paths": discover_benchmark_paths(Path.home()),
        "sessions": [asdict(row) for row in sessions],
    }

    with (output / "historical_baseline.json").open("w", encoding="utf-8") as handle:
        json.dump(inventory, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
    write_csv(output / "historical_baseline.csv", sessions)

    high = sum(1 for row in sessions if row.usage_confidence == "HIGH")
    low = sum(1 for row in sessions if row.usage_confidence == "LOW")
    no_usage = sum(1 for row in sessions if row.usage_confidence == "NONE")
    verified_delta = sum(1 for row in sessions if row.token_count_delta_verified is True)
    summary = {
        "session_count": len(sessions),
        "usage_high_confidence": high,
        "usage_low_confidence": low,
        "usage_not_found": no_usage,
        "token_count_delta_verified_sessions": verified_delta,
        "benchmark_path_count": len(inventory["benchmark_paths"]),
        "codex_version": inventory["codex"]["version"],
    }
    with (output / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")

    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    print(f"Wrote: {output / 'historical_baseline.json'}")
    print(f"Wrote: {output / 'historical_baseline.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

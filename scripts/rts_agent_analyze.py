#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
RTS Agent Analyze (Zero-Complete)
- Generates analyze/agent_index.md by scanning Run logs.
- Adds SUCCESS evaluation + SPAGHETTI detection (structure-only).
- No signature compare (v1). This is v0 "zero-complete".

Supported Run log locations (auto-detected):
- logs/RUN_*.md
- logs/runs/*.md
- runs/*.md

Supported Run format (YAML-ish markdown):

# RUN
- run_id: 2026-02-25_142233_clientA_agentX
- created_at: 2026-02-25T14:22:33+09:00
- operator: Nobutaka Yamauchi
- system: agentX
- goal: ...
- mode: auto | semi | manual
- success_flag: unknown | verified

## SPAN 000
- span_id: "000"
- parent_span_id: null
- node_type: planner
- status: ok | warn | fail | drift | verified
- tool_name: web.search   (optional)

(Any missing fields are tolerated.)
"""

from __future__ import annotations

import os
import re
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional


# -----------------------
# Paths (repo-relative)
# -----------------------
REPO_ROOT = Path(__file__).resolve().parents[1]
ANALYZE_DIR = REPO_ROOT / "analyze"
ANALYZE_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_MD = ANALYZE_DIR / "agent_index.md"
OUTPUT_JSON = ANALYZE_DIR / "agent_index.json"  # optional machine-read


# -----------------------
# Utilities
# -----------------------
def _safe_lower(s: Optional[str]) -> str:
    return (s or "").strip().lower()


def _now_iso() -> str:
    # Keep timezone naive; GitHub Actions logs are UTC anyway
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _sha256_bytes(b: bytes) -> str:
    h = hashlib.sha256()
    h.update(b)
    return h.hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


# -----------------------
# Run discovery
# -----------------------
def discover_run_files() -> List[Path]:
    patterns = [
        REPO_ROOT / "logs",
        REPO_ROOT / "logs" / "runs",
        REPO_ROOT / "runs",
    ]

    files: List[Path] = []

    # logs/RUN_*.md
    logs_dir = REPO_ROOT / "logs"
    if logs_dir.exists():
        files.extend(sorted(logs_dir.glob("RUN_*.md")))

    # logs/runs/*.md
    logs_runs = REPO_ROOT / "logs" / "runs"
    if logs_runs.exists():
        files.extend(sorted(logs_runs.glob("*.md")))

    # runs/*.md
    runs_dir = REPO_ROOT / "runs"
    if runs_dir.exists():
        files.extend(sorted(runs_dir.glob("*.md")))

    # de-dup
    uniq = []
    seen = set()
    for f in files:
        rp = str(f.resolve())
        if rp not in seen:
            uniq.append(f)
            seen.add(rp)
    return uniq


# -----------------------
# Parsing (YAML-ish list lines)
# -----------------------
KV_LINE = re.compile(r"^\s*-\s*([A-Za-z0-9_]+)\s*:\s*(.*)\s*$")
SPAN_HEADER = re.compile(r"^\s*##\s*SPAN\s+([0-9A-Za-z_\-]+)\s*$", re.IGNORECASE)
RUN_HEADER = re.compile(r"^\s*#\s*RUN\s*$", re.IGNORECASE)


def parse_run_markdown(md: str) -> Tuple[Dict[str, str], List[Dict[str, str]]]:
    """
    Returns:
      run_meta: dict
      spans: list of dict (each span fields)
    """
    lines = md.splitlines()

    run_meta: Dict[str, str] = {}
    spans: List[Dict[str, str]] = []

    in_run = False
    current_span: Optional[Dict[str, str]] = None

    for line in lines:
        if RUN_HEADER.match(line):
            in_run = True
            current_span = None
            continue

        m_span = SPAN_HEADER.match(line)
        if m_span:
            # close previous span
            if current_span is not None:
                spans.append(current_span)
            current_span = {"span_header": m_span.group(1)}
            continue

        m_kv = KV_LINE.match(line)
        if m_kv:
            k = m_kv.group(1).strip()
            v = m_kv.group(2).strip()

            # normalize null-ish
            if _safe_lower(v) in {"null", "none", ""}:
                v = ""

            if current_span is not None:
                current_span[k] = v
            elif in_run:
                run_meta[k] = v

    if current_span is not None:
        spans.append(current_span)

    return run_meta, spans


# -----------------------
# Classification (Zero-complete)
# -----------------------
def _is_fail(st: str) -> bool:
    return _safe_lower(st) == "fail"


def _is_drift(st: str) -> bool:
    return _safe_lower(st) == "drift"


def _is_verified(st: str) -> bool:
    return _safe_lower(st) == "verified"


def _count_missing(spans: List[Dict[str, str]]) -> int:
    missing = 0
    for s in spans:
        node = s.get("node_type", "")
        st = s.get("status", "")
        if not _safe_lower(node) or not _safe_lower(st):
            missing += 1
    return missing


def _extract_tool_names(spans: List[Dict[str, str]]) -> List[str]:
    tools = []
    for s in spans:
        tool = (s.get("tool_name", "") or "").strip()
        tools.append(tool)
    return tools


def _tool_call_ratio(spans: List[Dict[str, str]]) -> float:
    tools = _extract_tool_names(spans)
    tool_calls = sum(1 for t in tools if t)
    return tool_calls / max(1, len(spans))


def _max_consecutive_same_tool(spans: List[Dict[str, str]]) -> int:
    tools = _extract_tool_names(spans)
    best = 0
    cur = 0
    prev = None
    for t in tools:
        if t and t == prev:
            cur += 1
        else:
            cur = 1 if t else 0
        prev = t if t else None
        best = max(best, cur)
    return best


def classify_run(
    spans: List[Dict[str, str]],
    run_success_flag: str = "unknown",
    *,
    spaghetti_span_threshold: int = 80,
    spaghetti_tool_ratio_threshold: float = 0.60,
    spaghetti_same_tool_streak: int = 4,
    spaghetti_missing_ratio_threshold: float = 0.20,
) -> Tuple[str, List[str]]:
    """
    Returns: (classification: str, reasons: list[str])

    Labels:
      FAIL | DRIFT | SPAGHETTI | OK | VERIFIED

    Notes:
      - VERIFIED is explicit only in zero-complete:
        - run header: success_flag: verified
        - or any span has status: verified
      - No signature compare (v1)
      - Structure-only spaghetti heuristics
    """
    reasons: List[str] = []

    statuses = [_safe_lower(s.get("status", "")) for s in spans]

    if any(_is_fail(st) for st in statuses):
        return "FAIL", ["fail_span_detected"]

    if any(_is_drift(st) for st in statuses):
        return "DRIFT", ["drift_span_detected"]

    # verified explicit
    if _safe_lower(run_success_flag) == "verified" or any(_is_verified(st) for st in statuses):
        return "VERIFIED", ["explicit_verified_marker"]

    # spaghetti heuristics (structure-only)
    span_count = len(spans)
    if span_count >= spaghetti_span_threshold:
        reasons.append(f"span_count_high:{span_count}")

    ratio = _tool_call_ratio(spans)
    if ratio > spaghetti_tool_ratio_threshold:
        reasons.append(f"tool_call_ratio_high:{ratio:.2f}")

    streak = _max_consecutive_same_tool(spans)
    if streak >= spaghetti_same_tool_streak:
        reasons.append(f"same_tool_streak:{streak}")

    missing = _count_missing(spans)
    missing_ratio = missing / max(1, span_count)
    if missing_ratio > spaghetti_missing_ratio_threshold:
        reasons.append(f"missing_fields_ratio:{missing_ratio:.2f}")

    if reasons:
        return "SPAGHETTI", reasons

    return "OK", ["no_anomaly_detected"]


# -----------------------
# Report generation
# -----------------------
def make_md_index(rows: List[Dict[str, str]]) -> str:
    lines: List[str] = []
    lines.append("# RTS Agent Index")
    lines.append("")
    lines.append(f"- generated_at: {_now_iso()}")
    lines.append("")
    lines.append("This page lists Runs and their structural evaluation.")
    lines.append("")
    lines.append("## Legend")
    lines.append("- VERIFIED: explicitly marked verified (no signature compare in v0)")
    lines.append("- OK: no fail/drift/spaghetti signals")
    lines.append("- DRIFT: explicit drift spans exist")
    lines.append("- SPAGHETTI: success-looking but structurally suspicious")
    lines.append("- FAIL: at least one fail span")
    lines.append("")
    lines.append("## Runs")
    lines.append("")
    lines.append("| created_at | run_id | system | mode | result | reasons | source |")
    lines.append("|---|---|---|---|---|---|---|")

    for r in rows:
        created_at = r.get("created_at", "")
        run_id = r.get("run_id", "")
        system = r.get("system", "") or r.get("agent_stack", "") or ""
        mode = r.get("mode", "")
        result = r.get("classification", "")
        reasons = r.get("reasons", "")
        src = r.get("source_path", "")

        # Make repo-relative link
        src_link = src.replace(str(REPO_ROOT) + os.sep, "")
        lines.append(
            f"| {created_at} | `{run_id}` | {system} | {mode} | **{result}** | {reasons} | `{src_link}` |"
        )

    lines.append("")
    lines.append("## Notes")
    lines.append("- This is v0 zero-complete. v1 adds Success Signature compare.")
    lines.append("")
    return "\n".join(lines)


def build_index() -> int:
    run_files = discover_run_files()
    rows: List[Dict[str, str]] = []

    for f in run_files:
        md = _read_text(f)
        meta, spans = parse_run_markdown(md)

        run_id = meta.get("run_id", "") or f.stem
        created_at = meta.get("created_at", "") or meta.get("timestamp_start", "")
        mode = meta.get("mode", "")
        system = meta.get("system", "") or meta.get("agent_stack", "")

        success_flag = meta.get("success_flag", "unknown")

        cls, reasons = classify_run(spans, run_success_flag=success_flag)

        row = {
            "run_id": run_id,
            "created_at": created_at,
            "mode": mode,
            "system": system,
            "classification": cls,
            "reasons": ", ".join(reasons[:4]),  # keep short
            "source_path": str(f.resolve()),
            "span_count": str(len(spans)),
            "file_sha256": _sha256_file(f),
        }
        rows.append(row)

    # Sort: newest-ish first (created_at string sort may be rough; fallback by filename)
    def _sort_key(r: Dict[str, str]):
        return (r.get("created_at", ""), r.get("run_id", ""))

    rows_sorted = sorted(rows, key=_sort_key, reverse=True)

    OUTPUT_MD.write_text(make_md_index(rows_sorted), encoding="utf-8")
    OUTPUT_JSON.write_text(json.dumps(rows_sorted, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[OK] wrote: {OUTPUT_MD}")
    print(f"[OK] wrote: {OUTPUT_JSON}")
    print(f"[OK] runs scanned: {len(rows_sorted)}")
    return 0


def main() -> int:
    try:
        return build_index()
    except Exception as e:
        print("[ERROR]", e)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

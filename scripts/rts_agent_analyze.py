#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
RTS Agent Analyze ZERO (Hardened)
Execution Path Observer (Structure-only)

RTS does not judge semantics.
RTS reveals structure.

Inputs:
- runs/RUN_*.md

Outputs:
- analysis/agent_index.md
- analysis/agent_index.json

Safety fixes (v0 hardened):
- VERIFIED only upgrades OK (never overrides FAIL/DRIFT/SPAGHETTI)
- SPAGHETTI triggers are fixed to 3 (+ PARSE_ERROR)
- status normalization table (prevents FAIL miss)
- last-write-wins with conflict warnings
- stable file ordering
- per-file failure isolation (never breaks whole index)
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
import re
import json
from typing import Dict, List, Optional, Tuple


# -----------------------------
# Paths
# -----------------------------
ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = ROOT / "runs"
OUT_MD = ROOT / "analysis" / "agent_index.md"
OUT_JSON = ROOT / "analysis" / "agent_index.json"


# -----------------------------
# Regex (markdown-ish)
# -----------------------------
# Span header like:
# ## SPAN 000
# ## SPAN 010
SPAN_HDR_RE = re.compile(r"(?m)^\s*##\s*SPAN\s+(\d+)\s*$")

# YAML-ish key: value (inline)
KV_INLINE_RE = re.compile(r"(?m)^\s*[-*]\s*([A-Za-z0-9_]+)\s*:\s*(.*?)\s*$")

# YAML-ish key:\n  value (block-ish)
KV_BLOCK_KEY_RE = re.compile(r"(?m)^\s*[-*]\s*([A-Za-z0-9_]+)\s*:\s*$")


# -----------------------------
# Normalization (STATUS)
# -----------------------------
STATUS_MAP = {
    # ok
    "ok": "ok",
    "pass": "ok",
    "passed": "ok",
    "success": "ok",
    "succeeded": "ok",
    "green": "ok",
    "done": "ok",
    # warn
    "warn": "warn",
    "warning": "warn",
    "softfail": "warn",
    "unstable": "warn",
    "degraded": "warn",
    # fail
    "fail": "fail",
    "failed": "fail",
    "error": "fail",
    "err": "fail",
    "exception": "fail",
    "panic": "fail",
    "red": "fail",
    # drift
    "drift": "drift",
    "suspicious": "drift",
    "anomaly": "drift",
    "weird": "drift",
}


def normalize_status(raw: Optional[str]) -> Optional[str]:
    if raw is None:
        return None
    s = str(raw).strip().lower()
    if s == "" or s in ("null", "none"):
        return None
    return STATUS_MAP.get(s)  # unknown => None (missingness)


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def normalize_span_id(raw: Optional[str], fallback_from_hdr: Optional[str] = None) -> Optional[str]:
    """
    - Prefer explicit span_id if present
    - Else fallback to header number
    - 0-pad to 3 digits for <1000
    - allow >=1000 as-is
    """
    v = raw if raw is not None else fallback_from_hdr
    if v is None:
        return None
    v = str(v).strip().strip('"').strip("'")
    if v == "" or v.lower() in ("null", "none"):
        return None
    # if numeric, normalize
    if v.isdigit():
        n = int(v)
        if n < 1000:
            return str(n).zfill(3)
        return str(n)
    # non-numeric ids: keep as-is
    return v


def parse_value_token(v: str) -> Optional[str]:
    """
    Normalize null-like tokens and strip quotes.
    """
    if v is None:
        return None
    s = str(v).strip()
    if s == "" or s.lower() in ("null", "none"):
        return None
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        s = s[1:-1].strip()
    return s if s != "" else None


def last_write_wins_set(store: Dict[str, Optional[str]], key: str, value: Optional[str], conflicts: List[str]) -> None:
    """
    last-write-wins + conflict log
    """
    if key in store and store[key] != value:
        conflicts.append(key)
    store[key] = value


@dataclass
class Span:
    span_id: Optional[str]
    parent_span_id: Optional[str]
    node_type: Optional[str]
    status: Optional[str]          # normalized
    tool_name: Optional[str]
    error: Optional[str]
    order_index: Optional[int]


@dataclass
class RunSummary:
    name: str
    relpath: str
    run_id: Optional[str]
    mode: Optional[str]
    success_flag: Optional[str]
    config_fingerprint: Optional[str]

    span_count: int
    fail_count: int
    drift_count: int
    warn_count: int
    missing_status_rate: float

    classification: str  # FAIL/DRIFT/SPAGHETTI/OK/VERIFIED
    spaghetti_reason_codes: List[str]
    conflict_keys: List[str]


# -----------------------------
# Parsing
# -----------------------------
def split_into_span_blocks(text: str) -> List[Tuple[str, str]]:
    """
    Returns list of (span_hdr_number, span_block_text)
    """
    matches = list(SPAN_HDR_RE.finditer(text))
    blocks: List[Tuple[str, str]] = []
    if not matches:
        return blocks

    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        span_num = m.group(1)
        blocks.append((span_num, text[start:end]))
    return blocks


def extract_kv_pairs(block: str) -> Tuple[Dict[str, Optional[str]], List[str]]:
    """
    Extracts key/values using inline and block patterns.
    last-write-wins with conflicts list.
    """
    store: Dict[str, Optional[str]] = {}
    conflicts: List[str] = []

    # Inline first in order of appearance
    for m in KV_INLINE_RE.finditer(block):
        k = m.group(1)
        v = parse_value_token(m.group(2))
        last_write_wins_set(store, k, v, conflicts)

    # Block keys: take the next non-empty, non-list-marker line as value
    for m in KV_BLOCK_KEY_RE.finditer(block):
        k = m.group(1)
        # find next lines after this match
        after = block[m.end():]
        val: Optional[str] = None
        for line in after.splitlines():
            t = line.strip()
            if t == "":
                continue
            # stop if another key starts
            if re.match(r"^[-*]\s*[A-Za-z0-9_]+\s*:", t):
                break
            # list item -> treat as value token (first item only)
            if t.startswith("- "):
                val = parse_value_token(t[2:].strip())
                break
            # plain line
            val = parse_value_token(t)
            break
        if val is not None:
            last_write_wins_set(store, k, val, conflicts)

    # de-dup conflict keys
    conflicts = sorted(set(conflicts))
    return store, conflicts


def parse_run_header(text: str) -> Tuple[Dict[str, Optional[str]], List[str]]:
    """
    Very forgiving: treat everything before first SPAN header as header region.
    """
    blocks = split_into_span_blocks(text)
    header = text
    if blocks:
        first_span_num, first_span_block = blocks[0]
        # header is before first span header
        header = text[: text.find(first_span_block)]
    kv, conflicts = extract_kv_pairs(header)
    return kv, conflicts


def parse_spans(text: str) -> Tuple[List[Span], List[str]]:
    spans: List[Span] = []
    conflicts_all: List[str] = []

    blocks = split_into_span_blocks(text)
    for idx, (span_num, block) in enumerate(blocks):
        kv, conflicts = extract_kv_pairs(block)
        conflicts_all.extend([f"SPAN:{span_num}:{c}" for c in conflicts])

        span_id = normalize_span_id(kv.get("span_id"), fallback_from_hdr=span_num)
        parent_id = normalize_span_id(kv.get("parent_span_id"))
        node_type = parse_value_token(kv.get("node_type") or kv.get("node") or kv.get("action_type"))
        tool_name = parse_value_token(kv.get("tool_name"))
        error = parse_value_token(kv.get("error"))

        status_raw = kv.get("status")
        status = normalize_status(status_raw)

        order_index = None
        oi = kv.get("order_index")
        if oi and str(oi).strip().isdigit():
            order_index = int(str(oi).strip())
        else:
            # fallback: file order
            order_index = idx

        spans.append(
            Span(
                span_id=span_id,
                parent_span_id=parent_id,
                node_type=node_type,
                status=status,
                tool_name=tool_name,
                error=error,
                order_index=order_index,
            )
        )

    # de-dup
    conflicts_all = sorted(set(conflicts_all))
    return spans, conflicts_all


def detect_verified(text: str) -> bool:
    """
    VERIFIED marker is explicit and must be unambiguous.
    Accepts:
    - verified: true
    - classification: VERIFIED
    - verified_flag: true
    """
    t = text.lower()
    if re.search(r"(?m)^\s*[-*]\s*verified\s*:\s*true\s*$", t):
        return True
    if re.search(r"(?m)^\s*[-*]\s*verified_flag\s*:\s*true\s*$", t):
        return True
    if re.search(r"(?m)^\s*[-*]\s*classification\s*:\s*verified\s*$", t):
        return True
    return False


# -----------------------------
# SPAGHETTI triggers (fixed)
# -----------------------------
def spaghetti_reason_codes(spans: List[Span], parse_error: bool) -> List[str]:
    reasons: List[str] = []

    if parse_error:
        reasons.append("PARSE_ERROR")
        return reasons

    # 1) DUP_SPAN_ID
    ids = [s.span_id for s in spans if s.span_id is not None]
    if len(ids) != len(set(ids)):
        reasons.append("DUP_SPAN_ID")

    # 2) MISSING_PARENT (only if parent info exists)
    idset = set(ids)
    has_parent_info = any(s.parent_span_id not in (None, "") for s in spans)
    if has_parent_info:
        for s in spans:
            if s.parent_span_id is None:
                continue
            if s.parent_span_id not in idset:
                reasons.append("MISSING_PARENT")
                break

    # 3) HIGH_MISSING_STATUS (>50%)
    if spans:
        missing = sum(1 for s in spans if s.status is None)
        rate = missing / len(spans)
        if rate > 0.50:
            reasons.append("HIGH_MISSING_STATUS")

    return sorted(set(reasons))


# -----------------------------
# Classification (priority fixed)
# -----------------------------
def classify_run(spans: List[Span], verified_marker: bool, reasons: List[str]) -> str:
    # FAIL has highest priority
    if any(s.status == "fail" for s in spans):
        return "FAIL"
    # DRIFT next
    if any(s.status == "drift" for s in spans):
        return "DRIFT"
    # SPAGHETTI next (fixed triggers)
    if reasons:
        return "SPAGHETTI"
    # OK baseline
    base = "OK"
    # VERIFIED only upgrades OK
    if verified_marker:
        return "VERIFIED"
    return base


# -----------------------------
# Collect + Write outputs
# -----------------------------
def collect_runs() -> List[Path]:
    if not RUNS_DIR.exists():
        return []
    # stable ordering: ASCII filename sort
    return sorted(RUNS_DIR.glob("RUN_*.md"), key=lambda p: p.name)


def analyze_one_run(path: Path) -> RunSummary:
    name = path.name
    relpath = str(path.relative_to(ROOT))

    parse_error = False
    text = ""
    header_kv: Dict[str, Optional[str]] = {}
    header_conflicts: List[str] = []
    spans: List[Span] = []
    span_conflicts: List[str] = []

    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        header_kv, header_conflicts = parse_run_header(text)
        spans, span_conflicts = parse_spans(text)
    except Exception:
        parse_error = True
        spans = []

    verified_marker = detect_verified(text) if (not parse_error) else False

    # counts
    fail_count = sum(1 for s in spans if s.status == "fail")
    drift_count = sum(1 for s in spans if s.status == "drift")
    warn_count = sum(1 for s in spans if s.status == "warn")
    missing_status = sum(1 for s in spans if s.status is None)
    missing_rate = (missing_status / len(spans)) if spans else (1.0 if parse_error else 0.0)

    reasons = spaghetti_reason_codes(spans, parse_error=parse_error)
    classification = classify_run(spans, verified_marker=verified_marker, reasons=reasons)

    # header fields (best-effort, last-write-wins already applied in extractor)
    run_id = header_kv.get("run_id")
    mode = header_kv.get("mode")
    success_flag = header_kv.get("success_flag")
    config_fp = header_kv.get("config_fingerprint")

    conflict_keys = sorted(set(header_conflicts + span_conflicts))

    return RunSummary(
        name=name,
        relpath=relpath,
        run_id=run_id,
        mode=mode,
        success_flag=success_flag,
        config_fingerprint=config_fp,
        span_count=len(spans),
        fail_count=fail_count,
        drift_count=drift_count,
        warn_count=warn_count,
        missing_status_rate=round(missing_rate, 4),
        classification=classification,
        spaghetti_reason_codes=reasons,
        conflict_keys=conflict_keys,
    )


def write_outputs(items: List[RunSummary]) -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)

    generated = now_utc_iso()
    total = len(items)

    # summary counts
    counts: Dict[str, int] = {}
    for it in items:
        counts[it.classification] = counts.get(it.classification, 0) + 1

    # markdown
    lines: List[str] = []
    lines.append("# RTS Agent Analyze ZERO — Index")
    lines.append("")
    lines.append(f"- generated_at_utc: {generated}")
    lines.append(f"- runs_count: {total}")
    lines.append("")
    lines.append("RTS observes agent execution structure only. No semantics. No judging.")
    lines.append("")

    # Summary
    lines.append("## Summary")
    for k in ["FAIL", "DRIFT", "SPAGHETTI", "OK", "VERIFIED"]:
        lines.append(f"- {k}: {counts.get(k, 0)}")
    lines.append("")

    # Table
    lines.append("## Runs")
    lines.append("| Run | Class | Spans | fail | drift | warn | miss_status | spaghetti_reason_codes |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---|")

    for it in items:
        href = f"../{it.relpath}"
        run_cell = f"[{it.name}]({href})"
        reasons = ",".join(it.spaghetti_reason_codes) if it.spaghetti_reason_codes else ""
        lines.append(
            f"| {run_cell} | {it.classification} | {it.span_count} | {it.fail_count} | {it.drift_count} | {it.warn_count} | {it.missing_status_rate} | {reasons} |"
        )

    lines.append("")
    lines.append("## Operator Notes")
    lines.append("- VERIFIED only upgrades OK. It never overrides FAIL/DRIFT/SPAGHETTI.")
    lines.append("- SPAGHETTI triggers are fixed: DUP_SPAN_ID / MISSING_PARENT / HIGH_MISSING_STATUS (+ PARSE_ERROR).")
    lines.append("- Unknown status tokens are treated as missing (to avoid false OK).")
    lines.append("")

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    # json
    payload = {
        "generated_at_utc": generated,
        "runs_count": total,
        "counts": counts,
        "items": [asdict(it) for it in items],
    }
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    paths = collect_runs()
    items: List[RunSummary] = []
    for p in paths:
        items.append(analyze_one_run(p))
    write_outputs(items)
    print(f"[OK] RTS Agent Analyze ZERO wrote: {OUT_MD} and {OUT_JSON} (runs={len(items)})")


if __name__ == "__main__":
    main()

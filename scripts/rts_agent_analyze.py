#!/usr/bin/env python3
# RTS Agent Analyze v0
# Execution Path Observer (Structure-only)
#
# RTS does not judge semantics.
# RTS reveals structure.
#
# Output:
#   analysis/agent_index.md
#
# Classification (5-tier):
#   - FAIL       : any span status=fail
#   - DRIFT      : any span status=drift OR suspicious WARN accumulation
#   - SPAGHETTI  : "worked once" risk (looping / excessive retries / unstable path)
#   - OK         : clean run (no drift/fail/spaghetti) but not explicitly verified
#   - VERIFIED   : explicitly marked success_flag true (or equivalent) + clean structure

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import re
from typing import Dict, List, Optional, Tuple


# -----------------------------
# Paths
# -----------------------------
ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = ROOT / "runs"
OUTPUT = ROOT / "analysis" / "agent_index.md"


# -----------------------------
# Regex (robust, markdown-ish)
# -----------------------------
# Matches span header like:
#   ## SPAN 000
#   ## SPAN 010
SPAN_HDR_RE = re.compile(r"(?m)^\s*##\s*SPAN\s+(\d{1,4})\s*$")

# YAML-ish bullet styles:
# - key: value
# - key:
#   value
KEY_LINE_RE = re.compile(r"(?m)^\s*[-*]\s*([a-zA-Z0-9_]+)\s*:\s*(.*)\s*$")

# Specific fields (keep forgiving)
STATUS_RE = re.compile(r"(?im)^\s*[-*]\s*status\s*:\s*(ok|warn|fail|drift)\s*$")
NODE_RE = re.compile(r"(?im)^\s*[-*]\s*node_type\s*:\s*([a-zA-Z0-9_]+)\s*$")
PARENT_RE = re.compile(r"(?im)^\s*[-*]\s*parent_span_id\s*:\s*(null|\"[0-9]+\"|[0-9]+)\s*$")
ORDER_RE = re.compile(r"(?im)^\s*[-*]\s*order_index\s*:\s*([0-9]+)\s*$")
TOOL_RE = re.compile(r"(?im)^\s*[-*]\s*tool_name\s*:\s*(.+?)\s*$")
ERROR_RE = re.compile(r"(?im)^\s*[-*]\s*error\s*:\s*(.+?)\s*$")

# Run header fields (top section bullets)
RUN_ID_RE = re.compile(r"(?im)^\s*[-*]\s*run_id\s*:\s*(.+?)\s*$")
SUCCESS_FLAG_RE = re.compile(r"(?im)^\s*[-*]\s*success_flag\s*:\s*(true|false|unknown)\s*$")
MODE_RE = re.compile(r"(?im)^\s*[-*]\s*mode\s*:\s*(auto|semi|manual)\s*$")
CONFIG_FP_RE = re.compile(r"(?im)^\s*[-*]\s*config_(fingerprint|fingerprint)\s*:\s*(.+?)\s*$")


# -----------------------------
# Data
# -----------------------------
@dataclass
class Span:
    span_id: str
    parent_span_id: Optional[str]
    node_type: str
    status: str
    order_index: Optional[int]
    tool_name: Optional[str]
    error: Optional[str]


@dataclass
class RunSummary:
    name: str
    relpath: str
    run_id: str
    mode: str
    success_flag: str
    config_fp: str
    spans: List[Span]
    mtime_iso: str
    classification: str
    reason: str
    loop_score: int
    drift_count: int
    fail_count: int
    warn_count: int


# -----------------------------
# Helpers
# -----------------------------
def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def safe_read_text(path: Path) -> str:
    # smartphone-friendly: ignore decode errors rather than crashing
    return path.read_text(encoding="utf-8", errors="replace")


def normalize_span_id(raw: str) -> str:
    # pad to 3 digits by default; allow larger but keep stable
    try:
        n = int(raw)
        if n < 0:
            return raw
        if n < 1000:
            return str(n).zfill(3)
        return str(n)  # 1000+ keep as-is
    except Exception:
        return raw


def parse_parent(v: str) -> Optional[str]:
    v = v.strip()
    if v.lower() == "null":
        return None
    v = v.strip('"')
    return normalize_span_id(v) if v else None


def parse_run_header(text: str) -> Tuple[str, str, str, str]:
    run_id = ""
    mode = "unknown"
    success_flag = "unknown"
    config_fp = ""

    m = RUN_ID_RE.search(text)
    if m:
        run_id = m.group(1).strip().strip('"')

    m = MODE_RE.search(text)
    if m:
        mode = m.group(1).strip().lower()

    m = SUCCESS_FLAG_RE.search(text)
    if m:
        success_flag = m.group(1).strip().lower()

    m = CONFIG_FP_RE.search(text)
    if m:
        config_fp = m.group(2).strip().strip('"')

    return run_id, mode, success_flag, config_fp


def split_spans(text: str) -> List[Tuple[str, str]]:
    """
    Returns list of (span_id, span_block_text).
    We locate span headers and slice blocks.
    """
    matches = list(SPAN_HDR_RE.finditer(text))
    out: List[Tuple[str, str]] = []
    if not matches:
        return out

    for i, m in enumerate(matches):
        sid = normalize_span_id(m.group(1))
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        block = text[start:end]
        out.append((sid, block))
    return out


def parse_span_block(span_id: str, block: str) -> Span:
    # defaults
    status = "ok"
    node_type = "other"
    parent = None
    order_index = None
    tool_name = None
    error = None

    m = STATUS_RE.search(block)
    if m:
        status = m.group(1).lower()

    m = NODE_RE.search(block)
    if m:
        node_type = m.group(1).strip().lower()

    m = PARENT_RE.search(block)
    if m:
        parent = parse_parent(m.group(1))

    m = ORDER_RE.search(block)
    if m:
        try:
            order_index = int(m.group(1))
        except Exception:
            order_index = None

    m = TOOL_RE.search(block)
    if m:
        tool_name = m.group(1).strip()

    m = ERROR_RE.search(block)
    if m:
        error = m.group(1).strip()

    return Span(
        span_id=span_id,
        parent_span_id=parent,
        node_type=node_type,
        status=status,
        order_index=order_index,
        tool_name=tool_name,
        error=error,
    )


def detect_loops(spans: List[Span]) -> int:
    """
    Structure-only loop/risk score.
    Higher = more likely 'SPAGHETTI' (miracle alignment / retry storm / hidden instability).
    """
    if not spans:
        return 0

    score = 0
    node_seq = [s.node_type for s in spans]

    # 1) consecutive repeats
    consec = 1
    for i in range(1, len(node_seq)):
        if node_seq[i] == node_seq[i - 1]:
            consec += 1
            if consec >= 3:
                score += 2  # repeated same node type 3+ times in a row
        else:
            consec = 1

    # 2) excessive executor/tool_call ratios
    exec_count = sum(1 for s in spans if s.node_type == "executor")
    tool_count = sum(1 for s in spans if s.node_type == "tool_call")
    retr_count = sum(1 for s in spans if s.node_type == "retrieval")

    total = max(1, len(spans))
    if exec_count / total > 0.70 and total >= 10:
        score += 3
    if tool_count / total > 0.60 and total >= 10:
        score += 3
    if retr_count / total > 0.60 and total >= 10:
        score += 2

    # 3) repeated tool_name (retry storm)
    tool_names = [s.tool_name for s in spans if s.tool_name]
    if tool_names:
        freq: Dict[str, int] = {}
        for t in tool_names:
            freq[t] = freq.get(t, 0) + 1
        max_tool = max(freq.values())
        if max_tool >= 5:
            score += 4
        elif max_tool >= 3:
            score += 2

    # 4) span count too large (cheap guardrail)
    # (world-use assumption: you don't want to eyeball 200+ spans per run)
    if total >= 200:
        score += 8
    elif total >= 80:
        score += 4
    elif total >= 40:
        score += 2

    # 5) parent structure anomalies (missing parents)
    span_ids = {s.span_id for s in spans}
    missing_parent = sum(
        1 for s in spans if s.parent_span_id is not None and s.parent_span_id not in span_ids
    )
    if missing_parent >= 1:
        score += 3

    return score


def classify_run(success_flag: str, spans: List[Span]) -> Tuple[str, str, int, int, int, int]:
    """
    Returns:
      (classification, reason, loop_score, drift_count, fail_count, warn_count)
    """
    fail_count = sum(1 for s in spans if s.status == "fail")
    drift_count = sum(1 for s in spans if s.status == "drift")
    warn_count = sum(1 for s in spans if s.status == "warn")
    loop_score = detect_loops(spans)

    if fail_count > 0:
        return ("FAIL", f"{fail_count} span(s) failed", loop_score, drift_count, fail_count, warn_count)

    # drift is explicit, and warn can be "soft drift" if it accumulates
    if drift_count > 0:
        return ("DRIFT", f"{drift_count} span(s) drift", loop_score, drift_count, fail_count, warn_count)

    if warn_count >= 2:
        return ("DRIFT", f"{warn_count} warnings (soft drift)", loop_score, drift_count, fail_count, warn_count)

    # spaghetti = structure looks OK but risky (loops/retries/excess)
    if loop_score >= 6:
        return ("SPAGHETTI", f"loop/risk score={loop_score}", loop_score, drift_count, fail_count, warn_count)

    # verified only if explicitly flagged and structure clean
    if success_flag == "true":
        return ("VERIFIED", "success_flag=true + clean structure", loop_score, drift_count, fail_count, warn_count)

    return ("OK", "no fail/drift detected", loop_score, drift_count, fail_count, warn_count)


def collect_runs() -> List[Path]:
    if not RUNS_DIR.exists():
        return []
    # Scale: thousands ok; tens of thousands still ok (simple filesystem + parse)
    return sorted(RUNS_DIR.glob("RUN_*.md"), key=lambda p: p.stat().st_mtime, reverse=True)


def md_link(text: str, href: str) -> str:
    return f"[{text}]({href})"


def to_rel(p: Path) -> str:
    try:
        return str(p.relative_to(ROOT)).replace("\\", "/")
    except Exception:
        return str(p).replace("\\", "/")


def parse_run_file(path: Path) -> RunSummary:
    text = safe_read_text(path)

    run_id, mode, success_flag, config_fp = parse_run_header(text)
    if not run_id:
        # fallback to filename (stable)
        run_id = path.stem.replace("RUN_", "")

    span_blocks = split_spans(text)
    spans: List[Span] = [parse_span_block(sid, block) for (sid, block) in span_blocks]

    classification, reason, loop_score, drift_count, fail_count, warn_count = classify_run(success_flag, spans)

    mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat(timespec="seconds")

    return RunSummary(
        name=path.name,
        relpath=to_rel(path),
        run_id=run_id,
        mode=mode,
        success_flag=success_flag,
        config_fp=config_fp,
        spans=spans,
        mtime_iso=mtime,
        classification=classification,
        reason=reason,
        loop_score=loop_score,
        drift_count=drift_count,
        fail_count=fail_count,
        warn_count=warn_count,
    )


def write_index(items: List[RunSummary]) -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    generated = now_utc_iso()
    total = len(items)

    # summary counts
    counts: Dict[str, int] = {}
    for it in items:
        counts[it.classification] = counts.get(it.classification, 0) + 1

    lines: List[str] = []
    lines.append("# RTS Agent Analyze Index")
    lines.append("")
    lines.append(f"- generated_at_utc: {generated}")
    lines.append(f"- runs_dir: {to_rel(RUNS_DIR)}")
    lines.append(f"- runs_count: {total}")
    lines.append("")
    lines.append("RTS observes agent execution paths. Structure only. No semantic judging.")
    lines.append("")

    # counts
    lines.append("## Summary")
    lines.append("")
    for k in ["VERIFIED", "OK", "DRIFT", "SPAGHETTI", "FAIL"]:
        lines.append(f"- {k}: {counts.get(k, 0)}")
    lines.append("")
    lines.append("> Definitions: VERIFIED=explicit clean success. OK=clean. DRIFT=soft anomaly. SPAGHETTI=miracle alignment risk. FAIL=hard failure.")
    lines.append("")

    # table
    lines.append("## Runs")
    lines.append("")
    lines.append("| Run | Class | Spans | Fail | Drift | Warn | LoopScore | Mode | Updated(UTC) | Notes |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---|---|---|")

    for it in items:
        href = f"../{it.relpath}"
        run_cell = md_link(it.name, href)
        notes = it.reason.replace("|", " ")
        lines.append(
            f"| {run_cell} | {it.classification} | {len(it.spans)} | {it.fail_count} | {it.drift_count} | {it.warn_count} | {it.loop_score} | {it.mode} | {it.mtime_iso} | {notes} |"
        )

    lines.append("")
    lines.append("## Operator Notes")
    lines.append("")
    lines.append("- This report is structure-first. It does not assert correctness of outputs.")
    lines.append("- If you need stronger auditability: attach evidence links or snapshot hashes per span/run.")
    lines.append("- Use SPAGHETTI as a warning: it may pass once but likely fails on replay.")
    lines.append("")

    OUTPUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    runs = collect_runs()
    items = [parse_run_file(p) for p in runs]
    write_index(items)
    print(f"[OK] RTS Agent Analyze wrote: {to_rel(OUTPUT)} (runs={len(items)})")


if __name__ == "__main__":
    main()

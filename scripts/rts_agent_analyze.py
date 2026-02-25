#!/usr/bin/env python3
# RTS Agent Analyze v0
# Execution Path Observer
#
# RTS does not judge.
# RTS reveals structure.

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = ROOT / "runs"
OUTPUT = ROOT / "analysis" / "agent_index.md"

# Matches: "SPAN 000", "SPAN 010", "SPAN 1000" etc.
SPAN_RE = re.compile(r"\bSPAN\s+(\d+)\b", re.IGNORECASE)
STATUS_RE = re.compile(r"\bstatus:\s*(ok|warn|fail|drift)\b", re.IGNORECASE)
NODE_RE = re.compile(r"\bnode_type:\s*([a-zA-Z0-9_]+)\b", re.IGNORECASE)


def collect_runs():
    runs = []
    if RUNS_DIR.exists():
        for p in RUNS_DIR.glob("RUN_*.md"):
            runs.append(p)
    return sorted(runs)


def parse_run(path: Path):
    text = path.read_text(encoding="utf-8", errors="replace")

    spans = []
    # Split by "SPAN " blocks (works with your current template)
    blocks = text.split("SPAN ")

    for b in blocks[1:]:
        # Robust span id parse (fixes the old b[:3] bug)
        m = SPAN_RE.search("SPAN " + b)
        sid = m.group(1).zfill(3) if m else "???"

        node = NODE_RE.search(b)
        status = STATUS_RE.search(b)

        spans.append(
            {
                "span": sid,
                "node": (node.group(1).lower() if node else "unknown"),
                "status": (status.group(1).lower() if status else "unknown"),
            }
        )

    return spans


def classify(spans):
    fails = [s for s in spans if s["status"] == "fail"]
    drifts = [s for s in spans if s["status"] == "drift"]

    if fails:
        return "FAIL"
    if drifts:
        return "DRIFT"
    return "OK"


def write_index(rows):
    lines = []
    lines.append("# RTS Agent Analyze Index")
    lines.append("")
    lines.append("RTS observes agent execution paths (runs/spans).")
    lines.append("Structure only. No semantic judging.")
    lines.append("")
    lines.append("| Run | Status | Spans |")
    lines.append("|---|---:|---:|")

    for r in rows:
        href = f"../{r['file']}"
        lines.append(f"| [{r['name']}]({href}) | {r['status']} | {r['count']} |")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    rows = []

    for run in collect_runs():
        spans = parse_run(run)
        status = classify(spans)

        rows.append(
            {
                "name": run.name,
                "file": str(run.relative_to(ROOT)).replace("\\", "/"),
                "status": status,
                "count": len(spans),
            }
        )

    write_index(rows)
    print("[OK] RTS Agent analysis completed ->", OUTPUT)


if __name__ == "__main__":
    main()

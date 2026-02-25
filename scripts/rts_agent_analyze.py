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


SPAN_RE = re.compile(r"SPAN\s+(\d+)")
STATUS_RE = re.compile(r"status:\s*(\w+)")
NODE_RE = re.compile(r"node_type:\s*(\w+)")


def collect_runs():

    runs = []

    for p in RUNS_DIR.glob("RUN_*.md"):
        runs.append(p)

    return sorted(runs)


def parse_run(path):

    text = path.read_text(encoding="utf-8")

    spans = []

    blocks = text.split("SPAN ")

    for b in blocks[1:]:

        sid = b[:3]

        node = NODE_RE.search(b)
        status = STATUS_RE.search(b)

        spans.append(
            {
                "span": sid,
                "node": node.group(1) if node else "unknown",
                "status": status.group(1) if status else "unknown",
            }
        )

    return spans


def classify(spans):

    fails = [s for s in spans if s["status"] == "fail"]
    drift = [s for s in spans if s["status"] == "drift"]

    if fails:
        return "FAIL"

    if drift:
        return "DRIFT"

    return "OK"


def write_index(rows):

    lines = []

    lines.append("# RTS Agent Analyze Index")
    lines.append("")

    lines.append("| Run | Status | Spans |")
    lines.append("|---|---|---|")

    for r in rows:

        href = f"../{r['file']}"

        lines.append(
            f"| [{r['name']}]({href}) | {r['status']} | {r['count']} |"
        )

    OUTPUT.parent.mkdir(exist_ok=True)

    OUTPUT.write_text("\n".join(lines), encoding="utf-8")



def main():

    rows = []

    for run in collect_runs():

        spans = parse_run(run)

        status = classify(spans)

        rows.append(
            {
                "name": run.name,
                "file": run.relative_to(ROOT),
                "status": status,
                "count": len(spans),
            }
        )

    write_index(rows)

    print("[OK] RTS Agent analysis complete.")


if __name__ == "__main__":
    main()

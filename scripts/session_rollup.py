#!/usr/bin/env python3
import json
import os
import sys
from glob import glob
from typing import Any, Dict, List, Tuple

TAIL_N = 8

def load_jsonl(path: str) -> List[Dict[str, Any]]:
    out = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            out.append(json.loads(line))
    return out

def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def main() -> None:
    if len(sys.argv) < 2:
        print("usage: session_rollup.py YYYY-MM", file=sys.stderr)
        sys.exit(2)

    month = sys.argv[1]
    month_dir = os.path.join("sessions", month)
    os.makedirs(month_dir, exist_ok=True)

    ledgers = sorted(glob(os.path.join(month_dir, "session_*.jsonl")))
    events: List[Dict[str, Any]] = []
    for p in ledgers:
        events.extend(load_jsonl(p))

    events.sort(key=lambda e: e.get("ts", ""))

    # counts by kind
    counts: Dict[str, int] = {}
    for e in events:
        k = e.get("kind", "unknown")
        counts[k] = counts.get(k, 0) + 1

    updated_at = events[-1]["ts"] if events else None
    tail = events[-TAIL_N:] if events else []

    # transitions: take latest 3 transition files (if exist)
    transitions_files = sorted(glob(os.path.join(month_dir, "transition_*.json")))
    transitions: List[Tuple[str, Dict[str, Any]]] = []
    for p in transitions_files[-3:]:
        transitions.append((os.path.basename(p), load_json(p)))

    # write index.json
    index_json = {
        "schema": "RTS-SESSIONS-INDEX-V1",
        "month": month,
        "updated_at_utc": updated_at,
        "counts": counts,
        "latest": tail,
        "transitions_latest": [t[1] for t in transitions],
        "raw_ledgers": [os.path.basename(p) for p in ledgers],
    }

    with open(os.path.join(month_dir, "index.json"), "w", encoding="utf-8") as f:
        json.dump(index_json, f, ensure_ascii=False, indent=2)

    # write index.md (one-page view)
    md = []
    md.append(f"# RTS Sessions — {month}\n")
    if updated_at:
        md.append(f"- updated_at_utc: `{updated_at}`\n")

    md.append("\n## Counts\n")
    for k, v in sorted(counts.items(), key=lambda x: (-x[1], x[0])):
        md.append(f"- `{k}`: {v}\n")

    md.append("\n## Latest (tail)\n")
    for e in tail:
        ts = e.get("ts", "")
        kind = e.get("kind", "")
        wf = e.get("workflow", "")
        rid = e.get("run_id", "")
        st = e.get("status", "")
        commit = e.get("commit", "")
        note = e.get("note", "")
        md.append(f"- `{ts}` `{kind}` workflow={wf} run={rid} status={st} commit={commit} — {note}\n")

    md.append("\n## Transitions (latest)\n")
    if not transitions:
        md.append("- (none)\n")
    else:
        for fname, t in transitions[::-1]:
            sig = t.get("signals", {})
            stats = t.get("stats", {})
            md.append(f"- `{fname}` risk={stats.get('risk_score')} "
                      f"cluster={sig.get('failure_cluster')} "
                      f"recovery={sig.get('recovery_zone')} "
                      f"volatility={sig.get('volatility_spike')} "
                      f"fail_last_n={stats.get('fail_count_last_n')} "
                      f"flips_last_n={stats.get('flip_count_last_n')}\n")

    md.append("\n## Raw ledgers\n")
    for p in ledgers:
        md.append(f"- `{os.path.basename(p)}`\n")

    with open(os.path.join(month_dir, "index.md"), "w", encoding="utf-8") as f:
        f.write("".join(md))

    print(f"rolled up: {month_dir}")

if __name__ == "__main__":
    main()

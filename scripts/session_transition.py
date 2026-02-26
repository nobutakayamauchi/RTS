#!/usr/bin/env python3
import json
import os
import sys
from glob import glob
from typing import Any, Dict, List

WINDOW_N = 12
FAIL_THRESHOLD = 3
FLIP_THRESHOLD = 4

def load_jsonl(path: str) -> List[Dict[str, Any]]:
    out = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            out.append(json.loads(line))
    return out

def flip_count(statuses: List[str]) -> int:
    c = 0
    for i in range(1, len(statuses)):
        if statuses[i] != statuses[i-1]:
            c += 1
    return c

def main() -> None:
    if len(sys.argv) < 3:
        print("usage: session_transition.py YYYY-MM YYYYMMDD", file=sys.stderr)
        sys.exit(2)

    month = sys.argv[1]
    day = sys.argv[2]
    month_dir = os.path.join("sessions", month)

    ledger = os.path.join(month_dir, f"session_{day}.jsonl")
    if not os.path.exists(ledger):
        print(f"missing ledger: {ledger}", file=sys.stderr)
        sys.exit(0)

    # collect recent sentinel.run events across the month (simple + effective)
    ledgers = sorted(glob(os.path.join(month_dir, "session_*.jsonl")))
    events: List[Dict[str, Any]] = []
    for p in ledgers:
        events.extend(load_jsonl(p))

    sentinel = [e for e in events if e.get("kind") == "sentinel.run"]
    sentinel.sort(key=lambda e: e.get("ts", ""))

    window = sentinel[-WINDOW_N:] if len(sentinel) >= 1 else []
    statuses = [e.get("status", "unknown") for e in window]

    fail_count = sum(1 for s in statuses if s == "failure")
    cluster = fail_count >= FAIL_THRESHOLD

    # recovery: recent successes but still had cluster in window
    tail = statuses[-3:] if len(statuses) >= 3 else statuses
    tail_success = len(tail) == 3 and all(s == "success" for s in tail)
    recovery_zone = tail_success and cluster

    flips = flip_count(statuses)
    volatility_spike = flips >= FLIP_THRESHOLD

    risk = 0.0
    if cluster: risk += 0.6
    if recovery_zone: risk += 0.3
    if volatility_spike: risk += 0.2
    risk = min(1.0, risk)

    last_cluster_ts = None
    if cluster:
        # last failure timestamp in window
        for e in reversed(window):
            if e.get("status") == "failure":
                last_cluster_ts = e.get("ts")
                break

    latest = window[-1] if window else {}

    transition = {
        "schema": "RTS-SESSION-TRANSITION-V1",
        "month": month,
        "day": day,
        "computed_at_utc": latest.get("ts"),
        "window_n": WINDOW_N,
        "fail_threshold": FAIL_THRESHOLD,
        "flip_threshold": FLIP_THRESHOLD,
        "signals": {
            "failure_cluster": cluster,
            "recovery_zone": recovery_zone,
            "volatility_spike": volatility_spike,
        },
        "stats": {
            "fail_count_last_n": fail_count,
            "flip_count_last_n": flips,
            "last_n_statuses": statuses,
            "last_cluster_ts": last_cluster_ts,
            "risk_score": risk,
        },
        "evidence": {
            "latest_run_id": latest.get("run_id"),
            "latest_status": latest.get("status"),
            "latest_workflow": latest.get("workflow"),
        }
    }

    out_path = os.path.join(month_dir, f"transition_{day}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(transition, f, ensure_ascii=False, indent=2)

    print(f"wrote: {out_path}")

if __name__ == "__main__":
    main()

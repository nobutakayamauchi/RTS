#!/usr/bin/env python3
import json
import os
import sys
from datetime import datetime

def parse_ts(ts: str) -> datetime:
    # expecting "YYYY-MM-DDTHH:MM:SSZ"
    return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")

def main() -> None:
    if len(sys.argv) < 2:
        print("usage: session_append.py PAYLOAD_JSON_PATH [LEDGER_JSONL_PATH]", file=sys.stderr)
        sys.exit(2)

    payload_path = sys.argv[1]
    with open(payload_path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    ts = payload.get("ts")
    if not ts:
        print("payload missing ts", file=sys.stderr)
        sys.exit(2)

    dt = parse_ts(ts)
    month = dt.strftime("%Y-%m")
    day = dt.strftime("%Y%m%d")

    default_ledger = os.path.join("sessions", month, f"session_{day}.jsonl")
    ledger_path = sys.argv[2] if len(sys.argv) >= 3 else default_ledger

    os.makedirs(os.path.dirname(ledger_path), exist_ok=True)

    line = json.dumps(payload, ensure_ascii=False)
    with open(ledger_path, "a", encoding="utf-8") as f:
        f.write(line + "\n")

    print(f"appended: {ledger_path}")

if __name__ == "__main__":
    main()

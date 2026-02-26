#!/usr/bin/env python3
import json
import os
import sys
from datetime import datetime, timezone

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def main() -> None:
    if len(sys.argv) < 2:
        print("usage: session_payload.py OUTPUT_JSON_PATH", file=sys.stderr)
        sys.exit(2)

    out_path = sys.argv[1]

    payload = {
        "schema": "RTS-SESSION-EVENT-V1",
        "ts": utc_now_iso(),
        "kind": os.getenv("RTS_KIND", "sentinel.run"),
        "workflow": os.getenv("RTS_WORKFLOW", ""),
        "run_id": str(os.getenv("RTS_RUN_ID", "")),
        "run_attempt": str(os.getenv("RTS_RUN_ATTEMPT", "")),
        "status": os.getenv("RTS_STATUS", "unknown"),
        "commit": os.getenv("RTS_COMMIT", ""),
        "actor": os.getenv("RTS_ACTOR", ""),
        "repo": os.getenv("RTS_REPO", ""),
        "ref": os.getenv("RTS_REF", ""),
        "note": os.getenv("RTS_NOTE", ""),
    }

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()

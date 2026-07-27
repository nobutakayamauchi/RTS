from __future__ import annotations

import argparse
import json

from .report_reader_usability import verify_reader_usability_stage


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify the bounded internal reader-usability stage.")
    parser.add_argument("command", choices=["verify", "summary", "progress", "packet-v2", "review-v2"])
    args = parser.parse_args()
    stage = verify_reader_usability_stage()
    if args.command == "verify":
        value = {"verified": True, "state": stage["result"]["state"], "next_gate": stage["result"]["next_gate"]}
    elif args.command == "summary":
        value = stage["summary"]
    elif args.command == "progress":
        value = stage["progress"]
    elif args.command == "packet-v2":
        value = stage["packet_v2"]
    else:
        value = stage["review_v2"]
    print(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import json

from .report_customer_pilot_candidate_shortlist import verify_candidate_shortlist_stage


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("verify", "summary"))
    args = parser.parse_args()
    result = verify_candidate_shortlist_stage()
    if args.command == "summary":
        print(json.dumps(result["summary"], ensure_ascii=False, sort_keys=True))
    else:
        print(json.dumps({"ok": True, **result["summary"]}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

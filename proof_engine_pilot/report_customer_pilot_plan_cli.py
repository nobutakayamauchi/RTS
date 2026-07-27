from __future__ import annotations

import argparse
import json

from .report_customer_pilot_plan import verify_customer_pilot_plan_stage


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify the bounded customer-pilot planning stage.")
    parser.add_argument("command", choices=("verify", "summary"))
    args = parser.parse_args()

    result = verify_customer_pilot_plan_stage()
    if args.command == "verify":
        print(json.dumps({"status": "ok", "state": result["summary"]["state"]}, ensure_ascii=False, sort_keys=True))
    else:
        print(json.dumps(result["summary"], ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

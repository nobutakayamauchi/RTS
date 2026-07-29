from __future__ import annotations

import argparse
import json

from .report_customer_pilot_outreach_send_record import verify_all


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["verify", "summary"])
    args = parser.parse_args()
    result = verify_all()
    if args.command == "verify":
        print("outreach-send-record-ok")
    else:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import json

from .report_customer_pilot_named_candidate_contact_packet import summary, verify_all


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify the named-candidate contact packet.")
    parser.add_argument("command", choices=["verify", "summary"])
    args = parser.parse_args()

    if args.command == "verify":
        values = verify_all()
        print(json.dumps({
            "result": "PASS",
            "state": values["progress"]["current_position"]["current_state"],
            "next_gate": values["progress"]["current_position"]["next_gate"],
        }, ensure_ascii=False, sort_keys=True))
        return 0

    print(json.dumps(summary(), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

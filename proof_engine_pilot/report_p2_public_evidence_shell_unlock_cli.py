from __future__ import annotations

import argparse
import json

from .report_p2_public_evidence_shell_unlock import verify_all


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify the P2 public-evidence-shell unlock and planning stage.")
    parser.add_argument("command", choices=["verify", "summary"])
    args = parser.parse_args()
    result = verify_all()
    if args.command == "verify":
        print("P2 public evidence shell unlock and planning: PASS")
    else:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()

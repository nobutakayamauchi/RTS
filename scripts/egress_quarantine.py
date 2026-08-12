#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import quarantine_core

GATE_VERSION = "ultimate-loop-egress-quarantine-v1"


def inspect_file(path: Path, producer_id: str, target_id: str) -> dict[str, object]:
    record = quarantine_core.inspect_file(
        path,
        phase="pre-promotion-egress",
        identity={
            "producer_id": producer_id,
            "target_id": target_id,
        },
    )
    record["gate_version"] = GATE_VERSION
    return record


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "ULTIMATE LOOP egress quarantine. Bind producer and target identities, "
            "hash exact output bytes, and statically inspect before promotion."
        )
    )
    parser.add_argument(
        "--producer-id",
        required=True,
        help="Identity of the producing run/model/tool/commit or other governed producer.",
    )
    parser.add_argument(
        "--target-id",
        required=True,
        help="Promotion target identity (branch/environment/package/release surface).",
    )
    parser.add_argument("paths", nargs="+", help="Files proposed for promotion/egress.")
    args = parser.parse_args()

    records = [
        inspect_file(Path(raw), args.producer_id, args.target_id)
        for raw in args.paths
    ]

    for record in records:
        print(json.dumps(record, ensure_ascii=False, sort_keys=True))

    return 0 if all(record["verdict"] == "CLEAN" for record in records) else 1


if __name__ == "__main__":
    raise SystemExit(main())

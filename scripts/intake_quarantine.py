#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import quarantine_core

GATE_VERSION = "witness-intake-quarantine-v1"


def inspect_file(path: Path, source_id: str) -> dict[str, object]:
    record = quarantine_core.inspect_file(
        path,
        phase="pre-witness-intake",
        identity={"source_id": source_id},
    )
    record["gate_version"] = GATE_VERSION
    return record


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Pre-WITNESS intake quarantine. Bind source identity, hash exact bytes, "
            "and statically inspect input without executing or normalizing it."
        )
    )
    parser.add_argument(
        "--source-id",
        required=True,
        help="Immutable or externally meaningful source identity (commit/ref/object id).",
    )
    parser.add_argument("paths", nargs="+", help="Files proposed for WITNESS ingestion.")
    args = parser.parse_args()

    records = [inspect_file(Path(raw), args.source_id) for raw in args.paths]

    for record in records:
        print(json.dumps(record, ensure_ascii=False, sort_keys=True))

    return 0 if all(record["verdict"] == "CLEAN" for record in records) else 1


if __name__ == "__main__":
    raise SystemExit(main())

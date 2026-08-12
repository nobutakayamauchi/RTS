#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import check_invisible_unicode as unicode_guard

GATE_VERSION = "witness-intake-quarantine-v0"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_file(path: Path, source_id: str) -> dict[str, object]:
    record: dict[str, object] = {
        "gate_version": GATE_VERSION,
        "scanner_version": unicode_guard.SCANNER_VERSION,
        "source_id": source_id,
        "path": str(path),
        "sha256": None,
        "verdict": "BLOCK",
        "findings": [],
    }

    if not path.exists():
        record["findings"] = ["missing input"]
        return record

    if path.is_symlink():
        record["findings"] = ["symlink input is not admitted"]
        return record

    if not path.is_file():
        record["findings"] = ["input is not a regular file"]
        return record

    record["sha256"] = sha256_file(path)

    if not unicode_guard.should_check(path):
        record["findings"] = [
            "unsupported/unscanned file type; fail closed before WITNESS ingestion"
        ]
        return record

    findings = unicode_guard.scan_file(path)
    record["findings"] = [finding.render() for finding in findings]
    record["verdict"] = "CLEAN" if not findings else "BLOCK"
    return record


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Pre-WITNESS intake quarantine. Hash and statically inspect input "
            "without executing or normalizing it."
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

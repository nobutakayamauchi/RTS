#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json

import check_invisible_unicode as unicode_guard
import egress_quarantine

GATE_VERSION = "repository-egress-gate-v1"


def manifest_digest(records: list[dict[str, object]]) -> str:
    digest = hashlib.sha256()
    for record in sorted(records, key=lambda item: str(item["path"])):
        line = f"{record['path']}\0{record['sha256']}\n".encode("utf-8")
        digest.update(line)
    return digest.hexdigest()


def inspect_repository(producer_id: str, target_id: str) -> tuple[dict[str, object], list[dict[str, object]]]:
    files = unicode_guard.iter_files([])
    records = [
        egress_quarantine.inspect_file(path, producer_id, target_id)
        for path in files
    ]
    blocked = [record for record in records if record["verdict"] != "CLEAN"]
    clean = [record for record in records if record["verdict"] == "CLEAN"]

    summary: dict[str, object] = {
        "gate_version": GATE_VERSION,
        "producer_id": producer_id,
        "target_id": target_id,
        "checked_files": len(records),
        "clean_files": len(clean),
        "blocked_files": len(blocked),
        "manifest_sha256": manifest_digest(clean),
        "verdict": "CLEAN" if not blocked else "BLOCK",
    }
    return summary, blocked


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Exercise the egress quarantine against the current repository promotion surface."
    )
    parser.add_argument("--producer-id", required=True)
    parser.add_argument("--target-id", required=True)
    args = parser.parse_args()

    summary, blocked = inspect_repository(args.producer_id, args.target_id)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    for record in blocked:
        print(json.dumps(record, ensure_ascii=False, sort_keys=True))

    return 0 if summary["verdict"] == "CLEAN" else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Mapping

import check_invisible_unicode as unicode_guard

CORE_VERSION = "witness-quarantine-core-v1"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_file(
    path: Path,
    *,
    phase: str,
    identity: Mapping[str, str],
) -> dict[str, object]:
    record: dict[str, object] = {
        "core_version": CORE_VERSION,
        "scanner_version": unicode_guard.SCANNER_VERSION,
        "phase": phase,
        **dict(identity),
        "path": str(path),
        "sha256": None,
        "verdict": "BLOCK",
        "findings": [],
    }

    if not phase:
        record["findings"] = ["missing quarantine phase identity"]
        return record

    if not identity or any(not key or not value for key, value in identity.items()):
        record["findings"] = ["missing boundary identity"]
        return record

    if not path.exists():
        record["findings"] = ["missing file"]
        return record

    if path.is_symlink():
        record["findings"] = ["symlink file is not admitted"]
        return record

    if not path.is_file():
        record["findings"] = ["path is not a regular file"]
        return record

    record["sha256"] = sha256_file(path)

    if not unicode_guard.should_check(path):
        record["findings"] = [
            f"unsupported/unscanned file type; fail closed at {phase} boundary"
        ]
        return record

    findings = unicode_guard.scan_file(path)
    record["findings"] = [finding.render() for finding in findings]
    record["verdict"] = "CLEAN" if not findings else "BLOCK"
    return record

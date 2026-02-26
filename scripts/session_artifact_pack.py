#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
RTS Session Artifact Pack (FULL REPLACE)

Purpose:
- Freeze raw session ledgers (JSONL) into a forensic zip artifact
- Do NOT modify sessions/<YYYY-MM>/checksums.sha256 (that is rollup/append territory)
- Produce unique artifact names to avoid overwriting history
- Embed a manifest.json inside the zip for provenance + integrity

Output:
  sessions/<YYYY-MM>/raw_session_<YYYYMMDD>_<HHMMSSZ>.zip

Zip contents:
  <YYYY-MM>/session_*.jsonl
  <YYYY-MM>/manifest.json

Usage:
  python scripts/session_artifact_pack.py YYYY-MM
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import zipfile
from datetime import datetime, timezone
from glob import glob
from typing import Dict, List, Tuple


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def utc_now_iso() -> str:
    return utc_now().isoformat().replace("+00:00", "Z")


def sha256_bytes(data: bytes) -> str:
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def list_raw_ledgers(month_dir: str) -> List[str]:
    return sorted(glob(os.path.join(month_dir, "session_*.jsonl")))


def make_artifact_name(ts: datetime) -> Tuple[str, str]:
    # returns (day_tag, time_tag)
    day = ts.strftime("%Y%m%d")
    hhmmss = ts.strftime("%H%M%SZ")
    return day, hhmmss


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python scripts/session_artifact_pack.py YYYY-MM", file=sys.stderr)
        return 2

    month = sys.argv[1].strip()
    month_dir = os.path.join("sessions", month)
    if not os.path.isdir(month_dir):
        print(f"no month dir: {month_dir}")
        return 0

    raw_files = list_raw_ledgers(month_dir)
    if not raw_files:
        print("no raw files")
        return 0

    ts = utc_now()
    day_tag, time_tag = make_artifact_name(ts)

    zip_path = os.path.join(month_dir, f"raw_session_{day_tag}_{time_tag}.zip")

    # Build manifest (computed BEFORE zipping, includes file hashes)
    entries: List[Dict[str, str]] = []
    for fpath in raw_files:
        entries.append(
            {
                "file": os.path.basename(fpath),
                "sha256": sha256_file(fpath),
            }
        )

    manifest = {
        "kind": "rts.raw_artifact",
        "version": "2026-02",
        "month": month,
        "generated_at_utc": utc_now_iso(),
        "file_count": len(entries),
        "files": entries,
    }
    manifest_bytes = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    manifest_sha = sha256_bytes(manifest_bytes)
    manifest["manifest_sha256"] = manifest_sha
    manifest_bytes = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")

    # Write zip (unique name; do not overwrite)
    if os.path.exists(zip_path):
        # extremely unlikely unless same-second rerun
        zip_path = os.path.join(month_dir, f"raw_session_{day_tag}_{time_tag}_dup.zip")

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        # add ledgers
        for fpath in raw_files:
            arc = os.path.join(month, os.path.basename(fpath))
            z.write(fpath, arcname=arc)
        # add manifest inside zip
        z.writestr(os.path.join(month, "manifest.json"), manifest_bytes)

    zip_sha = sha256_file(zip_path)

    print("packed:", zip_path)
    print("zip_sha256:", zip_sha)
    print("manifest_sha256:", manifest_sha)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
# RTS Snapshot Linker (Level2)

import json
from pathlib import Path
import hashlib

INCIDENTS = Path("incidents")
SNAPS = INCIDENTS / "evidence_snapshots"


def sha256_file(path: Path):

    h = hashlib.sha256()

    with open(path,"rb") as f:
        while True:
            b = f.read(8192)
            if not b:
                break
            h.update(b)

    return h.hexdigest()


def update_incident(md_path, snap_path):

    snap_hash = sha256_file(snap_path)

    text = md_path.read_text()

    if "snapshot_ref:" not in text:
        return

    text = text.replace(
        "snapshot_ref: null",
        f"snapshot_ref: {snap_path.name}"
    )

    text = text.replace(
        "snapshot_hash_sha256: null",
        f"snapshot_hash_sha256: {snap_hash}"
    )

    text = text.replace(
        "retrieved_at: null",
        "retrieved_at: auto"
    )

    md_path.write_text(text)


def main():

    if not SNAPS.exists():
        return

    snaps = list(SNAPS.glob("SNAP_*.json"))

    if not snaps:
        return

    latest = max(snaps, key=lambda p:p.stat().st_mtime)

    for md in INCIDENTS.glob("INC_*.md"):

        update_incident(md, latest)


if __name__ == "__main__":
    main()

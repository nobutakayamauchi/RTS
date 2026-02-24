#!/usr/bin/env python3

import hashlib
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]

INCIDENTS = ROOT / "incidents"
SNAPSHOT_DIR = INCIDENTS / "evidence_snapshots"


def sha256_file(path: Path) -> str:

    h = hashlib.sha256()

    with open(path, "rb") as f:

        while True:

            chunk = f.read(8192)

            if not chunk:
                break

            h.update(chunk)

    return h.hexdigest()


def update_incident(md_path: Path):

    text = md_path.read_text(encoding="utf-8")

    if "snapshot_ref:" not in text:
        return

    match = re.search(
        r"snapshot_ref:\s*\n\s*(.+)",
        text
    )

    if not match:
        return

    snap_path = match.group(1).strip()

    snap = ROOT / snap_path

    if not snap.exists():
        return

    digest = sha256_file(snap)

    if "snapshot_hash_sha256:" in text:
        return

    insert = f"\nsnapshot_hash_sha256:\n {digest}\n"

    text = text.replace(
        snap_path,
        snap_path + insert
    )

    md_path.write_text(text, encoding="utf-8")

    print(f"[OK] updated {md_path.name}")


def main():

    for md in INCIDENTS.glob("INC_*.md"):

        update_incident(md)


if __name__ == "__main__":
    main()

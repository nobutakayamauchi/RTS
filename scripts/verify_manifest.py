#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations
import hashlib
import os
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def month_key_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")

def main() -> int:
    month = os.environ.get("RTS_MONTH") or month_key_utc()
    manifest = ROOT / "sessions" / month / "manifest.sha256"
    if not manifest.exists():
        print(f"[verify] fail: missing {manifest}")
        return 2

    bad = 0
    for i, line in enumerate(manifest.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        # expected: "<hash><2 spaces><path>"
        try:
            want_hash, rel_path = line.split(None, 1)
            rel_path = rel_path.strip()
        except ValueError:
            print(f"[verify] bad line {i}: {line}")
            bad += 1
            continue

        p = ROOT / rel_path
        if not p.exists():
            print(f"[verify] missing file line {i}: {rel_path}")
            bad += 1
            continue

        got = sha256_file(p)
        if got != want_hash:
            print(f"[verify] mismatch line {i}: {rel_path}\n  want={want_hash}\n  got ={got}")
            bad += 1

    if bad:
        print(f"[verify] FAIL: {bad} problem(s)")
        return 1

    print("[verify] OK")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

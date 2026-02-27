#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Verify sessions/YYYY-MM/manifest.sha256

Assumptions:
- manifest lines are: "<sha256>  <repo-relative-path>"
  (sha256sum compatible; two spaces recommended but any whitespace OK)

Behavior:
- Missing manifest -> FAIL
- Empty manifest -> OK (explicitly allows "no tracked files this month")
- For each line: check file exists, hash matches
- Exclude manifest itself if it appears in entries (defensive)
"""

from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path
from datetime import datetime, timezone


ROOT = Path(__file__).resolve().parents[1]
HEX64_RE = re.compile(r"^[0-9a-fA-F]{64}$")


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def month_key_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def parse_line(line: str) -> tuple[str, str] | None:
    """
    Parse a manifest line.
    Expected: "<hash><whitespace><path>"
    Returns (hash, path) or None for empty/comment lines.
    """
    s = line.strip()
    if not s:
        return None
    if s.startswith("#"):
        return None

    # sha256sum typically uses: "<hash>  <path>"
    # We accept any whitespace separation, but require both parts.
    parts = s.split(None, 1)
    if len(parts) != 2:
        raise ValueError(f"bad format (need '<hash> <path>'): {line.rstrip()}")
    want_hash, rel_path = parts[0].strip(), parts[1].strip()
    return want_hash, rel_path


def main() -> int:
    month = (os.environ.get("RTS_MONTH") or "").strip() or month_key_utc()
    manifest = ROOT / "sessions" / month / "manifest.sha256"

    if not manifest.exists():
        print(f"[verify] FAIL: missing manifest: {manifest}")
        return 2
    if not manifest.is_file():
        print(f"[verify] FAIL: manifest is not a file: {manifest}")
        return 2

    lines = manifest.read_text(encoding="utf-8").splitlines()
    if not lines:
        print("[verify] OK: manifest is empty (0 entries)")
        return 0

    problems = 0
    checked = 0

    for i, raw in enumerate(lines, start=1):
        try:
            parsed = parse_line(raw)
            if parsed is None:
                continue
            want_hash, rel_path = parsed

            if not HEX64_RE.match(want_hash):
                print(f"[verify] FAIL line {i}: invalid sha256 '{want_hash}'")
                problems += 1
                continue

            # Resolve path relative to repo root (must match generator)
            p = (ROOT / rel_path).resolve()

            # Defensive: if someone accidentally included the manifest itself, ignore it
            if p == manifest.resolve():
                # This should not happen if generator excludes it; ignore to avoid paradox.
                continue

            if not p.exists():
                print(f"[verify] FAIL line {i}: missing file: {rel_path}")
                problems += 1
                continue
            if not p.is_file():
                print(f"[verify] FAIL line {i}: not a file: {rel_path}")
                problems += 1
                continue

            got = sha256_file(p)
            checked += 1

            if got.lower() != want_hash.lower():
                print(f"[verify] FAIL line {i}: hash mismatch: {rel_path}")
                print(f"  want={want_hash}")
                print(f"  got ={got}")
                problems += 1

        except Exception as e:
            print(f"[verify] FAIL line {i}: {e}")
            problems += 1

    if problems:
        print(f"[verify] FAIL: {problems} problem(s), checked {checked} file(s)")
        return 1

    print(f"[verify] OK: checked {checked} file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Generate sessions/YYYY-MM/manifest.sha256

Design:
- Evidence-first, minimal assumptions
- Cover ALL files in sessions/<month>/ (future-proof, no glob maintenance)
- Exclude manifest.sha256 itself to avoid self-reference
- Stable ordering for deterministic output
- SHA-256, format compatible with sha256sum: "<hash>  <path>"
"""

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
    # Deterministic for Actions; UTC is safest
    return datetime.now(timezone.utc).strftime("%Y-%m")


def main() -> int:
    month = (os.environ.get("RTS_MONTH") or "").strip() or month_key_utc()
    base = ROOT / "sessions" / month

    if not base.exists():
        # Don't create folders implicitly: avoid surprising structure changes.
        print(f"[manifest] skip: {base} not found")
        return 0

    if not base.is_dir():
        print(f"[manifest] fail: {base} is not a directory")
        return 2

    out = base / "manifest.sha256"

    # Target: ALL files directly under sessions/<month>/
    # (not recursive; future-proof but avoids accidentally hashing huge trees)
    files = sorted([p for p in base.glob("*") if p.is_file()])

    # Exclude manifest itself to avoid self-hash / infinite change loop
    files = [p for p in files if p.name != out.name]

    rel_lines: list[str] = []
    for p in files:
        try:
            rel = p.relative_to(ROOT).as_posix()
        except ValueError:
            # Should never happen, but guard for safety
            rel = str(p.resolve())
        rel_lines.append(f"{sha256_file(p)}  {rel}")

    # Write deterministically
    out.write_text("\n".join(rel_lines) + ("\n" if rel_lines else ""), encoding="utf-8")

    print(f"[manifest] wrote: {out} ({len(rel_lines)} entries)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

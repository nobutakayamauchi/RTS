#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Generate sessions/YYYY-MM/manifest.sha256

Targets (minimum, safest):
- session_*.jsonl
- index_snapshot.*
- ESC_*.md   (include ALL ESC; no filter)
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
    # keep it deterministic for Actions; UTC is safest
    return datetime.now(timezone.utc).strftime("%Y-%m")

def main() -> int:
    month = os.environ.get("RTS_MONTH") or month_key_utc()
    base = ROOT / "sessions" / month
    if not base.exists():
        # If month folder doesn't exist, do nothing (avoid creating new structure unexpectedly)
        print(f"[manifest] skip: {base} not found")
        return 0

    patterns = [
        "session_*.jsonl",
        "index_snapshot.*",
        "ESC_*.md",
    ]

    files: list[Path] = []
    for pat in patterns:
        files.extend(sorted(base.glob(pat)))

    # Enforce "minimal assumptions": no files -> still write empty manifest (explicit)
    rel_lines: list[str] = []
    for p in sorted(set(files)):
        if p.is_file():
            rel = p.relative_to(ROOT).as_posix()
            rel_lines.append(f"{sha256_file(p)}  {rel}")

    out = base / "manifest.sha256"
    out.write_text("\n".join(rel_lines) + ("\n" if rel_lines else ""), encoding="utf-8")
    print(f"[manifest] wrote: {out} ({len(rel_lines)} entries)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

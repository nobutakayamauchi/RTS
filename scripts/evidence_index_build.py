#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Evidence Index Builder (Observed naming tolerant)
- Scan incidents/evidence_snapshots for ESC_ and SNAP_ files
- Build month-scoped index files:
    sessions/<YYYY-MM>/evidence_index.json
    sessions/<YYYY-MM>/evidence_index.md
    sessions/<YYYY-MM>/snap_index.json
    sessions/<YYYY-MM>/snap_index.md
- "Latest" is computed by (day, time_guess, filename) sorting.

Usage:
  python scripts/evidence_index_build.py 2026-02
"""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from glob import glob
from typing import Any, Dict, List, Optional, Tuple


BASE_DIR = os.path.join("incidents", "evidence_snapshots")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def month_prefix(month: str) -> str:
    # "2026-02" -> "202602"
    return month.replace("-", "")


def safe_int(s: str, default: int = 0) -> int:
    try:
        return int(s)
    except Exception:
        return default


def guess_time_token(filename: str) -> str:
    """
    Observed patterns:
      ESC_YYYYMMDD_09103...  (5 digits)
      ESC_YYYYMMDD_112814... (6 digits)
      ESC_YYYYMMDD_034800... (6 digits)
      SNAP_YYYYMMDD_1457...  (4 digits)
    We accept 4-6 digits right after day underscore.
    Normalize to HHMMSSZ-like string where possible; otherwise keep raw digits.
    """
    m = re.match(r"^(?:ESC|SNAP)_(\d{8})_(\d{4,6})", filename)
    if not m:
        return "000000Z"

    tok = m.group(2)  # 4..6 digits
    if len(tok) == 4:
        # HHMM -> HHMM00Z
        return f"{tok}00Z"
    if len(tok) == 5:
        # Ambiguous (HMMSS or HHMMS). Keep raw but pad to 6 with leading 0.
        return f"{tok.zfill(6)}Z"
    # 6 digits -> HHMMSSZ
    return f"{tok}Z"


def rel_link_to_repo(path: str) -> str:
    # from sessions/<YYYY-MM>/... to incidents/evidence_snapshots/...
    fn = os.path.basename(path)
    return os.path.join("..", "..", "incidents", "evidence_snapshots", fn)


@dataclass
class Item:
    kind: str          # "ESC" or "SNAP"
    day: str           # YYYYMMDD
    time: str          # HHMMSSZ (guessed)
    file: str
    rel: str


def scan_items(month: str) -> Tuple[List[Item], List[Item]]:
    if not os.path.isdir(BASE_DIR):
        return [], []

    pref = month_prefix(month)

    # month filter: YYYYMMDD where YYYYMM matches
    esc_paths = sorted(glob(os.path.join(BASE_DIR, f"ESC_{pref}[0-9][0-9]_*")))
    snap_paths = sorted(glob(os.path.join(BASE_DIR, f"SNAP_{pref}[0-9][0-9]_*")))

    esc_items: List[Item] = []
    snap_items: List[Item] = []

    rx_day = re.compile(r"^(ESC|SNAP)_(\d{8})_")

    for p in esc_paths:
        fn = os.path.basename(p)
        m = rx_day.match(fn)
        if not m:
            continue
        day = m.group(2)
        esc_items.append(Item(kind="ESC", day=day, time=guess_time_token(fn), file=fn, rel=rel_link_to_repo(p)))

    for p in snap_paths:
        fn = os.path.basename(p)
        m = rx_day.match(fn)
        if not m:
            continue
        day = m.group(2)
        snap_items.append(Item(kind="SNAP", day=day, time=guess_time_token(fn), file=fn, rel=rel_link_to_repo(p)))

    def sort_key(it: Item) -> Tuple[str, str, str]:
        return (it.day, it.time, it.file)

    esc_items.sort(key=sort_key)
    snap_items.sort(key=sort_key)
    return esc_items, snap_items


def write_index(month: str, kind: str, items: List[Item], out_json: str, out_md: str) -> None:
    updated = utc_now_iso()
    latest = items[-1] if items else None

    obj: Dict[str, Any] = {
        "month": month,
        "kind": kind,
        "updated_at_utc": updated,
        "latest": asdict(latest) if latest else None,
        "items": [asdict(x) for x in items[-500:]],  # cap
    }

    os.makedirs(os.path.dirname(out_json), exist_ok=True)

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")

    lines: List[str] = []
    lines.append(f"# {kind} Index — {month}")
    lines.append("")
    lines.append(f"- updated_at_utc: `{updated}`")
    lines.append("")

    if latest:
        lines.append("## Latest")
        lines.append("")
        lines.append(f"- `{latest.day}` `{latest.time}` — [{latest.file}]({latest.rel})")
        lines.append("")
    else:
        lines.append("## Latest")
        lines.append("")
        lines.append("- (none)")
        lines.append("")

    lines.append("## Recent (latest 50)")
    lines.append("")
    for it in items[-50:][::-1]:
        lines.append(f"- `{it.day}` `{it.time}` — [{it.file}]({it.rel})")

    with open(out_md, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python scripts/evidence_index_build.py YYYY-MM", file=sys.stderr)
        return 2

    month = sys.argv[1].strip()
    month_dir = os.path.join("sessions", month)
    os.makedirs(month_dir, exist_ok=True)

    esc_items, snap_items = scan_items(month)

    write_index(
        month=month,
        kind="ESC",
        items=esc_items,
        out_json=os.path.join(month_dir, "evidence_index.json"),
        out_md=os.path.join(month_dir, "evidence_index.md"),
    )

    write_index(
        month=month,
        kind="SNAP",
        items=snap_items,
        out_json=os.path.join(month_dir, "snap_index.json"),
        out_md=os.path.join(month_dir, "snap_index.md"),
    )

    print(f"Wrote: {os.path.join(month_dir, 'evidence_index.json')}")
    print(f"Wrote: {os.path.join(month_dir, 'evidence_index.md')}")
    print(f"Wrote: {os.path.join(month_dir, 'snap_index.json')}")
    print(f"Wrote: {os.path.join(month_dir, 'snap_index.md')}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

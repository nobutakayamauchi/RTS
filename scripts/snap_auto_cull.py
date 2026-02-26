#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SNAP Auto Cull (safe)
- Target: incidents/evidence_snapshots/SNAP_*.md
- Scope: month prefix only (YYYY-MM -> YYYYMM)
- Keep:
    * keep_per_day: newest N per day
    * keep_per_month: newest N per month (after per-day keep is applied)
- Default: dry-run (no deletion). Use --apply to delete.
- Filename formats tolerated:
    SNAP_<YYYYMMDD>_<HHMM...>*.md
    SNAP_<YYYYMMDD>_*.md  (time missing -> treated as 000000)
"""

from __future__ import annotations

import argparse
import os
import re
from glob import glob
from dataclasses import dataclass
from typing import Dict, List, Tuple


BASE_DIR = os.path.join("incidents", "evidence_snapshots")


def month_prefix(month: str) -> str:
    # "2026-02" -> "202602"
    return month.replace("-", "").strip()


@dataclass
class SnapItem:
    path: str
    file: str
    day: str      # YYYYMMDD
    time: str     # HHMMSS (normalized to 6 digits)

    def key(self) -> Tuple[str, str]:
        return (self.day, self.time)


def parse_snap_filename(fn: str) -> SnapItem | None:
    # SNAP_20260224_143600_anything.md
    # SNAP_20260224_1436.md (HHMM) -> normalize to HHMM00
    # SNAP_20260224_anything.md -> time=000000
    rx = re.compile(r"^SNAP_(\d{8})(?:_(\d{4,6}))?.*\.md$")
    m = rx.match(fn)
    if not m:
        return None
    day = m.group(1)
    t = m.group(2) or "000000"
    t = t.strip()
    if len(t) == 4:
        t = t + "00"
    elif len(t) == 5:
        # rare, pad right
        t = t + "0"
    elif len(t) >= 6:
        t = t[:6]
    else:
        t = "000000"
    return SnapItem(path="", file=fn, day=day, time=t)


def collect(month: str) -> List[SnapItem]:
    if not os.path.isdir(BASE_DIR):
        return []
    pref = month_prefix(month)
    # month scope: SNAP_YYYYMM??_*.md
    paths = sorted(glob(os.path.join(BASE_DIR, f"SNAP_{pref}[0-9][0-9]_*.md")))
    items: List[SnapItem] = []
    for p in paths:
        fn = os.path.basename(p)
        it = parse_snap_filename(fn)
        if not it:
            continue
        it.path = p
        items.append(it)
    # sort ascending then we can take newest by reversing
    items.sort(key=lambda x: (x.day, x.time, x.file))
    return items


def plan_cull(items: List[SnapItem], keep_per_day: int, keep_per_month: int) -> Tuple[List[SnapItem], List[SnapItem]]:
    """
    returns: (keep, delete)
    """
    if not items:
        return [], []

    # group by day -> keep newest N per day
    by_day: Dict[str, List[SnapItem]] = {}
    for it in items:
        by_day.setdefault(it.day, []).append(it)

    keep_set: Dict[str, SnapItem] = {}

    for day, arr in by_day.items():
        arr_sorted = sorted(arr, key=lambda x: (x.day, x.time, x.file))
        newest = arr_sorted[::-1][:max(0, keep_per_day)]
        for it in newest:
            keep_set[it.path] = it

    # after per-day keep, enforce per-month keep (newest N overall)
    kept = list(keep_set.values())
    kept_sorted_newest = sorted(kept, key=lambda x: (x.day, x.time, x.file), reverse=True)

    final_keep = kept_sorted_newest[:max(0, keep_per_month)] if keep_per_month > 0 else kept_sorted_newest
    final_keep_set = {it.path for it in final_keep}

    delete = [it for it in items if it.path not in final_keep_set]
    keep = [it for it in items if it.path in final_keep_set]

    # stable output ordering (newest first)
    keep.sort(key=lambda x: (x.day, x.time, x.file), reverse=True)
    delete.sort(key=lambda x: (x.day, x.time, x.file), reverse=True)
    return keep, delete


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("month", help="YYYY-MM (e.g., 2026-02)")
    ap.add_argument("--keep-per-day", type=int, default=3)
    ap.add_argument("--keep-per-month", type=int, default=30)
    ap.add_argument("--apply", action="store_true", help="Actually delete files (default: dry-run)")
    args = ap.parse_args()

    items = collect(args.month)
    keep, delete = plan_cull(items, args.keep_per_day, args.keep_per_month)

    print(f"[SNAP] month={args.month} base={BASE_DIR}")
    print(f"[SNAP] found={len(items)} keep={len(keep)} delete={len(delete)} apply={args.apply}")

    if keep:
        print("[SNAP] keep (newest first):")
        for it in keep[:30]:
            print(f"  KEEP {it.file}")
        if len(keep) > 30:
            print(f"  ... ({len(keep)} total)")

    if delete:
        print("[SNAP] delete (newest first):")
        for it in delete[:30]:
            print(f"  DEL  {it.file}")
        if len(delete) > 30:
            print(f"  ... ({len(delete)} total)")

    if not args.apply:
        print("[SNAP] dry-run only. Use --apply to delete.")
        return 0

    # apply deletions
    deleted = 0
    for it in delete:
        try:
            os.remove(it.path)
            deleted += 1
        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"[SNAP] WARN failed to delete {it.file}: {e}")

    print(f"[SNAP] deleted={deleted}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

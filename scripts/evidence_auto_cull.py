#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Evidence Auto Cull (safe)
- Target: incidents/evidence_snapshots/*.md
- Keep policy (ESC only by default):
    * keep_per_day: keep latest K per day
    * keep_per_month: keep latest M per month
    * pin_if_contains: if file content contains any keywords, always keep
- Action:
    * default: move culled files to incidents/evidence_archive/<YYYY-MM>/ and zip them
    * optional: delete (NOT recommended) -> --delete
- Always supports --dry-run

Usage:
  python scripts/evidence_auto_cull.py 2026-02 --dry-run
  python scripts/evidence_auto_cull.py 2026-02 --keep-per-day 3 --keep-per-month 30
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from glob import glob
from typing import Dict, List, Optional, Tuple


RX_ESC = re.compile(r"^ESC_(\d{8})_([0-9A-Za-z]+)_(\d{6}Z)\.md$")
# If you also want to manage INC/SNAP, extend here:
RX_ANY = re.compile(r"^(ESC|INC|SNAP)_(\d{8})_.*\.md$")


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def month_prefix(month: str) -> str:
    # "2026-02" -> "202602"
    return month.replace("-", "")


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def read_text(path: str, limit_bytes: int = 64 * 1024) -> str:
    # read first 64KB for keyword detection (fast & safe)
    with open(path, "rb") as f:
        b = f.read(limit_bytes)
    try:
        return b.decode("utf-8", errors="replace")
    except Exception:
        return ""


@dataclass
class Item:
    path: str
    file: str
    day: str      # YYYYMMDD
    rule: str
    time: str     # HHMMSSZ
    dt: datetime  # parsed UTC


def parse_esc_file(fn: str) -> Optional[Tuple[str, str, str]]:
    m = RX_ESC.match(fn)
    if not m:
        return None
    day, rule, time = m.group(1), m.group(2), m.group(3)
    return day, rule, time


def parse_dt(day: str, hhmmssz: str) -> datetime:
    # day=YYYYMMDD, time=HHMMSSZ
    hhmmss = hhmmssz.replace("Z", "")
    s = f"{day}{hhmmss}"
    return datetime.strptime(s, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)


def collect_esc_for_month(month: str) -> List[Item]:
    base = os.path.join("incidents", "evidence_snapshots")
    if not os.path.isdir(base):
        return []
    pref = month_prefix(month)
    paths = sorted(glob(os.path.join(base, f"ESC_{pref}[0-9][0-9]_*_*.md")))
    out: List[Item] = []
    for p in paths:
        fn = os.path.basename(p)
        parsed = parse_esc_file(fn)
        if not parsed:
            continue
        day, rule, t = parsed
        try:
            dt = parse_dt(day, t)
        except Exception:
            # fallback: use mtime if parse fails
            dt = datetime.fromtimestamp(os.path.getmtime(p), tz=timezone.utc)
        out.append(Item(path=p, file=fn, day=day, rule=rule, time=t, dt=dt))
    out.sort(key=lambda x: x.dt)
    return out


def choose_keep_set(
    items: List[Item],
    keep_per_day: int,
    keep_per_month: int,
    pin_if_contains: List[str],
) -> Tuple[List[Item], List[Item]]:
    """
    returns: (keep, cull)
    Policy:
      1) Pin (keyword match) => keep
      2) Keep latest keep_per_day per each day
      3) Keep latest keep_per_month overall
      4) Others => cull
    """
    pinned: Dict[str, Item] = {}
    if pin_if_contains:
        for it in items:
            txt = read_text(it.path)
            if any(k in txt for k in pin_if_contains):
                pinned[it.path] = it

    # per-day keep (latest K)
    by_day: Dict[str, List[Item]] = {}
    for it in items:
        by_day.setdefault(it.day, []).append(it)
    keep_day: Dict[str, Item] = {}
    for day, arr in by_day.items():
        arr_sorted = sorted(arr, key=lambda x: x.dt)
        for it in arr_sorted[-keep_per_day:]:
            keep_day[it.path] = it

    # per-month keep (latest M)
    keep_month: Dict[str, Item] = {}
    for it in sorted(items, key=lambda x: x.dt)[-keep_per_month:]:
        keep_month[it.path] = it

    keep_map: Dict[str, Item] = {}
    keep_map.update(pinned)
    keep_map.update(keep_day)
    keep_map.update(keep_month)

    keep = [keep_map[p] for p in sorted(keep_map.keys())]
    keep_set = set(keep_map.keys())
    cull = [it for it in items if it.path not in keep_set]
    return keep, cull


def zip_dir(src_dir: str, zip_path: str) -> None:
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(src_dir):
            for fn in files:
                full = os.path.join(root, fn)
                rel = os.path.relpath(full, os.path.dirname(src_dir))
                z.write(full, arcname=rel)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("month", help="YYYY-MM")
    ap.add_argument("--keep-per-day", type=int, default=3)
    ap.add_argument("--keep-per-month", type=int, default=30)
    ap.add_argument("--pin", action="append", default=[
        # safe defaults: keep anything that smells important
        "evidence_level: L2",
        "conclusion: failure",
        "breakpoint: `True`",
        "dangling_run_detected",
    ])
    ap.add_argument("--dry-run", action="store_true", help="print plan only")
    ap.add_argument("--delete", action="store_true", help="delete instead of archive (danger)")
    args = ap.parse_args()

    month = args.month.strip()

    items = collect_esc_for_month(month)
    print(f"[evidence] month={month} esc_items={len(items)}")

    keep, cull = choose_keep_set(
        items=items,
        keep_per_day=max(0, args.keep_per_day),
        keep_per_month=max(0, args.keep_per_month),
        pin_if_contains=[x for x in (args.pin or []) if x],
    )

    print(f"[plan] keep={len(keep)} cull={len(cull)}")
    if keep:
        print("[keep] latest:", keep[-1].file)
    if cull:
        print("[cull] oldest:", cull[0].file)

    if args.dry_run:
        for it in cull[:30]:
            print("DRY-CULL:", it.file)
        if len(cull) > 30:
            print(f"... ({len(cull)} total)")
        return 0

    if not cull:
        print("nothing to cull")
        return 0

    if args.delete:
        # Dangerous: delete from repo
        for it in cull:
            os.remove(it.path)
        print(f"deleted {len(cull)} files")
        return 0

    # Archive move
    arch_root = os.path.join("incidents", "evidence_archive", month)
    ensure_dir(arch_root)
    moved_dir = os.path.join(arch_root, f"moved_{utc_now().strftime('%Y%m%d_%H%M%SZ')}")
    ensure_dir(moved_dir)

    for it in cull:
        shutil.move(it.path, os.path.join(moved_dir, it.file))

    # zip it
    zip_path = os.path.join(arch_root, f"esc_culled_{utc_now().strftime('%Y%m%d_%H%M%SZ')}.zip")
    zip_dir(moved_dir, zip_path)

    # optional: remove moved_dir after zip to avoid clutter
    # (keep dir if you want transparency)
    shutil.rmtree(moved_dir, ignore_errors=True)

    print(f"archived {len(cull)} files -> {zip_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

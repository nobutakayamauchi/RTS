#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SNAP Index Rebuild (SAFE)
- incidents/evidence_snapshots/ にある SNAP_*.md を収集
- 月フィルタ: SNAP_<YYYYMMDD>_... のYYYYMMDDが指定 month の範囲(YYYYMM**)のみ
- 出力:
  - incidents/evidence_snapshots/SNAP_INDEX_<YYYYMM>.json
  - incidents/evidence_snapshots/SNAP_INDEX_<YYYYMM>.md
  - incidents/evidence_snapshots/SNAP_INDEX_LATEST.json (最新月を上書き)
  - incidents/evidence_snapshots/SNAP_INDEX_LATEST.md   (最新月を上書き)

Usage:
  python scripts/snap_index_rebuild.py 2026-02
"""

from __future__ import annotations

import json
import os
import re
import sys
from glob import glob
from datetime import datetime, timezone
from typing import Any, Dict, List


BASE_DIR = os.path.join("incidents", "evidence_snapshots")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def month_prefix(month: str) -> str:
    # "2026-02" -> "202602"
    return month.replace("-", "")


def collect_snaps(month: str) -> List[Dict[str, Any]]:
    if not os.path.isdir(BASE_DIR):
        return []

    pref = month_prefix(month)  # YYYYMM
    paths = sorted(glob(os.path.join(BASE_DIR, "SNAP_*.md")))

    # SNAP_20260226_0649...md とかを想定
    rx = re.compile(r"^SNAP_(\d{8})_(.+)\.md$")

    out: List[Dict[str, Any]] = []
    for p in paths:
        fn = os.path.basename(p)
        m = rx.match(fn)
        if not m:
            continue
        day = m.group(1)  # YYYYMMDD
        if not day.startswith(pref):
            continue
        suffix = m.group(2)

        out.append(
            {
                "day": day,
                "suffix": suffix,
                "file": fn,
                "path": p,
                "rel": os.path.join("..", "..", "incidents", "evidence_snapshots", fn),
            }
        )

    # sort by day then suffix
    out.sort(key=lambda x: (x["day"], x["suffix"]))
    return out


def render_md(month: str, updated_at_utc: str, items: List[Dict[str, Any]]) -> str:
    lines: List[str] = []
    lines.append(f"# SNAP Index — {month}")
    lines.append("")
    lines.append(f"- updated_at_utc: `{updated_at_utc}`")
    lines.append(f"- total: `{len(items)}`")
    lines.append("")

    if not items:
        lines.append("- (none)")
        lines.append("")
        return "\n".join(lines)

    # day grouping
    cur = None
    for it in items:
        if cur != it["day"]:
            cur = it["day"]
            lines.append(f"## {cur}")
            lines.append("")
        lines.append(f"- [{it['file']}]({it['rel']})")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python scripts/snap_index_rebuild.py YYYY-MM", file=sys.stderr)
        return 2

    month = sys.argv[1].strip()
    os.makedirs(BASE_DIR, exist_ok=True)

    items = collect_snaps(month)
    updated = utc_now_iso()

    pref = month_prefix(month)
    out_json = os.path.join(BASE_DIR, f"SNAP_INDEX_{pref}.json")
    out_md = os.path.join(BASE_DIR, f"SNAP_INDEX_{pref}.md")

    obj = {
        "month": month,
        "updated_at_utc": updated,
        "total": len(items),
        "items": [{"day": x["day"], "suffix": x["suffix"], "file": x["file"], "rel": x["rel"]} for x in items],
    }

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")

    md = render_md(month, updated, items)
    with open(out_md, "w", encoding="utf-8") as f:
        f.write(md + "\n")

    # latest pointers (上書きOK)
    latest_json = os.path.join(BASE_DIR, "SNAP_INDEX_LATEST.json")
    latest_md = os.path.join(BASE_DIR, "SNAP_INDEX_LATEST.md")
    with open(latest_json, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")
    with open(latest_md, "w", encoding="utf-8") as f:
        f.write(md + "\n")

    print(f"Wrote: {out_json}")
    print(f"Wrote: {out_md}")
    print(f"Wrote: {latest_json}")
    print(f"Wrote: {latest_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

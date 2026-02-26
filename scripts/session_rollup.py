#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
RTS Sessions rollup:
- Read sessions/<YYYY-MM>/session_<YYYYMMDD>.jsonl (JSON lines)
- Build monthly index.json + index.md
- Add Transitions (latest): detect structural breakpoints from event stream

Usage:
  python scripts/session_rollup.py 2026-02
  python scripts/session_rollup.py 2026-02 20260226
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from glob import glob
from typing import Any, Dict, List, Optional, Tuple


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_ts(ts: str) -> datetime:
    # expects "....Z" or ISO
    if ts.endswith("Z"):
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    return datetime.fromisoformat(ts)


def safe_load_json_line(line: str) -> Optional[Dict[str, Any]]:
    line = line.strip()
    if not line:
        return None
    try:
        return json.loads(line)
    except Exception:
        return None


@dataclass
class Transition:
    ts: str
    kind: str
    severity: str
    title: str
    detail: str
    run_id: Optional[str] = None
    commit: Optional[str] = None


def read_month_events(month: str) -> Tuple[List[Dict[str, Any]], List[str]]:
    month_dir = os.path.join("sessions", month)
    if not os.path.isdir(month_dir):
        return [], []

    jsonl_paths = sorted(glob(os.path.join(month_dir, "session_*.jsonl")))
    events: List[Dict[str, Any]] = []

    for p in jsonl_paths:
        with open(p, "r", encoding="utf-8") as f:
            for line in f:
                obj = safe_load_json_line(line)
                if obj is None:
                    continue
                # require minimal fields
                if "ts" not in obj or "kind" not in obj:
                    continue
                events.append(obj)

    # stable sort by timestamp
    events.sort(key=lambda e: parse_ts(str(e["ts"])))
    return events, [os.path.basename(p) for p in jsonl_paths]


def count_by_kind(events: List[Dict[str, Any]]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for e in events:
        k = str(e.get("kind", "unknown"))
        counts[k] = counts.get(k, 0) + 1
    return counts


def tail(events: List[Dict[str, Any]], n: int = 12) -> List[Dict[str, Any]]:
    return events[-n:] if len(events) > n else events[:]


def detect_transitions(events: List[Dict[str, Any]]) -> List[Transition]:
    """
    Human-first breakpoints from the event stream.
    Minimal but useful:
      - status flip (success<->failure) for sentinel.run
      - failure streak starts / ends
      - failure density spike in rolling window (last N)
    """
    sentinel = [e for e in events if e.get("kind") == "sentinel.run"]
    if len(sentinel) < 2:
        return []

    # normalize status
    def norm_status(e: Dict[str, Any]) -> str:
        # prefer conclusion; fallback status
        v = e.get("conclusion") or e.get("status") or ""
        return str(v).lower()

    # rolling window helpers
    WINDOW_N = 12
    SPIKE_DELTA = 2  # spike threshold (fail count increase vs previous window)

    statuses = [norm_status(e) for e in sentinel]
    times = [str(e["ts"]) for e in sentinel]

    # compute rolling failure counts (last N up to i)
    fail_counts: List[int] = []
    for i in range(len(statuses)):
        start = max(0, i - WINDOW_N + 1)
        window = statuses[start : i + 1]
        fail_counts.append(sum(1 for s in window if s in ("failure", "failed")))

    transitions: List[Transition] = []

    # 1) status flip (last few)
    for i in range(1, len(sentinel)):
        prev = sentinel[i - 1]
        cur = sentinel[i]
        ps = norm_status(prev)
        cs = norm_status(cur)
        if ps != cs:
            sev = "HIGH" if cs in ("failure", "failed") else "MED"
            title = f"status flip: {ps} → {cs}"
            detail = (
                f"workflow={cur.get('workflow','') or 'RTS Sentinel Analyze'} "
                f"run={cur.get('run_id','')} "
                f"commit={cur.get('commit','')}"
            ).strip()
            transitions.append(
                Transition(
                    ts=str(cur["ts"]),
                    kind="sentinel.run",
                    severity=sev,
                    title=title,
                    detail=detail,
                    run_id=str(cur.get("run_id")) if cur.get("run_id") else None,
                    commit=str(cur.get("commit")) if cur.get("commit") else None,
                )
            )

    # 2) failure streak boundaries (start/end)
    # streak start: prev != failure and cur == failure
    # streak end: prev == failure and cur != failure
    for i in range(1, len(statuses)):
        ps, cs = statuses[i - 1], statuses[i]
        if ps not in ("failure", "failed") and cs in ("failure", "failed"):
            transitions.append(
                Transition(
                    ts=times[i],
                    kind="sentinel.run",
                    severity="HIGH",
                    title="failure streak started",
                    detail=f"run={sentinel[i].get('run_id','')} commit={sentinel[i].get('commit','')}".strip(),
                    run_id=str(sentinel[i].get("run_id")) if sentinel[i].get("run_id") else None,
                    commit=str(sentinel[i].get("commit")) if sentinel[i].get("commit") else None,
                )
            )
        if ps in ("failure", "failed") and cs not in ("failure", "failed"):
            transitions.append(
                Transition(
                    ts=times[i],
                    kind="sentinel.run",
                    severity="MED",
                    title="failure streak ended (recovery)",
                    detail=f"run={sentinel[i].get('run_id','')} commit={sentinel[i].get('commit','')}".strip(),
                    run_id=str(sentinel[i].get("run_id")) if sentinel[i].get("run_id") else None,
                    commit=str(sentinel[i].get("commit")) if sentinel[i].get("commit") else None,
                )
            )

    # 3) failure density spike (rolling)
    # compare fail_counts[i] vs fail_counts[i-1] to catch steep increase
    for i in range(1, len(fail_counts)):
        delta = fail_counts[i] - fail_counts[i - 1]
        if delta >= SPIKE_DELTA and statuses[i] in ("failure", "failed"):
            transitions.append(
                Transition(
                    ts=times[i],
                    kind="sentinel.run",
                    severity="HIGH",
                    title="failure density spike",
                    detail=f"fail_count_last_{WINDOW_N}={fail_counts[i]} (+{delta}) run={sentinel[i].get('run_id','')}".strip(),
                    run_id=str(sentinel[i].get("run_id")) if sentinel[i].get("run_id") else None,
                    commit=str(sentinel[i].get("commit")) if sentinel[i].get("commit") else None,
                )
            )

    # keep only latest N transitions (human-first)
    transitions.sort(key=lambda t: parse_ts(t.ts))
    return transitions[-12:]


def render_index_md(
    month: str,
    updated_at_utc: str,
    counts: Dict[str, int],
    latest_tail: List[Dict[str, Any]],
    transitions: List[Transition],
    raw_ledgers: List[str],
) -> str:
    lines: List[str] = []
    lines.append(f"# RTS Sessions — {month}")
    lines.append("")
    lines.append(f"- updated_at_utc: `{updated_at_utc}`")
    lines.append("")
    lines.append("## Counts")
    lines.append("")
    for k in sorted(counts.keys()):
        lines.append(f"- `{k}`: {counts[k]}")
    lines.append("")

    lines.append("## Latest (tail)")
    lines.append("")
    for e in latest_tail:
        ts = str(e.get("ts", ""))
        kind = str(e.get("kind", ""))
        wf = str(e.get("workflow", ""))
        rid = str(e.get("run_id", ""))
        st = str((e.get("conclusion") or e.get("status") or ""))
        commit = str(e.get("commit", ""))
        note = str(e.get("note", "")).strip()
        # compact one-liner
        s = f"- `{ts}` `{kind}`"
        if wf:
            s += f" workflow={wf}"
        if rid:
            s += f" run={rid}"
        if st:
            s += f" status={st}"
        if commit:
            s += f" commit={commit}"
        if note:
            s += f" — {note}"
        lines.append(s)
    if not latest_tail:
        lines.append("- (none)")
    lines.append("")

    lines.append("## Transitions (latest)")
    lines.append("")
    if transitions:
        for t in transitions:
            s = f"- `{t.ts}` **{t.severity}** — {t.title}"
            if t.detail:
                s += f"  \n  {t.detail}"
            lines.append(s)
    else:
        lines.append("- (none)")
    lines.append("")

    lines.append("## Raw ledgers")
    lines.append("")
    for fn in raw_ledgers:
        lines.append(f"- `{fn}`")
    if not raw_ledgers:
        lines.append("- (none)")
    lines.append("")

    return "\n".join(lines)


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python scripts/session_rollup.py YYYY-MM [YYYYMMDD]", file=sys.stderr)
        return 2

    month = sys.argv[1].strip()
    month_dir = os.path.join("sessions", month)
    os.makedirs(month_dir, exist_ok=True)

    events, raw_ledgers = read_month_events(month)
    counts = count_by_kind(events)
    latest_tail = tail([e for e in events if e.get("kind") == "sentinel.run"], n=8)  # human-first
    transitions = detect_transitions(events)

    updated_at_utc = utc_now_iso()

    index_obj = {
        "month": month,
        "updated_at_utc": updated_at_utc,
        "counts": counts,
        "latest": [
            {
                "ts": e.get("ts"),
                "kind": e.get("kind"),
                "workflow": e.get("workflow"),
                "run_id": e.get("run_id"),
                "status": e.get("conclusion") or e.get("status"),
                "commit": e.get("commit"),
                "note": e.get("note"),
            }
            for e in latest_tail
        ],
        "transitions": [
            {
                "ts": t.ts,
                "kind": t.kind,
                "severity": t.severity,
                "title": t.title,
                "detail": t.detail,
                "run_id": t.run_id,
                "commit": t.commit,
            }
            for t in transitions
        ],
        "raw_ledgers": raw_ledgers,
    }

    index_json_path = os.path.join(month_dir, "index.json")
    index_md_path = os.path.join(month_dir, "index.md")

    with open(index_json_path, "w", encoding="utf-8") as f:
        json.dump(index_obj, f, ensure_ascii=False, indent=2)

    md = render_index_md(month, updated_at_utc, counts, latest_tail, transitions, raw_ledgers)
    with open(index_md_path, "w", encoding="utf-8") as f:
        f.write(md)

    print(f"Wrote: {index_json_path}")
    print(f"Wrote: {index_md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

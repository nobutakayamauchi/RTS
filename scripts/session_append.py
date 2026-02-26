#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
RTS Session Append (FULL REPLACE) — Month-wide idempotency

Append exactly one JSON event (one line) into:
  sessions/<YYYY-MM>/session_<YYYYMMDD>.jsonl

Hard rules:
- No sed, no YAML logic, Python-only JSON generation
- Idempotent on (kind, run_id) across the entire month directory (prevents UTC-day split duplicates)
- Always write UTC ISO ts with Z (if absent)
- Update sessions/<YYYY-MM>/checksums.sha256 over all files in that month dir

Usage:
  python scripts/session_append.py YYYY-MM payload.json
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from glob import glob
from typing import Any, Dict, Optional, Set, Tuple


# ---- config: dedupe scope ----
DEDUPE_KINDS = {"sentinel.run", "sentinel.run.start", "sentinel.run.end"}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_ts(ts: str) -> datetime:
    s = str(ts).strip()
    if s.endswith("Z"):
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    return datetime.fromisoformat(s)


def yyyymmdd_from_ts(ts: str) -> str:
    d = parse_ts(ts).astimezone(timezone.utc)
    return d.strftime("%Y%m%d")


def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        obj = json.load(f)
    if not isinstance(obj, dict):
        raise ValueError("payload must be a JSON object")
    return obj


def safe_load_json_line(line: str) -> Optional[Dict[str, Any]]:
    line = line.strip()
    if not line:
        return None
    try:
        obj = json.loads(line)
        return obj if isinstance(obj, dict) else None
    except Exception:
        return None


def ensure_month_dir(month: str) -> str:
    d = os.path.join("sessions", month)
    os.makedirs(d, exist_ok=True)
    return d


def ledger_path_for(month: str, day: str) -> str:
    return os.path.join("sessions", month, f"session_{day}.jsonl")


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def update_month_checksums(month_dir: str) -> str:
    """
    Compute checksums for all files in month_dir except checksums.sha256 itself.
    Output format: "<sha256>  <filename>"
    """
    out_path = os.path.join(month_dir, "checksums.sha256")
    files = sorted(
        p for p in glob(os.path.join(month_dir, "*"))
        if os.path.isfile(p) and os.path.basename(p) != "checksums.sha256"
    )
    lines = []
    for p in files:
        digest = sha256_file(p)
        lines.append(f"{digest}  {os.path.basename(p)}")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + ("\n" if lines else ""))
    return out_path


def normalize_event(payload: Dict[str, Any]) -> Dict[str, Any]:
    kind = str(payload.get("kind", "")).strip()
    if not kind:
        raise ValueError("payload.kind is required")

    ts = payload.get("ts")
    if not ts:
        payload["ts"] = utc_now_iso()
    else:
        _ = parse_ts(str(ts))  # validate parseable

    return payload


def build_month_run_id_index(month_dir: str) -> Set[Tuple[str, str]]:
    """
    Scan all session_*.jsonl in the month dir and return a set of (kind, run_id)
    for kinds in DEDUPE_KINDS only.
    """
    idx: Set[Tuple[str, str]] = set()
    paths = sorted(glob(os.path.join(month_dir, "session_*.jsonl")))
    for p in paths:
        with open(p, "r", encoding="utf-8") as f:
            for line in f:
                obj = safe_load_json_line(line)
                if not obj:
                    continue
                k = str(obj.get("kind", "")).strip()
                rid = str(obj.get("run_id", "")).strip()
                if not rid:
                    continue
                if k in DEDUPE_KINDS:
                    idx.add((k, rid))
    return idx


def main() -> int:
    if len(sys.argv) < 3:
        print("Usage: python scripts/session_append.py YYYY-MM payload.json", file=sys.stderr)
        return 2

    month = sys.argv[1].strip()
    payload_path = sys.argv[2].strip()

    payload = load_json(payload_path)
    payload = normalize_event(payload)

    month_dir = ensure_month_dir(month)

    kind = str(payload.get("kind", "")).strip()
    run_id = str(payload.get("run_id", "")).strip()

    # Month-wide idempotency for sentinel kinds only
    if run_id and kind in DEDUPE_KINDS:
        idx = build_month_run_id_index(month_dir)
        if (kind, run_id) in idx:
            print(f"Skip append (duplicate in month): kind={kind} run_id={run_id} month={month}")
            return 0

    ts = str(payload["ts"])
    day = yyyymmdd_from_ts(ts)
    ledger_path = ledger_path_for(month, day)

    # append one line (compact json)
    line = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    with open(ledger_path, "a", encoding="utf-8") as f:
        f.write(line + "\n")

    chk = update_month_checksums(month_dir)

    print(f"Appended: {ledger_path}")
    print(f"Updated: {chk}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

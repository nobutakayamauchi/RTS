from __future__ import annotations

import os
import json
import datetime as _dt
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


REQUIRED_PATHS = [
    "logs",
    "incidents",
    "radar",
    "vibecode",
    "START_HERE.py",
    "README.md",
]


@dataclass
class RTSState:
    status: str
    integrity: str
    signals: Dict[str, str]
    missing: List[str]
    timestamp_utc: str


def _utc_now_iso() -> str:
    return _dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def detect_repo_state(repo_root: str | Path = ".") -> RTSState:
    root = Path(repo_root)

    missing = []
    for p in REQUIRED_PATHS:
        if not (root / p).exists():
            missing.append(p)

    signals: Dict[str, str] = {}
    signals["repo_root"] = str(root.resolve())

    # Evidence signals
    exec_log = root / "logs" / "EXECUTION_LOG.md"
    radar_log = root / "logs" / "RADAR_LOG.md"

    signals["execution_log_present"] = "yes" if exec_log.exists() else "no"
    signals["radar_log_present"] = "yes" if radar_log.exists() else "no"

    # Basic "active" heuristic: any log present, or any incident file present
    has_any_logs = exec_log.exists() or radar_log.exists()
    has_incidents = (root / "incidents").exists() and any((root / "incidents").glob("**/*.*"))

    if missing:
        status = "INCOMPLETE"
        integrity = "UNVERIFIED"
        signals["reason"] = "missing required paths"
    else:
        status = "ACTIVE" if (has_any_logs or has_incidents) else "INITIALIZED"
        integrity = "VERIFIED" if has_any_logs else "UNVERIFIED"
        signals["reason"] = "evidence detected" if integrity == "VERIFIED" else "no evidence yet"

    return RTSState(
        status=status,
        integrity=integrity,
        signals=signals,
        missing=missing,
        timestamp_utc=_utc_now_iso(),
    )


def write_state_snapshot(repo_root: str | Path = ".", out_path: str | Path = "rts_state.json") -> RTSState:
    state = detect_repo_state(repo_root=repo_root)
    root = Path(repo_root)
    outp = root / out_path
    outp.write_text(json.dumps(state.__dict__, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return state

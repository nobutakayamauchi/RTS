from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class RepoState:
    repo_root: str
    timestamp_utc: str

    has_logs_dir: bool
    has_incidents_dir: bool
    has_memory_dir: bool
    has_evolution_dir: bool

    has_execution_log: bool
    has_result_log: bool
    has_success_log: bool
    has_reflection_log: bool

    status: str  # "READY" | "PARTIAL" | "EMPTY"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def detect_repo_state(repo_root: Path) -> RepoState:
    repo_root = repo_root.resolve()

    logs_dir = repo_root / "logs"
    incidents_dir = repo_root / "incidents"
    memory_dir = repo_root / "memory"
    evolution_dir = repo_root / "evolution"

    has_logs_dir = logs_dir.is_dir()
    has_incidents_dir = incidents_dir.is_dir()
    has_memory_dir = memory_dir.is_dir()
    has_evolution_dir = evolution_dir.is_dir()

    def exists_in_logs(name: str) -> bool:
        return (logs_dir / name).exists()

    has_execution_log = exists_in_logs("EXECUTION_LOG.md")
    has_result_log = exists_in_logs("RESULT_LOG.md")
    has_success_log = exists_in_logs("SUCCESS_LOG.md")
    has_reflection_log = exists_in_logs("RTS_REFLECTION_LOG.md") or exists_in_logs("REFLECTION_LOG.md")

    # Determine status
    core_dirs = [has_logs_dir, has_incidents_dir, has_memory_dir, has_evolution_dir]
    core_logs = [has_execution_log, has_result_log, has_success_log]

    if all(core_dirs) and all(core_logs):
        status = "READY"
    elif any(core_dirs) or any(core_logs):
        status = "PARTIAL"
    else:
        status = "EMPTY"

    return RepoState(
        repo_root=str(repo_root),
        timestamp_utc=_utc_now_iso(),
        has_logs_dir=has_logs_dir,
        has_incidents_dir=has_incidents_dir,
        has_memory_dir=has_memory_dir,
        has_evolution_dir=has_evolution_dir,
        has_execution_log=has_execution_log,
        has_result_log=has_result_log,
        has_success_log=has_success_log,
        has_reflection_log=has_reflection_log,
        status=status,
    )


def write_state_snapshot(repo_root: Path, state: RepoState) -> Path:
    """
    Writes repo state snapshot to: <repo_root>/rts_state.json
    """
    out_path = repo_root / "rts_state.json"
    out_path.write_text(json.dumps(asdict(state), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return out_path

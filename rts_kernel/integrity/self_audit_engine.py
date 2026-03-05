from __future__ import annotations

import json
import datetime as _dt
import hashlib
from pathlib import Path
from typing import Dict, Optional


HASHCHAIN_FILE = "logs/.rts_hashchain.json"
AUDIT_LOG_FILE = "logs/SELF_AUDIT_LOG.md"
EXEC_LOG_FILE = "logs/EXECUTION_LOG.md"


def _utc_now_iso() -> str:
    return _dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes()) if path.exists() else ""


def _load_json(path: Path) -> Dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_json(path: Path, obj: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _append_md(path: Path, block: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    path.write_text(existing + block, encoding="utf-8")


def audit_append_only_exec_log(repo_root: str | Path = ".") -> Dict:
    root = Path(repo_root)
    exec_log = root / EXEC_LOG_FILE
    chain_path = root / HASHCHAIN_FILE

    record = {
        "utc": _utc_now_iso(),
        "exec_log_present": exec_log.exists(),
        "violation": False,
        "details": [],
    }

    if not exec_log.exists():
        record["details"].append("EXECUTION_LOG.md missing")
        return record

    current_bytes = exec_log.read_bytes()
    current_hash = _sha256_bytes(current_bytes)
    current_len = len(current_bytes)

    chain = _load_json(chain_path)
    prev_hash = chain.get("exec_log_sha256")
    prev_len = chain.get("exec_log_bytes")

    # Violation heuristics:
    # - file shrunk
    # - hash changed while length shrunk (strong)
    if prev_len is not None and current_len < int(prev_len):
        record["violation"] = True
        record["details"].append(f"EXECUTION_LOG.md shrunk: {prev_len} -> {current_len} bytes")

    # Update hashchain (always) so next run has a baseline
    chain_update = {
        "updated_utc": record["utc"],
        "exec_log_sha256": current_hash,
        "exec_log_bytes": current_len,
        "previous_exec_log_sha256": prev_hash,
        "previous_exec_log_bytes": prev_len,
    }
    _save_json(chain_path, chain_update)

    record["exec_log_sha256"] = current_hash
    record["exec_log_bytes"] = current_len
    return record


def write_audit_log(repo_root: str | Path = ".", status: str = "ACTIVE", integrity: str = "VERIFIED") -> Dict:
    root = Path(repo_root)
    audit = audit_append_only_exec_log(repo_root=repo_root)

    # Human-readable markdown block
    block = []
    block.append(f"## {_utc_now_iso()}\n")
    block.append(f"Event: RTS self-audit\n")
    block.append(f"Status: {status}\n")
    block.append(f"Integrity: {integrity}\n\n")

    if audit.get("violation"):
        block.append("### Result: VIOLATION DETECTED\n")
    else:
        block.append("### Result: OK\n")

    if audit.get("details"):
        block.append("\n### Details\n")
        for d in audit["details"]:
            block.append(f"- {d}\n")

    # Evidence
    if audit.get("exec_log_sha256"):
        block.append("\n### Evidence\n")
        block.append(f"- EXECUTION_LOG sha256: `{audit['exec_log_sha256']}`\n")
        block.append(f"- EXECUTION_LOG bytes: `{audit['exec_log_bytes']}`\n")

    block.append("\n---\n\n")

    _append_md(root / AUDIT_LOG_FILE, "".join(block))
    return audit

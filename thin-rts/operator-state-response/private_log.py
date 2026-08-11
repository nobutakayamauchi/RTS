#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime
import json
import os
from pathlib import Path
from typing import Mapping


class PrivateLogError(RuntimeError):
    pass


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LOG_PATH = Path.home() / ".local" / "share" / "rts-private" / "operator-state" / "state.jsonl"


def _inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def validate_private_path(path: Path) -> Path:
    resolved = path.expanduser().resolve()
    if _inside(resolved, REPO_ROOT):
        raise PrivateLogError("health/operator-state logs must stay outside the public repository")
    return resolved


def append_private_record(record: Mapping[str, object], path: Path | None = None) -> Path:
    """Append a privacy-minimized JSONL record outside the repository.

    Callers should persist derived metrics/tags, not raw chat text. The function adds a timestamp
    when one is not already present and creates the file with owner-only permissions where supported.
    """
    target = validate_private_path(path or DEFAULT_LOG_PATH)
    target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    payload = dict(record)
    payload.setdefault("logged_at", datetime.now().astimezone().isoformat())
    line = json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n"

    fd = os.open(target, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
    try:
        with os.fdopen(fd, "a", encoding="utf-8") as stream:
            stream.write(line)
            stream.flush()
            os.fsync(stream.fileno())
    finally:
        try:
            os.chmod(target, 0o600)
        except OSError:
            pass
    return target

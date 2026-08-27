from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Callable

from .core import run_campaign


def _load_checkpoint(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def run_background_chunk(
    campaign: dict[str, Any],
    adapter: Callable[[dict[str, Any]], dict[str, Any]],
    checkpoint_path: str | Path,
    *,
    max_jobs_this_chunk: int,
) -> dict[str, Any]:
    """Run one bounded campaign chunk and atomically persist its checkpoint.

    The caller owns scheduling and the provider-specific adapter. This function owns
    resume semantics only: terminal jobs already present in the checkpoint are not
    executed again by ``run_campaign``.
    """

    path = Path(checkpoint_path)
    checkpoint = _load_checkpoint(path)
    result = run_campaign(
        campaign,
        adapter,
        checkpoint,
        max_jobs_this_chunk=max_jobs_this_chunk,
    )
    _atomic_write_json(path, result)
    return result

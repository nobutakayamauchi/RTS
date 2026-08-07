from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .config import BridgeConfig


@dataclass(frozen=True)
class SourceNote:
    relative_path: str
    absolute_path: Path
    content: bytes
    content_hash: str


def hash_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _excluded(relative: Path, excluded_dirs: tuple[str, ...]) -> bool:
    return any(part in excluded_dirs for part in relative.parts)


def iter_notes(config: BridgeConfig) -> Iterable[SourceNote]:
    vault = config.vault_path
    if not vault.exists() or not vault.is_dir():
        raise FileNotFoundError(f"Vault is unavailable: {vault}")

    seen: set[Path] = set()
    for pattern in config.include_globs:
        for path in sorted(vault.glob(pattern)):
            if not path.is_file() or path in seen:
                continue
            seen.add(path)
            relative = path.relative_to(vault)
            if _excluded(relative, config.exclude_dirs):
                continue
            content = path.read_bytes()
            yield SourceNote(
                relative_path=relative.as_posix(),
                absolute_path=path,
                content=content,
                content_hash=hash_bytes(content),
            )

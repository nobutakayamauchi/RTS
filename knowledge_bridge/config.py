from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class BridgeConfig:
    vault_path: Path
    state_path: Path
    include_globs: tuple[str, ...] = ("**/*.md",)
    exclude_dirs: tuple[str, ...] = (".obsidian", ".git", ".trash")

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "BridgeConfig":
        vault = Path(str(data["vault_path"])).expanduser().resolve()
        state = Path(str(data.get("state_path", ".rts/knowledge_bridge"))).expanduser().resolve()
        return cls(
            vault_path=vault,
            state_path=state,
            include_globs=tuple(data.get("include_globs", ["**/*.md"])),
            exclude_dirs=tuple(data.get("exclude_dirs", [".obsidian", ".git", ".trash"])),
        )


def load_config(path: str | Path) -> BridgeConfig:
    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as handle:
        raw = json.load(handle)
    return BridgeConfig.from_mapping(raw)

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .capture_store import CaptureStore
from .config import BridgeConfig, load_config
from .intake import iter_notes


def _config(args: argparse.Namespace) -> BridgeConfig:
    if args.config:
        return load_config(args.config)
    if not args.vault:
        raise SystemExit("--vault or --config is required")
    return BridgeConfig(
        vault_path=Path(args.vault).expanduser().resolve(),
        state_path=Path(args.state).expanduser().resolve(),
    )


def scan(args: argparse.Namespace) -> int:
    config = _config(args)
    store = CaptureStore(config.state_path)
    created = 0
    unchanged = 0
    records = []
    for note in iter_notes(config):
        record, was_created = store.capture(note)
        records.append({"capture_id": record.capture_id, "source_path": record.source_path, "created": was_created})
        created += int(was_created)
        unchanged += int(not was_created)
    print(json.dumps({"created": created, "unchanged": unchanged, "records": records}, ensure_ascii=False, indent=2))
    return 0


def verify(args: argparse.Namespace) -> int:
    config = _config(args)
    errors = CaptureStore(config.state_path).verify()
    print(json.dumps({"ok": not errors, "errors": errors}, ensure_ascii=False, indent=2))
    return 1 if errors else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="RTS Obsidian knowledge bridge")
    sub = parser.add_subparsers(dest="command", required=True)
    for name, handler in (("scan", scan), ("verify", verify)):
        command = sub.add_parser(name)
        command.add_argument("--vault")
        command.add_argument("--state", default=".rts/knowledge_bridge")
        command.add_argument("--config")
        command.set_defaults(handler=handler)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return int(args.handler(args))


if __name__ == "__main__":
    raise SystemExit(main())

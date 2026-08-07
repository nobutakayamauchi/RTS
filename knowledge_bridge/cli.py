from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from .capture_store import CaptureStore
from .challenge import challenge_record
from .config import BridgeConfig, load_config
from .connect import connect_record
from .council import analyze_implementation_council
from .design_e2e import run_design_e2e
from .freezer_export import export_freezer_draft
from .intake import iter_notes
from .intent_translator import translate_intent
from .normalize import normalize_capture
from .obsidian_adapter import run_obsidian_design
from .recall import SUPPORTED_EVENTS, recall_event
from .route import route_record


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


def normalize(args: argparse.Namespace) -> int:
    config = _config(args)
    record = normalize_capture(config.state_path, args.capture)
    print(json.dumps(asdict(record), ensure_ascii=False, indent=2))
    return 0


def connect(args: argparse.Namespace) -> int:
    config = _config(args)
    records = connect_record(config.state_path, args.knowledge)
    print(json.dumps([asdict(item) for item in records], ensure_ascii=False, indent=2))
    return 0


def challenge(args: argparse.Namespace) -> int:
    config = _config(args)
    result = challenge_record(config.state_path, args.knowledge)
    print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
    return 0 if result.promotion_ready else 2


def route(args: argparse.Namespace) -> int:
    config = _config(args)
    result = route_record(config.state_path, args.knowledge)
    print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
    return 0


def recall(args: argparse.Namespace) -> int:
    config = _config(args)
    results = recall_event(config.state_path, args.event, project_id=args.project, threshold=args.threshold)
    print(json.dumps([asdict(item) for item in results], ensure_ascii=False, indent=2))
    return 0


def export_freezer(args: argparse.Namespace) -> int:
    config = _config(args)
    result = export_freezer_draft(config.state_path, args.knowledge, args.output)
    print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
    return 0


def council(args: argparse.Namespace) -> int:
    config = _config(args)
    result = analyze_implementation_council(
        config.state_path,
        args.knowledge,
        args.repo,
        args.output,
    )
    print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
    return 0


def translate(args: argparse.Namespace) -> int:
    result = translate_intent(args.input, args.output)
    print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
    return 0


def design_e2e(args: argparse.Namespace) -> int:
    result = run_design_e2e(args.input, args.repo, args.output)
    print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
    return 0


def obsidian_design(args: argparse.Namespace) -> int:
    result = run_obsidian_design(args.vault, args.note, args.repo, args.review_dir)
    print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
    return 0


def _common(command: argparse.ArgumentParser) -> None:
    command.add_argument("--vault")
    command.add_argument("--state", default=".rts/knowledge_bridge")
    command.add_argument("--config")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="RTS Obsidian knowledge bridge")
    sub = parser.add_subparsers(dest="command", required=True)
    for name, handler in (("scan", scan), ("verify", verify)):
        command = sub.add_parser(name)
        _common(command)
        command.set_defaults(handler=handler)

    command = sub.add_parser("normalize")
    command.add_argument("--capture", required=True)
    _common(command)
    command.set_defaults(handler=normalize)

    for name, handler in (("connect", connect), ("challenge", challenge), ("route", route)):
        command = sub.add_parser(name)
        command.add_argument("--knowledge", required=True)
        _common(command)
        command.set_defaults(handler=handler)

    command = sub.add_parser("recall")
    command.add_argument("--event", required=True, choices=sorted(SUPPORTED_EVENTS))
    command.add_argument("--project")
    command.add_argument("--threshold", type=float, default=0.45)
    _common(command)
    command.set_defaults(handler=recall)

    command = sub.add_parser("export-freezer")
    command.add_argument("--knowledge", required=True)
    command.add_argument("--output", required=True)
    _common(command)
    command.set_defaults(handler=export_freezer)

    command = sub.add_parser("council")
    command.add_argument("--knowledge", required=True)
    command.add_argument("--repo", required=True)
    command.add_argument("--output", required=True)
    _common(command)
    command.set_defaults(handler=council)

    command = sub.add_parser("translate-intent")
    command.add_argument("--input", required=True)
    command.add_argument("--output", required=True)
    command.set_defaults(handler=translate)

    command = sub.add_parser("design-e2e")
    command.add_argument("--input", required=True)
    command.add_argument("--repo", required=True)
    command.add_argument("--output", required=True)
    command.set_defaults(handler=design_e2e)

    command = sub.add_parser("obsidian-design")
    command.add_argument("--vault", required=True)
    command.add_argument("--note", required=True)
    command.add_argument("--repo", required=True)
    command.add_argument("--review-dir", default="_RTS/Design Reviews")
    command.set_defaults(handler=obsidian_design)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return int(args.handler(args))


if __name__ == "__main__":
    raise SystemExit(main())

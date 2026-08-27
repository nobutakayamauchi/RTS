from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core import authorize_campaign, compile_campaign, observations_from_checkpoint


def _load(path: str):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write(path: str, value) -> None:
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    compile_cmd = sub.add_parser("compile")
    compile_cmd.add_argument("--plan", required=True)
    compile_cmd.add_argument("--tasks", required=True)
    compile_cmd.add_argument("--budget", required=True)
    compile_cmd.add_argument("--adapter-kind", choices=("fixture", "external"), default="fixture")
    compile_cmd.add_argument("--output", required=True)

    authorize_cmd = sub.add_parser("authorize")
    authorize_cmd.add_argument("--campaign", required=True)
    authorize_cmd.add_argument("--approval", required=True)
    authorize_cmd.add_argument("--output", required=True)

    observations_cmd = sub.add_parser("observations")
    observations_cmd.add_argument("--checkpoint", required=True)
    observations_cmd.add_argument("--output", required=True)

    args = parser.parse_args()
    if args.command == "compile":
        result = compile_campaign(
            _load(args.plan),
            _load(args.tasks),
            _load(args.budget),
            args.adapter_kind,
        )
    elif args.command == "authorize":
        result = authorize_campaign(_load(args.campaign), _load(args.approval))
    else:
        result = observations_from_checkpoint(_load(args.checkpoint))
    _write(args.output, result)


if __name__ == "__main__":
    main()

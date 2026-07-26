from __future__ import annotations

import argparse
import json
from pathlib import Path

from .common import PilotRunContractError, load_json
from .models import validate_seed

PACKAGE_DIR = Path(__file__).resolve().parent
DEFAULT_SEED = PACKAGE_DIR / "examples" / "value-discovery-case-001.json"


def load_and_validate(path: Path) -> dict:
    value = load_json(path)
    if not isinstance(value, dict):
        raise PilotRunContractError("pilot seed must contain an object")
    return validate_seed(value)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Verify a governed, non-authorizing pilot seed/run contract.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("verify", "summary"):
        command = subparsers.add_parser(name)
        command.add_argument("path", nargs="?", default=str(DEFAULT_SEED))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        seed = load_and_validate(Path(args.path))
    except PilotRunContractError as exc:
        print(str(exc))
        return 1
    if args.command == "verify":
        print(f"Pilot seed verification passed ({seed['seed_id']})")
        return 0
    summary = {
        "seed_id": seed["seed_id"],
        "seed_fingerprint": seed["seed_fingerprint"],
        "case_id": seed["project"]["case_id"],
        "readiness": seed["readiness"]["state"],
        "wip_limit": seed["constraints"]["wip_limit"],
        "human_gate_required": seed["constraints"]["human_gate_required"],
        "advisory_only": seed["authority"]["advisory_only"],
        "external_execution_authorized": seed["authority"]["external_execution_authorized"],
    }
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

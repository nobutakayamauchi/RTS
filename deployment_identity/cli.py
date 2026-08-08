from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .core import DeploymentIdentityError, build_snapshot, pretty_json, validate_snapshot


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="RTS Deployment Identity Probe v1")
    sub = parser.add_subparsers(dest="command", required=True)

    probe = sub.add_parser("probe", help="collect a read-only deployment identity snapshot")
    probe.add_argument("--root", type=Path)
    probe.add_argument("--service-unit")
    probe.add_argument("--active-route")
    probe.add_argument("--deployed-revision")
    probe.add_argument("--entrypoint")
    probe.add_argument("--artifact", type=Path)
    probe.add_argument("--observed-at")
    probe.add_argument("--require-established", action="store_true")

    verify = sub.add_parser("verify", help="validate an existing snapshot")
    verify.add_argument("snapshot", type=Path)
    verify.add_argument("--require-established", action="store_true")
    return parser


def command_probe(args: argparse.Namespace) -> int:
    snapshot = build_snapshot(
        root=args.root,
        service_unit=args.service_unit,
        active_route=args.active_route,
        deployed_revision=args.deployed_revision,
        entrypoint=args.entrypoint,
        artifact=args.artifact,
        observed_at=args.observed_at,
    )
    sys.stdout.write(pretty_json(snapshot))
    if args.require_established and snapshot["status"] != "ESTABLISHED":
        print(
            "ERROR: Deployment Identity is not ESTABLISHED; runtime implementation classification is forbidden",
            file=sys.stderr,
        )
        return 2
    return 0


def command_verify(args: argparse.Namespace) -> int:
    try:
        snapshot = json.loads(args.snapshot.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DeploymentIdentityError(f"unable to read snapshot: {exc}") from exc
    if not isinstance(snapshot, dict):
        raise DeploymentIdentityError("snapshot must be a JSON object")
    validate_snapshot(snapshot)
    if args.require_established and snapshot["status"] != "ESTABLISHED":
        print(
            "ERROR: Deployment Identity is not ESTABLISHED; runtime implementation classification is forbidden",
            file=sys.stderr,
        )
        return 2
    print(f"Deployment Identity verification passed: {snapshot['status']}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "probe":
            return command_probe(args)
        if args.command == "verify":
            return command_verify(args)
        raise DeploymentIdentityError(f"unknown command: {args.command}")
    except DeploymentIdentityError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from asset_manifest.core import (
    AssetManifestError,
    create_snapshot,
    diff_snapshots,
    load_current_snapshot,
    reindex,
    verify,
)

PACKAGE_DIR = Path(__file__).resolve().parent
DEFAULT_ROOT = PACKAGE_DIR.parent


def _print_json(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="RTS Cross-Repo Asset Manifest")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("create")
    create.add_argument("--input", type=Path, required=True)
    sub.add_parser("verify")
    sub.add_parser("reindex")
    sub.add_parser("list-repos")
    sub.add_parser("list-assets")
    show = sub.add_parser("show")
    show.add_argument("target")
    diff = sub.add_parser("diff")
    diff.add_argument("old_version", type=int)
    diff.add_argument("new_version", type=int)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.root.resolve()
    try:
        if args.command == "create":
            snapshot = create_snapshot(root, args.input.resolve())
            print(f"created v{snapshot['snapshot_version']:03d}")
        elif args.command == "verify":
            errors = verify(root)
            if errors:
                for error in errors:
                    print(f"ERROR: {error}", file=sys.stderr)
                return 1
            print("Asset Manifest verification passed")
        elif args.command == "reindex":
            indexes = reindex(root)
            print(f"indexed {indexes['repositories.json']['count']} repos and {indexes['assets.json']['count']} assets")
        elif args.command == "list-repos":
            snapshot = load_current_snapshot(root)
            for repo in sorted(snapshot["repositories"], key=lambda row: row["repository"]):
                print(f"{repo['repository']}\t{repo['visibility']}\t{repo['lifecycle_status']}\t{repo['role']}")
        elif args.command == "list-assets":
            snapshot = load_current_snapshot(root)
            for asset in sorted(snapshot["assets"], key=lambda row: row["asset_id"]):
                print(f"{asset['asset_id']}\t{asset['capability']}\t{asset['repository']}\t{asset['canonicality']}\t{asset['reuse_mode']}")
        elif args.command == "show":
            snapshot = load_current_snapshot(root)
            matches = [asset for asset in snapshot["assets"] if asset["asset_id"] == args.target]
            if not matches:
                matches = [repo for repo in snapshot["repositories"] if repo["repository"] == args.target]
            if not matches:
                raise AssetManifestError(f"unknown asset or repository: {args.target}")
            _print_json(matches[0])
        elif args.command == "diff":
            _print_json(diff_snapshots(root, args.old_version, args.new_version))
        return 0
    except AssetManifestError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

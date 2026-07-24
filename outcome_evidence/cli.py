from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

from .corpus import DEFAULT_ROOT, bundle_paths, corpus_summary
from .models import OutcomeEvidenceError, load_json, pretty_json, sha256_file, validate_bundle

PACKAGE_DIR = Path(__file__).resolve().parent
FORBIDDEN_MODULES = {"subprocess", "socket", "requests", "urllib", "http.client"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="RTS Governed Outcome Evidence Corpus v1")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("verify")
    sub.add_parser("list")
    show = sub.add_parser("show")
    show.add_argument("bundle_id")
    return parser


def _tracked_paths(root: Path) -> list[Path]:
    paths = bundle_paths(root)
    paths.extend(sorted((root / "outcome_evidence" / "evidence").glob("*.json")))
    paths.extend(sorted((root / "outcome_evidence").glob("*.py")))
    return sorted(set(path.resolve() for path in paths))


def _verify_no_external_action_dependencies() -> None:
    for path in sorted(PACKAGE_DIR.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            names: set[str]
            if isinstance(node, ast.Import):
                names = {alias.name for alias in node.names}
            elif isinstance(node, ast.ImportFrom):
                names = {node.module or ""}
            else:
                continue
            for name in names:
                if name in FORBIDDEN_MODULES or name.split(".")[0] in FORBIDDEN_MODULES:
                    raise OutcomeEvidenceError(
                        f"forbidden external-action dependency found in {path.name}: {name}"
                    )


def command_verify(root: Path) -> None:
    tracked = _tracked_paths(root)
    before = {path: sha256_file(path) for path in tracked}
    first = corpus_summary(root)
    second = corpus_summary(root)
    if pretty_json(first) != pretty_json(second):
        raise OutcomeEvidenceError("corpus summary is not deterministic")
    after = {path: sha256_file(path) for path in tracked}
    if before != after:
        raise OutcomeEvidenceError("verification modified governed corpus files")
    _verify_no_external_action_dependencies()
    print("Governed Outcome Evidence Corpus verification passed")


def command_list(root: Path) -> None:
    sys.stdout.write(pretty_json(corpus_summary(root)))


def command_show(root: Path, bundle_id: str) -> None:
    matches = []
    for path in bundle_paths(root):
        bundle = validate_bundle(load_json(path))
        if bundle["bundle_id"] == bundle_id:
            matches.append(bundle)
    if len(matches) != 1:
        raise OutcomeEvidenceError(f"bundle ID must resolve exactly once: {bundle_id}")
    sys.stdout.write(pretty_json(matches[0]))


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.root.resolve()
    try:
        if args.command == "verify":
            command_verify(root)
        elif args.command == "list":
            command_list(root)
        elif args.command == "show":
            command_show(root, args.bundle_id)
        else:
            raise OutcomeEvidenceError(f"unknown command: {args.command}")
    except OutcomeEvidenceError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
from pathlib import Path

from .state_engine import detect_repo_state, write_state_snapshot
from .indexing.memory_index_engine import build_index
from .self_audit import write_audit_log


def main() -> int:
    parser = argparse.ArgumentParser(
        description="RTS Kernel CLI — State / Index / Audit runner"
    )

    parser.add_argument(
        "--repo",
        default=".",
        help="Repository root path (default: current directory)",
    )

    parser.add_argument(
        "--state",
        action="store_true",
        help="Run state snapshot only",
    )

    parser.add_argument(
        "--index",
        action="store_true",
        help="Run memory indexing only",
    )

    parser.add_argument(
        "--audit",
        action="store_true",
        help="Run self audit only",
    )

    args = parser.parse_args()
    repo = Path(args.repo).resolve()

    # Default behavior: run all if no specific flag provided
    do_all = not (args.state or args.index or args.audit)
    if do_all:
        args.state = args.index = args.audit = True

    # --- STATE ---
    state = detect_repo_state(repo_root=repo)

    if args.state:
        write_state_snapshot(
            repo_root=repo,
            state=state,
        )

    # --- INDEX ---
    if args.index:
        build_index(
            repo_root=repo,
        )

    # --- AUDIT ---
    if args.audit:
        write_audit_log(
            repo_root=repo,
            state=state,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

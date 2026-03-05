from __future__ import annotations

import argparse
from pathlib import Path

from .state_engine import write_state_snapshot, detect_repo_state
from .memory_index import build_index
from .self_audit import write_audit_log


def main() -> int:
    parser = argparse.ArgumentParser(description="RTS OS Kernel (v0.1)")
    parser.add_argument("--repo", default=".", help="Repository root")
    parser.add_argument("--state", action="store_true", help="Write rts_state.json")
    parser.add_argument("--index", action="store_true", help="Write rts_index.json")
    parser.add_argument("--audit", action="store_true", help="Append logs/SELF_AUDIT_LOG.md and update hashchain")
    args = parser.parse_args()

    repo = Path(args.repo)

    # Default: do all
    do_all = not (args.state or args.index or args.audit)
    if do_all:
        args.state = args.index = args.audit = True

    state = detect_repo_state(repo_root=repo)

    if args.state:
        write_state_snapshot(repo_root=repo, out_path="rts_state.json")

    if args.index:
        build_index(repo_root=repo, out_path="rts_index.json")

    if args.audit:
        write_audit_log(repo_root=repo, status=state.status, integrity=state.integrity)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

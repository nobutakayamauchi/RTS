from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core import build_profile, detect_drift, plan_probe_matrix, validate_observations


def load(path: str):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="RTS Adaptive Engine Profiler v1")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("validate")
    p.add_argument("--input", required=True)
    p = sub.add_parser("plan")
    p.add_argument("--engine", required=True)
    p.add_argument("--domain", required=True)
    p.add_argument("--prior-profile")
    p.add_argument("--max-probes", type=int, default=8)
    p = sub.add_parser("profile")
    p.add_argument("--input", required=True)
    p.add_argument("--engine", required=True)
    p.add_argument("--domain", required=True)
    p = sub.add_parser("drift")
    p.add_argument("--profile", required=True)
    p.add_argument("--input", required=True)
    p.add_argument("--engine", required=True)
    args = parser.parse_args()
    if args.command == "validate":
        rows = validate_observations(load(args.input))
        result = {"status": "PASS", "observations": len(rows)}
    elif args.command == "plan":
        result = plan_probe_matrix(
            load(args.engine),
            args.domain,
            load(args.prior_profile) if args.prior_profile else None,
            args.max_probes,
        )
    elif args.command == "profile":
        result = build_profile(load(args.input), load(args.engine), args.domain)
    else:
        result = detect_drift(load(args.profile), load(args.input), load(args.engine))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

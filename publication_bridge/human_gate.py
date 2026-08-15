from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .core import PublicationBridgeError, build_humanization_record, load_bundle


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Record a completed /human pass for external X/note drafts. This command does not rewrite copy."
    )
    parser.add_argument("bundle_dir", type=Path, help="Post Adapter bundle directory after /human rewrite")
    parser.add_argument("--reviewer", required=True, help="Reviewer/mode identity, normally /human")
    parser.add_argument(
        "--evidence-preserved",
        action="store_true",
        help="Explicitly attest that verified facts, prices, URLs, scope and boundaries were preserved",
    )
    parser.add_argument("--notes", default="", help="Optional /human review note")
    args = parser.parse_args(argv)

    try:
        manifest, drafts = load_bundle(args.bundle_dir)
        if manifest.get("verification_warnings"):
            raise PublicationBridgeError("cannot /human-approve a bundle with verification warnings")
        if manifest.get("human_review_state") not in {"APPROVED_FOR_COPY", "APPROVED_FOR_HANDOFF"}:
            raise PublicationBridgeError("bundle must first be APPROVED_FOR_COPY")

        record = build_humanization_record(
            drafts,
            reviewer=args.reviewer,
            evidence_preserved=args.evidence_preserved,
            notes=args.notes,
        )
        manifest["humanization"] = record
        manifest["human_review_state"] = "APPROVED_FOR_HANDOFF"
        (args.bundle_dir / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    except (OSError, json.JSONDecodeError, PublicationBridgeError) as exc:
        print(f"publication-human-gate: {exc}", file=sys.stderr)
        return 2

    print(
        json.dumps(
            {
                "state": "APPROVED_FOR_HANDOFF",
                "humanization_mode": record["mode"],
                "reviewed_channels": record["reviewed_channels"],
                "evidence_preserved": record["evidence_preserved"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

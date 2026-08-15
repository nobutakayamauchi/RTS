from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .core import PublicationBridgeError, build_handoff, load_bundle, render_handoff_html


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prepare reviewed drafts for human handoff to X and note without auto-publishing.")
    parser.add_argument("bundle_dir", type=Path, help="Post Adapter bundle directory")
    parser.add_argument("--out-dir", type=Path, required=True, help="Output directory")
    args = parser.parse_args(argv)

    try:
        manifest, drafts = load_bundle(args.bundle_dir)
        handoff = build_handoff(manifest, drafts)
        args.out_dir.mkdir(parents=True, exist_ok=True)
        (args.out_dir / "handoff.json").write_text(json.dumps(handoff, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (args.out_dir / "index.html").write_text(render_handoff_html(handoff), encoding="utf-8")
    except (OSError, json.JSONDecodeError, PublicationBridgeError) as exc:
        print(f"publication-bridge: {exc}", file=sys.stderr)
        return 2

    print(json.dumps({"state": handoff["state"], "actions": len(handoff["actions"]), "automatic_publication": False, "out_dir": str(args.out_dir)}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .common_ui import build_common_view_model
from .obsidian_adapter import run_obsidian_design

_TRACKED_TYPES = {"feature", "implementation_target", "missing_part"}


@dataclass(frozen=True)
class DogfoodStartResult:
    run_path: str
    bundle_path: str
    common_ui_path: str
    observations_path: str
    request_id: str
    project_id: str
    planned_count: int
    status: str
    human_decision_required: bool


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object in {path}")
    return value


def start_dogfood(
    vault_path: str | Path,
    note_relative_path: str | Path,
    repo_root: str | Path,
    output_root: str | Path,
) -> DogfoodStartResult:
    output = Path(output_root).expanduser().resolve()
    if output.exists():
        raise FileExistsError(f"refusing to overwrite dogfood run: {output}")
    output.mkdir(parents=True)

    review = run_obsidian_design(vault_path, note_relative_path, repo_root)
    source_bundle = Path(review.bundle_path)
    bundle = output / "bundle"
    shutil.copytree(source_bundle, bundle)

    common_ui = output / "common-ui.json"
    build_common_view_model(bundle, common_ui)

    translation = _load(bundle / "translation.json")
    nodes = translation.get("planned_structure", {}).get("nodes", [])
    tracked = [
        node for node in nodes
        if isinstance(node, dict) and node.get("type") in _TRACKED_TYPES and node.get("id")
    ]
    observations = {
        "schema_version": "1.0",
        "request_id": translation["request_id"],
        "project_id": translation["project_id"],
        "instructions": "Fill observations with AS_BUILT, BROKEN, or STALE evidence from the real dogfood run. Do not invent evidence.",
        "planned_nodes": [
            {
                "node_id": node["id"],
                "type": node.get("type"),
                "label": node.get("label", node.get("title", node["id"])),
            }
            for node in tracked
        ],
        "observations": [],
    }
    observations_path = output / "observations.json"
    observations_path.write_text(json.dumps(observations, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    manifest = {
        "schema_version": "1.0",
        "mode": "rts-dogfood-v1",
        "request_id": translation["request_id"],
        "project_id": translation["project_id"],
        "source_note": review.source_note,
        "bundle": "bundle",
        "common_ui": "common-ui.json",
        "common_ui_html": "common-ui.html",
        "observations": "observations.json",
        "planned_count": len(tracked),
        "status": "AWAITING_REAL_OBSERVATIONS",
        "human_decision_required": True,
        "implementation_executed": False,
        "next_action": "Use the real project, record evidence in observations.json, then run debug-link and city-release.",
    }
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return DogfoodStartResult(
        run_path=str(output),
        bundle_path=str(bundle),
        common_ui_path=str(common_ui),
        observations_path=str(observations_path),
        request_id=translation["request_id"],
        project_id=translation["project_id"],
        planned_count=len(tracked),
        status="AWAITING_REAL_OBSERVATIONS",
        human_decision_required=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Start one RTS dogfood run across Obsidian, common UI, and debug evidence")
    parser.add_argument("--vault", required=True)
    parser.add_argument("--note", required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = start_dogfood(args.vault, args.note, args.repo, args.output)
    print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

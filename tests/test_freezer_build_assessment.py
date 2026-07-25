from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from freezer.cli import rebuild


def _load_cases():
    path = Path(__file__).with_name("_freezer_build_assessment_cases.py")
    spec = importlib.util.spec_from_file_location(
        "_rts_freezer_build_assessment_cases", path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load test cases: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_CASES = _load_cases()


class BuildAssessmentTests(_CASES.BuildAssessmentTests):
    def isolated_root(self, temp_dir: str) -> Path:
        root = super().isolated_root(temp_dir)
        items_root = root / "freezer" / "items"
        for pointer_path in sorted(items_root.glob("RTS-FRZ-*/current.json")):
            pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
            item_path = root / pointer["path"]
            item = json.loads(item_path.read_text(encoding="utf-8"))
            if item["status"] in {"SELECTED", "IN_PROGRESS"}:
                item["status"] = "FROZEN"
                item["build_authority"] = "NOT_APPROVED"
                item_path.write_text(
                    json.dumps(item, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
        rebuild(root)
        return root

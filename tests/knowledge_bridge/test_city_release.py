from __future__ import annotations

import json
from pathlib import Path

import pytest

from knowledge_bridge.city_release import audit_city_release


def _write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def _fixture(tmp_path: Path) -> tuple[Path, Path]:
    bundle = tmp_path / "bundle"
    _write(bundle / "translation.json", {"request_id": "REQ-1", "project_id": "PRJ-1"})
    _write(bundle / "summary.json", {"request_id": "REQ-1", "project_id": "PRJ-1", "implementation_executed": False})
    lifecycle = tmp_path / "lifecycle.json"
    _write(lifecycle, {
        "request_id": "REQ-1",
        "project_id": "PRJ-1",
        "counts": {"planned": 5, "as_built": 1, "broken": 1, "stale": 1, "unobserved": 2, "orphan": 0},
        "approval": {"implementation_executed": False},
    })
    return bundle, lifecycle


def test_city_release_freezes_v1_and_selects_dogfooding(tmp_path: Path) -> None:
    bundle, lifecycle = _fixture(tmp_path)
    output = tmp_path / "release.json"
    result = audit_city_release(bundle, lifecycle, output)
    report = json.loads(output.read_text())
    assert result.next_city == "DOGFOODING"
    assert result.decision == "V1_SCOPE_COMPLETE_WITH_KNOWN_ISSUES"
    assert report["status"] == "AWAITING_HUMAN_RELEASE_DECISION"
    assert report["implementation_executed"] is False
    assert "Full Obsidian rewrite" in report["do_not_build_now"]
    assert output.with_suffix(".md").exists()


def test_city_release_rejects_identity_mismatch(tmp_path: Path) -> None:
    bundle, lifecycle = _fixture(tmp_path)
    value = json.loads(lifecycle.read_text())
    value["project_id"] = "PRJ-OTHER"
    _write(lifecycle, value)
    with pytest.raises(ValueError, match="project identity"):
        audit_city_release(bundle, lifecycle, tmp_path / "release.json")


def test_city_release_refuses_execution_evidence(tmp_path: Path) -> None:
    bundle, lifecycle = _fixture(tmp_path)
    value = json.loads(lifecycle.read_text())
    value["approval"]["implementation_executed"] = True
    _write(lifecycle, value)
    with pytest.raises(PermissionError, match="execution"):
        audit_city_release(bundle, lifecycle, tmp_path / "release.json")

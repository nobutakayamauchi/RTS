from __future__ import annotations

import json
from pathlib import Path

import pytest

from knowledge_bridge.common_ui import build_common_view_model


def _write(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def _bundle(root: Path, *, status: str = "AWAITING_HUMAN_DECISION", executed: bool = False) -> Path:
    root.mkdir()
    _write(
        root / "translation.json",
        {
            "request_id": "REQ-1",
            "project_id": "PRJ-1",
            "title": "Mobile player",
            "domain": "music",
            "target_user": "beginner",
            "inferred_goals": ["Reach playlists quickly."],
            "feature_decisions": [
                {"feature": "playlist shortcut", "decision": "KEEP", "reason": "Primary path."}
            ],
            "planned_structure": {
                "nodes": [{"id": "REQ-1", "type": "request", "label": "Mobile player"}],
                "edges": [],
            },
        },
    )
    _write(
        root / "summary.json",
        {
            "request_id": "REQ-1",
            "project_id": "PRJ-1",
            "status": status,
            "implementation_executed": executed,
            "missing_parts": [
                {"category": "blocking", "name": "navigation contract", "reason": "Needed before implementation."}
            ],
            "insertion_candidates": ["web/player.py::PlayerView"],
            "related_freezer_items": ["RTS-FRZ-000001:freezer/items/current.json"],
            "human_questions": ["Should this remain one tap?"],
        },
    )
    _write(
        root / "council.json",
        {"recommendation": "DISCUSS", "implementation_strategy": "HOLD_FOR_HUMAN"},
    )
    return root


def test_builds_five_section_view_model_and_html(tmp_path: Path) -> None:
    bundle = _bundle(tmp_path / "bundle")
    result = build_common_view_model(bundle, tmp_path / "view.json")
    model = json.loads(Path(result.view_model_path).read_text(encoding="utf-8"))
    assert set(model["sections"]) == {"request", "plan", "missing", "connections", "approval"}
    assert model["sections"]["approval"]["human_decision_required"] is True
    assert model["sections"]["approval"]["implementation_executed"] is False
    html = Path(result.html_path).read_text(encoding="utf-8")
    for title in ("要望", "計画", "不足", "接続先", "承認"):
        assert title in html
    assert "コード変更・実装は実行されていません" in html


def test_refuses_non_gated_or_executed_bundle(tmp_path: Path) -> None:
    with pytest.raises(PermissionError):
        build_common_view_model(_bundle(tmp_path / "bad-status", status="APPROVED"), tmp_path / "a.json")
    with pytest.raises(PermissionError):
        build_common_view_model(_bundle(tmp_path / "executed", executed=True), tmp_path / "b.json")


def test_refuses_identity_mismatch_and_overwrite(tmp_path: Path) -> None:
    bundle = _bundle(tmp_path / "bundle")
    summary = json.loads((bundle / "summary.json").read_text(encoding="utf-8"))
    summary["request_id"] = "REQ-OTHER"
    _write(bundle / "summary.json", summary)
    with pytest.raises(ValueError):
        build_common_view_model(bundle, tmp_path / "bad.json")

    clean = _bundle(tmp_path / "clean")
    output = tmp_path / "view.json"
    build_common_view_model(clean, output)
    with pytest.raises(FileExistsError):
        build_common_view_model(clean, output)

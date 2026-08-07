from __future__ import annotations

import json
from pathlib import Path

import pytest

from knowledge_bridge.idea_router import route_idea


def _write(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


def test_routes_raw_vlog_save_export_idea_to_v1(tmp_path: Path) -> None:
    source = tmp_path / "idea.json"
    _write(source, {
        "idea": "Vlogの保存と書き出し導線を直したい。保存で固まる問題も確認したい。",
        "known_projects": ["vlog", "RTS"],
        "constraints": ["スマホ中心", "既存編集機能を壊さない"],
        "freezer_matches": ["FRZ-SAVE-EXPORT"],
    })
    result = route_idea(source, tmp_path / "route.json")
    report = json.loads((tmp_path / "route.json").read_text())
    assert result.target_project == "vlog"
    assert result.target_component == "save-export"
    assert result.timing == "NOW"
    assert result.routing_action == "ROUTE_TO_V1"
    assert report["human_decision_required"] is True
    assert report["implementation_executed"] is False
    assert report["context_matches"] == ["FRZ-SAVE-EXPORT"]
    v1 = json.loads((tmp_path / "route.v1-input.json").read_text())
    assert v1["project_id"] == "vlog"
    assert v1["feedback"]


def test_normalizes_string_features_and_references_to_v1_contract(tmp_path: Path) -> None:
    source = tmp_path / "idea.json"
    _write(source, {
        "idea": "Vlogの保存導線を直したい",
        "project_hint": "vlog",
        "component_hint": "save-export",
        "constraints": ["既存機能を壊さない"],
        "features": ["保存処理", "書き出し処理"],
        "references": ["save-export-reference"],
    })
    route_idea(source, tmp_path / "route.json")
    v1 = json.loads((tmp_path / "route.v1-input.json").read_text())
    assert v1["features"] == [
        {"feature": "保存処理", "decision": "KEEP", "reason": "Supplied by V1.1 raw idea context."},
        {"feature": "書き出し処理", "decision": "KEEP", "reason": "Supplied by V1.1 raw idea context."},
    ]
    assert v1["references"][0]["reference_id"] == "save-export-reference"


def test_preserves_structured_features(tmp_path: Path) -> None:
    source = tmp_path / "idea.json"
    _write(source, {
        "idea": "Vlog保存を直したい",
        "project_hint": "vlog",
        "component_hint": "save-export",
        "constraints": ["既存機能を壊さない"],
        "features": [{"feature": "保存処理", "decision": "SIMPLIFY", "reason": "導線を短くする"}],
    })
    route_idea(source, tmp_path / "route.json")
    v1 = json.loads((tmp_path / "route.v1-input.json").read_text())
    assert v1["features"] == [{"feature": "保存処理", "decision": "SIMPLIFY", "reason": "導線を短くする"}]


def test_clarifies_when_target_is_unknown(tmp_path: Path) -> None:
    source = tmp_path / "idea.json"
    _write(source, {"idea": "なんかもっと気持ちよくしたい"})
    result = route_idea(source, tmp_path / "route.json")
    report = json.loads((tmp_path / "route.json").read_text())
    assert result.timing == "CLARIFY"
    assert result.routing_action == "ASK_HUMAN"
    assert "target_project" in report["missing_parts"]
    assert "target_component" in report["missing_parts"]


def test_defer_does_not_route_automatically(tmp_path: Path) -> None:
    source = tmp_path / "idea.json"
    _write(source, {
        "idea": "VlogのYouTubeアップロードは保存導線の安定後に追加したい",
        "known_projects": ["vlog"],
        "known_components": ["upload"],
    })
    result = route_idea(source, tmp_path / "route.json")
    assert result.timing == "DEFER"
    assert result.routing_action == "FREEZE_FOR_LATER"
    assert result.implementation_executed is False


def test_requires_idea_and_refuses_overwrite(tmp_path: Path) -> None:
    source = tmp_path / "idea.json"
    _write(source, {})
    with pytest.raises(ValueError, match="idea is required"):
        route_idea(source, tmp_path / "route.json")

    _write(source, {"idea": "Vlog保存を直したい", "project_hint": "vlog", "component_hint": "save-export"})
    output = tmp_path / "route.json"
    route_idea(source, output)
    with pytest.raises(FileExistsError):
        route_idea(source, output)

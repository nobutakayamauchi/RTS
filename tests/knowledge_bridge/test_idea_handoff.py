from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import knowledge_bridge.idea_handoff as handoff


def _report(path: Path, **overrides: object) -> None:
    value = {
        "idea_id": "IDEA-1",
        "status": "AWAITING_HUMAN_ROUTING_DECISION",
        "routing_action": "ROUTE_TO_V1",
        "timing": "NOW",
        "missing_parts": [],
        "human_questions": [],
        "v1_input": {"title": "Vlog save export", "project_id": "vlog"},
    }
    value.update(overrides)
    path.write_text(json.dumps(value), encoding="utf-8")


def test_requires_explicit_approval(tmp_path: Path) -> None:
    report = tmp_path / "route.json"
    _report(report)
    with pytest.raises(PermissionError):
        handoff.handoff_approved_idea(report, tmp_path / "repo", tmp_path / "out", "NEXT")


def test_hands_approved_route_to_existing_v1(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    report = tmp_path / "route.json"
    _report(report)

    def fake_e2e(input_path: Path, repo_root: Path, output_path: Path) -> SimpleNamespace:
        assert json.loads(Path(input_path).read_text())["project_id"] == "vlog"
        output_path.mkdir(parents=True)
        return SimpleNamespace(request_id="REQ-1", project_id="vlog")

    monkeypatch.setattr(handoff, "run_design_e2e", fake_e2e)
    result = handoff.handoff_approved_idea(report, tmp_path / "repo", tmp_path / "out", "APPROVE")
    assert result.status == "HANDED_OFF_TO_V1_AWAITING_HUMAN_DECISION"
    assert result.implementation_executed is False
    record = json.loads((tmp_path / "out" / "handoff.json").read_text())
    assert record["human_decision_recorded"] is True
    assert record["implementation_executed"] is False


def test_refuses_unresolved_or_deferred_route(tmp_path: Path) -> None:
    report = tmp_path / "route.json"
    _report(report, timing="DEFER", routing_action="FREEZE_FOR_LATER")
    with pytest.raises(ValueError):
        handoff.handoff_approved_idea(report, tmp_path / "repo", tmp_path / "out", "APPROVE")

from __future__ import annotations

import json
from pathlib import Path

import pytest

from knowledge_bridge.intent_translator import translate_intent


def _write(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def test_translates_ambiguous_feedback_into_constraints(tmp_path: Path) -> None:
    source = tmp_path / "input.json"
    output = tmp_path / "brief.json"
    _write(
        source,
        {
            "title": "Music player",
            "domain": "music",
            "role": "listener",
            "target_user": "beginner smartphone user",
            "feedback": ["This is too complex", "I want one-tap access", "This button is unclear"],
        },
    )
    brief = translate_intent(source, output)
    assert brief.status == "AWAITING_HUMAN_DECISION"
    assert brief.human_decision_required is True
    assert any("cognitive load" in item for item in brief.inferred_goals)
    assert any("fixed navigation" in item for item in brief.design_constraints)
    assert any("ambiguous icon" in item for item in brief.design_constraints)
    assert output.exists()
    assert output.with_suffix(".md").exists()


def test_reference_ledger_and_feature_decisions_are_preserved(tmp_path: Path) -> None:
    source = tmp_path / "input.json"
    _write(
        source,
        {
            "title": "Player",
            "goals": ["Make playback immediately understandable."],
            "references": [
                {
                    "reference_id": "REF-A",
                    "reaction": "like",
                    "adopted": ["large artwork", "bottom controls"],
                    "rejected": ["unlabeled icons"],
                }
            ],
            "features": [
                {"feature": "equalizer", "decision": "DEFER", "reason": "Not required for first playback."},
                {"feature": "play button", "decision": "KEEP", "reason": "Primary action."},
            ],
        },
    )
    brief = translate_intent(source, tmp_path / "brief.json")
    assert brief.reference_ledger[0].adopted == ("large artwork", "bottom controls")
    assert {item.decision for item in brief.feature_decisions} == {"KEEP", "DEFER"}


def test_sensory_profile_is_bounded(tmp_path: Path) -> None:
    source = tmp_path / "input.json"
    _write(source, {"goals": ["Create a calm player."], "sensory_profile": {"gloss": 4, "motion": -3, "spacing": 0.5}})
    brief = translate_intent(source, tmp_path / "brief.json")
    assert brief.sensory_profile == {"gloss": 1.0, "motion": -1.0, "spacing": 0.5}


def test_confusing_reference_without_notes_requests_clarification(tmp_path: Path) -> None:
    source = tmp_path / "input.json"
    _write(source, {"goals": ["Clarify controls."], "references": [{"reference_id": "REF-X", "reaction": "confusing"}]})
    brief = translate_intent(source, tmp_path / "brief.json")
    assert any("confusing reference" in item for item in brief.unresolved_questions)


def test_refuses_overwrite_and_invalid_decisions(tmp_path: Path) -> None:
    source = tmp_path / "input.json"
    output = tmp_path / "brief.json"
    _write(source, {"goals": ["A"], "features": [{"feature": "x", "decision": "KEEP"}]})
    translate_intent(source, output)
    with pytest.raises(FileExistsError):
        translate_intent(source, output)

    bad = tmp_path / "bad.json"
    _write(bad, {"features": [{"feature": "x", "decision": "MAGIC"}]})
    with pytest.raises(ValueError):
        translate_intent(bad, tmp_path / "bad-output.json")

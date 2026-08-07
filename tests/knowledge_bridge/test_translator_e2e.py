from __future__ import annotations

import json
from pathlib import Path

from knowledge_bridge.intent_translator import translate_intent


def test_music_player_design_translation_e2e(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    source = repo_root / "examples" / "design_function_translator" / "music_player_e2e.json"
    output = tmp_path / "music-player-brief.json"

    brief = translate_intent(source, output)
    payload = json.loads(output.read_text(encoding="utf-8"))
    markdown = output.with_suffix(".md").read_text(encoding="utf-8")

    assert brief.status == "AWAITING_HUMAN_DECISION"
    assert brief.human_decision_required is True
    assert any("cognitive load" in item for item in brief.inferred_goals)
    assert any("minimal navigation" in item for item in brief.inferred_goals)
    assert any("ambiguous icon" in item for item in brief.design_constraints)
    assert {item.decision for item in brief.feature_decisions} >= {"KEEP", "DEFER", "REMOVE"}
    assert len(brief.reference_ledger) == 2
    assert brief.sensory_profile["spacing"] == 0.8
    assert brief.unresolved_questions

    assert payload["status"] == "AWAITING_HUMAN_DECISION"
    assert payload["human_decision_required"] is True
    assert "No design approval or implementation was executed." in markdown
    assert "プレイリスト固定導線" in markdown
    assert "REF-A" in markdown

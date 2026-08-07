from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import pytest

from knowledge_bridge.contract import validate_output_contract
from knowledge_bridge.intent_translator import translate_intent


def _write(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def test_contract_adds_stable_ids_version_and_planned_graph(tmp_path: Path) -> None:
    source = tmp_path / "input.json"
    output = tmp_path / "brief.json"
    payload = {
        "title": "Simple player",
        "domain": "music",
        "feedback": ["Too complex", "I want one-tap access"],
        "features": [
            {"feature": "playback", "decision": "KEEP", "reason": "Primary action."},
            {"feature": "equalizer", "decision": "DEFER", "reason": "Advanced option."},
        ],
    }
    _write(source, payload)

    brief = translate_intent(source, output)
    written = json.loads(output.read_text(encoding="utf-8"))

    assert brief.schema_version == "1.0"
    assert brief.request_id.startswith("REQ-")
    assert brief.project_id.startswith("PRJ-")
    assert written["planned_structure"]["nodes"]
    assert any(edge["type"] == "requires_approval" for edge in written["planned_structure"]["edges"])
    assert validate_output_contract(written) == ()


def test_supplied_ids_are_preserved_for_obsidian_and_ui_adapters(tmp_path: Path) -> None:
    source = tmp_path / "input.json"
    output = tmp_path / "brief.json"
    _write(
        source,
        {
            "schema_version": "1.0",
            "request_id": "REQ-OBSIDIAN-1",
            "project_id": "PRJ-RTS",
            "goals": ["Keep one shared contract."],
        },
    )
    brief = translate_intent(source, output)
    assert brief.request_id == "REQ-OBSIDIAN-1"
    assert brief.project_id == "PRJ-RTS"


def test_old_input_without_contract_fields_remains_supported(tmp_path: Path) -> None:
    source = tmp_path / "legacy.json"
    _write(source, {"goals": ["Preserve legacy callers."], "features": []})
    brief = translate_intent(source, tmp_path / "brief.json")
    assert brief.schema_version == "1.0"
    assert brief.status == "AWAITING_HUMAN_DECISION"


def test_missing_scope_is_exposed_as_planned_blocker(tmp_path: Path) -> None:
    source = tmp_path / "input.json"
    output = tmp_path / "brief.json"
    _write(source, {"title": "Undefined request"})
    brief = translate_intent(source, output)
    assert "primary_outcome" in brief.missing_parts
    assert "feature_scope" in brief.missing_parts
    assert any(node.type == "missing_part" and node.status == "blocking" for node in brief.planned_structure.nodes)


def test_rejects_unsupported_schema_version_before_writing(tmp_path: Path) -> None:
    source = tmp_path / "input.json"
    output = tmp_path / "brief.json"
    _write(source, {"schema_version": "9.0", "goals": ["Nope"]})
    with pytest.raises(ValueError, match="schema_version"):
        translate_intent(source, output)
    assert not output.exists()

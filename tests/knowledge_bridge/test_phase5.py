from __future__ import annotations

import json
from pathlib import Path

import pytest

from knowledge_bridge.freezer_export import export_freezer_draft


def _write_record(root: Path, knowledge_id: str, *, metadata: dict, sensitivity: str = "internal") -> None:
    normalized = root / "normalized"
    normalized.mkdir(parents=True, exist_ok=True)
    record = {
        "knowledge_id": knowledge_id,
        "capture_id": "KBC-TEST-V0001",
        "source_path": "decision.md",
        "source_hash": "a" * 64,
        "title": "保存方式",
        "knowledge_type": "decision",
        "status": "challenged",
        "project_id": "TEST",
        "tags": ["storage"],
        "confidence": 1.0,
        "sensitivity": sensitivity,
        "sensitivity_reasons": [],
        "public_export_allowed": False,
        "frontmatter": metadata,
        "body": "データは端末内だけに保存する。正式な保存方式の決定である。",
        "source_excerpt": "データは端末内だけに保存する。",
    }
    (normalized / f"{knowledge_id}.json").write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")


def _metadata() -> dict:
    return {
        "purpose": "保存方式を一意に決める",
        "constraints": ["read-only source"],
        "acceptance_criteria": ["保存先が一意に決まる"],
        "test_plan": ["fixture test"],
        "rollback": "disable bridge",
        "alternatives": ["cloud storage"],
        "original_problem": "保存先が決まっておらず実装が分岐する",
        "why_it_matters": "データ消失と二重実装を防ぐ",
        "trigger_conditions": ["保存方式を実装する前"],
        "negative_triggers": ["個人情報を含む場合"],
        "dependencies": ["Knowledge Bridge Phase 4"],
        "estimated_hours": {"minimum": 1, "maximum": 3},
        "human_review": "required",
    }


def test_valid_draft_is_not_approved_and_does_not_mutate_freezer(tmp_path: Path) -> None:
    _write_record(tmp_path, "KBR-A", metadata=_metadata())
    output = tmp_path / "draft.json"
    result = export_freezer_draft(tmp_path, "KBR-A", output)
    item = json.loads(output.read_text(encoding="utf-8"))
    review = json.loads(Path(result.review_path).read_text(encoding="utf-8"))

    assert item["build_authority"] == "NOT_APPROVED"
    assert item["status"] == "CAPTURED"
    assert item["item_id"].startswith("RTS-FRZ-")
    assert item["source_refs"]
    assert review["automatic_freezer_add_invoked"] is False
    assert review["automatic_approval_possible"] is False
    assert not (tmp_path / "freezer").exists()


def test_export_rejects_missing_governance_metadata(tmp_path: Path) -> None:
    metadata = _metadata()
    del metadata["negative_triggers"]
    _write_record(tmp_path, "KBR-A", metadata=metadata)
    with pytest.raises(ValueError, match="negative_triggers"):
        export_freezer_draft(tmp_path, "KBR-A", tmp_path / "draft.json")


def test_export_rejects_sensitive_record(tmp_path: Path) -> None:
    _write_record(tmp_path, "KBR-A", metadata=_metadata(), sensitivity="personal")
    with pytest.raises(PermissionError):
        export_freezer_draft(tmp_path, "KBR-A", tmp_path / "draft.json")


def test_export_refuses_overwrite(tmp_path: Path) -> None:
    _write_record(tmp_path, "KBR-A", metadata=_metadata())
    output = tmp_path / "draft.json"
    export_freezer_draft(tmp_path, "KBR-A", output)
    with pytest.raises(FileExistsError):
        export_freezer_draft(tmp_path, "KBR-A", output)

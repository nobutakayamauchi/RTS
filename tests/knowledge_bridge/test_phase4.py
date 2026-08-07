from __future__ import annotations

import json
from pathlib import Path

from knowledge_bridge.recall import recall_event
from knowledge_bridge.route import route_record


def _write(root: Path, knowledge_id: str, *, kind: str, status: str = "captured", project: str | None = "P1", sensitivity: str = "internal", confidence: float = 1.0) -> None:
    folder = root / "normalized"
    folder.mkdir(parents=True, exist_ok=True)
    record = {
        "knowledge_id": knowledge_id,
        "capture_id": "CAP-" + knowledge_id,
        "source_path": knowledge_id + ".md",
        "source_hash": (knowledge_id.lower() * 64)[:64],
        "title": knowledge_id,
        "knowledge_type": kind,
        "status": status,
        "project_id": project,
        "tags": [],
        "confidence": confidence,
        "sensitivity": sensitivity,
        "sensitivity_reasons": [],
        "public_export_allowed": False,
        "frontmatter": {},
        "body": knowledge_id,
        "source_excerpt": knowledge_id,
    }
    (folder / f"{knowledge_id}.json").write_text(json.dumps(record), encoding="utf-8")


def test_test_knowledge_routes_to_test(tmp_path: Path) -> None:
    _write(tmp_path, "KBR-T", kind="test")
    result = route_record(tmp_path, "KBR-T")
    assert result.destination == "test"


def test_promotion_ready_spec_routes_to_freezer(tmp_path: Path) -> None:
    _write(tmp_path, "KBR-S", kind="spec", status="challenged")
    folder = tmp_path / "challenges"
    folder.mkdir()
    (folder / "KBR-S.json").write_text(json.dumps({"promotion_ready": True}), encoding="utf-8")
    result = route_record(tmp_path, "KBR-S")
    assert result.destination == "freezer"
    assert "challenge:promotion_ready" in result.reasons


def test_sensitive_record_routes_to_archive(tmp_path: Path) -> None:
    _write(tmp_path, "KBR-P", kind="decision", sensitivity="personal")
    assert route_record(tmp_path, "KBR-P").destination == "archive"


def test_bug_recall_returns_explained_project_matches(tmp_path: Path) -> None:
    _write(tmp_path, "KBR-BUG", kind="problem", status="challenged", project="P1")
    _write(tmp_path, "KBR-OTHER", kind="pattern", project="P2")
    results = recall_event(tmp_path, "BUG_REPORTED", project_id="P1")
    assert results
    assert results[0].knowledge_id == "KBR-BUG"
    assert "same_project" in results[0].reasons
    assert any(reason.startswith("event_type_match") for reason in results[0].reasons)


def test_recall_can_stay_silent(tmp_path: Path) -> None:
    _write(tmp_path, "KBR-X", kind="archive", confidence=0.1)
    assert recall_event(tmp_path, "RELEASE_GATE", project_id="NOPE", threshold=0.8) == ()


def test_sensitive_records_are_not_recalled(tmp_path: Path) -> None:
    _write(tmp_path, "KBR-PRIVATE", kind="problem", sensitivity="restricted")
    assert recall_event(tmp_path, "BUG_REPORTED", project_id="P1") == ()

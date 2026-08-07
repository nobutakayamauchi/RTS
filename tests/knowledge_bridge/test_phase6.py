from __future__ import annotations

import json
from pathlib import Path

import pytest

from knowledge_bridge.council import analyze_implementation_council


def _state(root: Path, *, promotion_ready: bool = True, metadata: dict | None = None) -> None:
    normalized = root / "normalized"
    challenges = root / "challenges"
    normalized.mkdir(parents=True)
    challenges.mkdir(parents=True)
    record = {
        "knowledge_id": "KBR-A",
        "title": "保存方式",
        "body": "データ保存方式を実装する",
        "tags": ["storage"],
        "frontmatter": metadata or {
            "rollback": "disable",
            "test_plan": ["fixture"],
            "acceptance_criteria": ["deterministic"],
            "dependencies": ["Phase 5"],
        },
    }
    (normalized / "KBR-A.json").write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")
    (challenges / "KBR-A.json").write_text(json.dumps({"promotion_ready": promotion_ready}), encoding="utf-8")


def _repo(root: Path) -> None:
    (root / "knowledge_bridge").mkdir(parents=True)
    (root / "knowledge_bridge" / "storage.py").write_text("def save_storage_record():\n    pass\n", encoding="utf-8")
    (root / "tests" / "knowledge_bridge").mkdir(parents=True)
    (root / "tests" / "knowledge_bridge" / "test_storage.py").write_text("def test_storage_record():\n    pass\n", encoding="utf-8")
    (root / "docs").mkdir(parents=True)
    (root / "docs" / "storage.md").write_text("# Storage design\n", encoding="utf-8")
    (root / "freezer" / "items").mkdir(parents=True)
    item = {"item_id": "RTS-FRZ-000001", "title": "storage foundation", "tags": ["storage"]}
    (root / "freezer" / "items" / "one.json").write_text(json.dumps(item), encoding="utf-8")


def test_council_stops_before_human_decision(tmp_path: Path) -> None:
    state = tmp_path / "state"
    repo = tmp_path / "repo"
    _state(state)
    _repo(repo)
    report = analyze_implementation_council(state, "KBR-A", repo, tmp_path / "report.json")
    assert report.status == "AWAITING_HUMAN_DECISION"
    assert report.human_decision_required is True
    assert report.recommendation == "BUNDLE_WITH_OTHER_ITEMS"
    assert report.insertion_candidates
    assert "storage.py" in report.insertion_candidates[0]
    assert "role=implementation" in report.insertion_candidates[0]
    assert report.test_candidates
    assert "test_storage.py" in report.test_candidates[0]
    assert report.reference_candidates
    assert "storage.md" in report.reference_candidates[0]
    assert (tmp_path / "report.md").exists()


def test_missing_blocking_foundation_changes_recommendation(tmp_path: Path) -> None:
    state = tmp_path / "state"
    repo = tmp_path / "repo"
    _state(state, metadata={"dependencies": []})
    _repo(repo)
    report = analyze_implementation_council(state, "KBR-A", repo, tmp_path / "report.json")
    assert report.recommendation == "APPROVE_AFTER_FOUNDATION"
    assert {item.name for item in report.missing_parts if item.category == "blocking"} >= {"rollback", "test_plan", "acceptance_criteria"}


def test_council_requires_promotion_ready(tmp_path: Path) -> None:
    state = tmp_path / "state"
    repo = tmp_path / "repo"
    _state(state, promotion_ready=False)
    _repo(repo)
    with pytest.raises(PermissionError):
        analyze_implementation_council(state, "KBR-A", repo, tmp_path / "report.json")


def test_council_refuses_overwrite(tmp_path: Path) -> None:
    state = tmp_path / "state"
    repo = tmp_path / "repo"
    _state(state)
    _repo(repo)
    output = tmp_path / "report.json"
    analyze_implementation_council(state, "KBR-A", repo, output)
    with pytest.raises(FileExistsError):
        analyze_implementation_council(state, "KBR-A", repo, output)


def test_council_finds_candidate_from_source_content_not_filename(tmp_path: Path) -> None:
    state = tmp_path / "state"
    repo = tmp_path / "repo"
    _state(state)
    (repo / "core").mkdir(parents=True)
    (repo / "core" / "engine.py").write_text("def storage_adapter():\n    return 'data storage'\n", encoding="utf-8")
    report = analyze_implementation_council(state, "KBR-A", repo, tmp_path / "report.json")
    assert report.insertion_candidates
    assert any("core/engine.py" in item for item in report.insertion_candidates)


def test_council_treats_missing_insertion_boundary_as_blocking(tmp_path: Path) -> None:
    state = tmp_path / "state"
    repo = tmp_path / "repo"
    _state(state)
    (repo / "unrelated").mkdir(parents=True)
    (repo / "unrelated" / "clock.py").write_text("def current_time():\n    return 0\n", encoding="utf-8")
    report = analyze_implementation_council(state, "KBR-A", repo, tmp_path / "report.json")
    assert report.recommendation == "APPROVE_AFTER_FOUNDATION"
    assert any(item.name == "insertion_boundary" and item.category == "blocking" for item in report.missing_parts)


def test_reference_only_match_cannot_authorize_implementation(tmp_path: Path) -> None:
    state = tmp_path / "state"
    repo = tmp_path / "repo"
    _state(state)
    (repo / "docs").mkdir(parents=True)
    (repo / "docs" / "storage.md").write_text("# Storage implementation design\n", encoding="utf-8")
    report = analyze_implementation_council(state, "KBR-A", repo, tmp_path / "report.json")
    assert not report.insertion_candidates
    assert report.reference_candidates
    assert report.recommendation == "APPROVE_AFTER_FOUNDATION"
    assert any(item.name == "insertion_boundary" for item in report.missing_parts)


def test_candidate_reports_responsibility_and_side_effect(tmp_path: Path) -> None:
    state = tmp_path / "state"
    repo = tmp_path / "repo"
    _state(state)
    (repo / "core").mkdir(parents=True)
    (repo / "core" / "storage_state.py").write_text("def save_storage():\n    pass\n", encoding="utf-8")
    report = analyze_implementation_council(state, "KBR-A", repo, tmp_path / "report.json")
    candidate = next(item for item in report.insertion_candidates if "storage_state.py" in item)
    assert "responsibility=state persistence responsibility" in candidate
    assert "side_effect=migration, durability, and rollback risk" in candidate

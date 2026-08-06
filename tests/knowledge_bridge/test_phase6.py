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
    (root / "knowledge_bridge" / "storage.py").write_text("# storage", encoding="utf-8")
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

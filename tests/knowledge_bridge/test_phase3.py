from __future__ import annotations

import json
from pathlib import Path

from knowledge_bridge.challenge import challenge_record
from knowledge_bridge.connect import connect_record
from knowledge_bridge.normalize import normalize_capture


def _write_record(root: Path, knowledge_id: str, *, body: str, kind: str = "decision", project: str | None = "P1", tags: list[str] | None = None, status: str = "captured", sensitivity: str = "internal", confidence: float = 1.0, frontmatter: dict | None = None) -> None:
    folder = root / "normalized"
    folder.mkdir(parents=True, exist_ok=True)
    record = {
        "knowledge_id": knowledge_id,
        "capture_id": "CAP-" + knowledge_id,
        "source_path": knowledge_id + ".md",
        "source_hash": (knowledge_id.lower() * 64)[:64],
        "title": body.split("。", 1)[0],
        "knowledge_type": kind,
        "status": status,
        "project_id": project,
        "tags": tags or [],
        "confidence": confidence,
        "sensitivity": sensitivity,
        "sensitivity_reasons": [],
        "public_export_allowed": False,
        "frontmatter": frontmatter or {},
        "body": body,
        "source_excerpt": body[:500],
    }
    (folder / f"{knowledge_id}.json").write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")


def test_connections_explain_shared_project_and_tags(tmp_path: Path) -> None:
    _write_record(tmp_path, "KBR-A", body="UIの保存方式を決定する。", tags=["ui", "save"])
    _write_record(tmp_path, "KBR-B", body="UI保存の回帰テストを作る。", kind="test", tags=["ui"])
    results = connect_record(tmp_path, "KBR-A")
    assert results
    assert results[0].other_knowledge_id == "KBR-B"
    assert "same_project" in results[0].reasons
    assert any(reason.startswith("shared_tags") for reason in results[0].reasons)


def test_possible_contradiction_remains_visible(tmp_path: Path) -> None:
    _write_record(tmp_path, "KBR-A", body="データは端末内だけに保存する。")
    _write_record(tmp_path, "KBR-B", body="データはクラウドだけに保存する。")
    results = connect_record(tmp_path, "KBR-A")
    assert any(item.relation == "possible_contradiction" for item in results)


def test_challenge_blocks_flat_spec_without_completion_evidence(tmp_path: Path) -> None:
    _write_record(tmp_path, "KBR-A", body="新しい同期機能を作る。", kind="spec")
    result = challenge_record(tmp_path, "KBR-A")
    assert result.promotion_ready is False
    unresolved = {item.code for item in result.findings if not item.resolved}
    assert "ACCEPTANCE_MISSING" in unresolved
    assert "TEST_MISSING" in unresolved
    assert "AUTHORITY_UNCLEAR" in unresolved


def test_challenged_record_can_pass_when_high_risk_fields_are_present(tmp_path: Path) -> None:
    frontmatter = {
        "purpose": "端末間で仕様を同期する",
        "constraints": ["read-only source"],
        "acceptance_criteria": ["same input yields same output"],
        "test_plan": ["fixture test"],
        "rollback": "disable bridge",
        "alternatives": ["manual copy"],
    }
    _write_record(tmp_path, "KBR-A", body="同期仕様を実装可能な単位に限定するための正式候補です。", kind="spec", status="challenged", frontmatter=frontmatter)
    result = challenge_record(tmp_path, "KBR-A")
    assert result.promotion_ready is True


def test_sensitive_record_never_becomes_promotion_ready(tmp_path: Path) -> None:
    frontmatter = {
        "purpose": "個人情報を整理する",
        "constraints": ["private"],
        "acceptance_criteria": ["reviewed"],
        "test_plan": ["manual"],
        "rollback": "delete derivative",
        "alternatives": ["none"],
    }
    _write_record(tmp_path, "KBR-A", body="労働問題と病院の情報", status="challenged", sensitivity="personal", frontmatter=frontmatter)
    result = challenge_record(tmp_path, "KBR-A")
    assert result.promotion_ready is False
    assert any(item.code == "SENSITIVITY_BLOCK" and not item.resolved for item in result.findings)

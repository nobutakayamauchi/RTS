from __future__ import annotations

import json
from pathlib import Path

import pytest

from knowledge_bridge.design_e2e import run_design_e2e


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def _input(path: Path) -> None:
    _write_json(
        path,
        {
            "schema_version": "1.0",
            "request_id": "REQ-MUSIC-001",
            "project_id": "PRJ-MUSIC",
            "title": "Beginner mobile music player",
            "domain": "music player",
            "role": "listener",
            "target_user": "beginner smartphone user",
            "feedback": [
                "The current screen is too complex.",
                "I want one-tap access to playlists.",
                "Unlabeled controls are confusing.",
            ],
            "features": [
                {"feature": "playback controls", "decision": "KEEP", "reason": "Primary action."},
                {"feature": "equalizer", "decision": "DEFER", "reason": "Not required for first use."},
            ],
            "references": [
                {
                    "reference_id": "REF-A",
                    "reaction": "like",
                    "adopted": ["bottom playback controls"],
                    "rejected": ["dense settings"],
                }
            ],
            "constraints": ["mobile first", "human review required"],
            "unresolved_questions": ["Which playlist destination needs one-tap access?"],
        },
    )


def test_design_e2e_connects_translation_and_council(tmp_path: Path) -> None:
    source = tmp_path / "input.json"
    _input(source)
    repo = tmp_path / "repo"
    (repo / "player").mkdir(parents=True)
    (repo / "player" / "playlist_view.py").write_text(
        "def open_playlist():\n    return 'playlist'\n", encoding="utf-8"
    )
    (repo / "tests").mkdir()
    (repo / "tests" / "test_playlist_view.py").write_text(
        "def test_playlist():\n    assert True\n", encoding="utf-8"
    )
    _write_json(
        repo / "freezer" / "items" / "item.json",
        {"item_id": "RTS-FRZ-MUSIC", "title": "playlist navigation", "status": "frozen"},
    )

    result = run_design_e2e(source, repo, tmp_path / "bundle")

    assert result.request_id == "REQ-MUSIC-001"
    assert result.project_id == "PRJ-MUSIC"
    assert result.status == "AWAITING_HUMAN_DECISION"
    assert result.human_decision_required is True
    summary = json.loads((tmp_path / "bundle" / "summary.json").read_text(encoding="utf-8"))
    assert summary["implementation_executed"] is False
    assert summary["status"] == "AWAITING_HUMAN_DECISION"
    assert (tmp_path / "bundle" / "translation.md").exists()
    assert (tmp_path / "bundle" / "council.md").exists()
    assert (tmp_path / "bundle" / "summary.md").exists()
    assert not (tmp_path / "bundle" / ".state").exists()


def test_design_e2e_refuses_overwrite_and_cleans_failed_bundle(tmp_path: Path) -> None:
    source = tmp_path / "input.json"
    _input(source)
    repo = tmp_path / "repo"
    repo.mkdir()
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    with pytest.raises(FileExistsError):
        run_design_e2e(source, repo, bundle)

    broken = tmp_path / "broken.json"
    broken.write_text("not-json", encoding="utf-8")
    failed_bundle = tmp_path / "failed"
    with pytest.raises(json.JSONDecodeError):
        run_design_e2e(broken, repo, failed_bundle)
    assert not failed_bundle.exists()

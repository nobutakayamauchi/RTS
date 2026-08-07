from __future__ import annotations

import json
from pathlib import Path

import pytest

from knowledge_bridge.obsidian_adapter import note_to_translation_input, run_obsidian_design


def _repo(path: Path) -> Path:
    repo = path / "repo"
    repo.mkdir()
    (repo / "player.py").write_text(
        "def open_playlist():\n    return 'playlist'\n\ndef render_player():\n    return 'player'\n",
        encoding="utf-8",
    )
    (repo / "test_player.py").write_text("def test_player():\n    assert True\n", encoding="utf-8")
    return repo


def test_note_sections_become_translation_input(tmp_path: Path) -> None:
    note = tmp_path / "player.md"
    note.write_text(
        "---\n"
        "rts_design: true\n"
        "title: Mobile player\n"
        "domain: music\n"
        "role: listener\n"
        "target_user: beginner smartphone user\n"
        "---\n\n"
        "# 要望\n\n"
        "- 複雑すぎる\n"
        "- プレイリストへ一発で行きたい\n\n"
        "# 制約\n\n"
        "- スマホ片手操作\n",
        encoding="utf-8",
    )
    payload = note_to_translation_input(note)
    assert payload["title"] == "Mobile player"
    assert payload["feedback"] == ["複雑すぎる", "プレイリストへ一発で行きたい"]
    assert payload["constraints"] == ["スマホ片手操作"]
    assert payload["source"] == {"type": "obsidian", "path": "player.md"}


def test_adapter_returns_review_to_vault_without_implementation(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    note = vault / "player.md"
    note.write_text(
        "---\n"
        "rts_design: true\n"
        "request_id: REQ-OBS-1\n"
        "project_id: PRJ-OBS-1\n"
        "title: Mobile player\n"
        "domain: music\n"
        "target_user: beginner smartphone user\n"
        "---\n\n"
        "# Feedback\n\n"
        "- This is too complex\n"
        "- I want one-tap access to playlists\n",
        encoding="utf-8",
    )
    result = run_obsidian_design(vault, "player.md", _repo(tmp_path))
    review = Path(result.review_note)
    machine = Path(result.machine_record)
    bundle = Path(result.bundle_path)
    assert result.status == "AWAITING_HUMAN_DECISION"
    assert review.exists() and machine.exists() and bundle.is_dir()
    text = review.read_text(encoding="utf-8")
    assert "[[player.md]]" in text
    assert "No approval, code modification, or implementation was executed." in text
    record = json.loads(machine.read_text(encoding="utf-8"))
    assert record["source_note"] == "player.md"
    assert (bundle / "summary.json").exists()


def test_adapter_requires_opt_in_and_refuses_overwrite(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    note = vault / "plain.md"
    note.write_text("# Idea\nMake a player", encoding="utf-8")
    with pytest.raises(PermissionError):
        run_obsidian_design(vault, "plain.md", _repo(tmp_path))

    note.write_text(
        "---\nrts_design: true\nrequest_id: REQ-SAME\nproject_id: PRJ-SAME\n---\n\n# Goals\n- Make a player\n",
        encoding="utf-8",
    )
    repo = tmp_path / "repo"
    run_obsidian_design(vault, "plain.md", repo)
    with pytest.raises(FileExistsError):
        run_obsidian_design(vault, "plain.md", repo)

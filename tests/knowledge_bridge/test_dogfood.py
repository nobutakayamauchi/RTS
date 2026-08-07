from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import knowledge_bridge.dogfood as dogfood


def _write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def test_starts_one_run_across_three_surfaces(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source_bundle = tmp_path / "source.bundle"
    _write(source_bundle / "translation.json", {
        "request_id": "REQ-1",
        "project_id": "PRJ-1",
        "planned_structure": {"nodes": [
            {"id": "REQ-1:feature:1", "type": "feature", "label": "Player"},
            {"id": "REQ-1:missing:1", "type": "missing_part", "label": "Shortcut"},
            {"id": "REQ-1:approval", "type": "approval", "label": "Approval"},
        ]},
    })
    _write(source_bundle / "summary.json", {"request_id": "REQ-1", "project_id": "PRJ-1"})

    monkeypatch.setattr(dogfood, "run_obsidian_design", lambda *args, **kwargs: SimpleNamespace(
        bundle_path=str(source_bundle), source_note="player.md", request_id="REQ-1", project_id="PRJ-1"
    ))

    def fake_common_ui(bundle: Path, output: Path) -> None:
        output.write_text("{}", encoding="utf-8")
        output.with_suffix(".html").write_text("<html></html>", encoding="utf-8")

    monkeypatch.setattr(dogfood, "build_common_view_model", fake_common_ui)

    result = dogfood.start_dogfood(tmp_path / "vault", "player.md", tmp_path / "repo", tmp_path / "run")
    assert result.status == "AWAITING_REAL_OBSERVATIONS"
    assert result.planned_count == 2
    observations = json.loads((tmp_path / "run" / "observations.json").read_text())
    assert observations["request_id"] == "REQ-1"
    assert observations["project_id"] == "PRJ-1"
    assert observations["observations"] == []
    assert len(observations["planned_nodes"]) == 2
    manifest = json.loads((tmp_path / "run" / "manifest.json").read_text())
    assert manifest["implementation_executed"] is False
    assert (tmp_path / "run" / "common-ui.html").exists()


def test_refuses_to_overwrite_dogfood_run(tmp_path: Path) -> None:
    output = tmp_path / "run"
    output.mkdir()
    with pytest.raises(FileExistsError):
        dogfood.start_dogfood(tmp_path / "vault", "player.md", tmp_path / "repo", output)

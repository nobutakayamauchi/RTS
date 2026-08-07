from __future__ import annotations

import json
from pathlib import Path

import pytest

from knowledge_bridge.debug_link import link_debug_observations


def _write(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


def _bundle(tmp_path: Path) -> Path:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    _write(bundle / "translation.json", {
        "request_id": "REQ-1", "project_id": "PRJ-1", "title": "Player",
        "planned_structure": {"nodes": [
            {"id": "REQ-1:feature:1", "type": "feature", "label": "Play"},
            {"id": "REQ-1:feature:2", "type": "feature", "label": "Playlist"},
            {"id": "REQ-1:missing:1", "type": "missing_part", "label": "Shortcut decision"},
            {"id": "REQ-1:approval", "type": "approval", "label": "Approval"},
        ], "edges": []},
    })
    _write(bundle / "summary.json", {"request_id": "REQ-1", "project_id": "PRJ-1", "status": "AWAITING_HUMAN_DECISION", "implementation_executed": False})
    return bundle


def test_links_planned_built_broken_stale_and_unobserved(tmp_path: Path) -> None:
    bundle = _bundle(tmp_path)
    observations = tmp_path / "observations.json"
    _write(observations, {"request_id": "REQ-1", "project_id": "PRJ-1", "observations": [
        {"node_id": "REQ-1:feature:1", "status": "AS_BUILT", "artifact": "player.html"},
        {"node_id": "REQ-1:feature:2", "status": "BROKEN", "artifact": "playlist.js", "details": "tap fails"},
        {"node_id": "REQ-1:feature:2", "status": "STALE", "artifact": "legacy.html"},
        {"node_id": "UNKNOWN", "status": "STALE", "artifact": "orphan.html"},
    ]})
    result = link_debug_observations(bundle, observations, tmp_path / "lifecycle.json")
    assert result.planned_count == 3
    assert result.as_built_count == 1
    assert result.broken_count == 1
    assert result.stale_count == 0
    assert result.unobserved_count == 1
    data = json.loads((tmp_path / "lifecycle.json").read_text())
    assert data["counts"]["orphan"] == 1
    assert (tmp_path / "lifecycle.html").exists()
    assert data["approval"]["implementation_executed"] is False


def test_rejects_identity_mismatch_and_invalid_status(tmp_path: Path) -> None:
    bundle = _bundle(tmp_path)
    mismatch = tmp_path / "mismatch.json"
    _write(mismatch, {"request_id": "REQ-X", "project_id": "PRJ-1", "observations": []})
    with pytest.raises(ValueError, match="request_id"):
        link_debug_observations(bundle, mismatch, tmp_path / "out.json")

    bad = tmp_path / "bad.json"
    _write(bad, {"request_id": "REQ-1", "project_id": "PRJ-1", "observations": [{"node_id": "REQ-1:feature:1", "status": "FIXED"}]})
    with pytest.raises(ValueError, match="unsupported"):
        link_debug_observations(bundle, bad, tmp_path / "bad-out.json")


def test_refuses_overwrite(tmp_path: Path) -> None:
    bundle = _bundle(tmp_path)
    observations = tmp_path / "observations.json"
    _write(observations, {"request_id": "REQ-1", "project_id": "PRJ-1", "observations": []})
    output = tmp_path / "lifecycle.json"
    link_debug_observations(bundle, observations, output)
    with pytest.raises(FileExistsError):
        link_debug_observations(bundle, observations, output)

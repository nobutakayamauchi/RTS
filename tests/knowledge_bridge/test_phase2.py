from __future__ import annotations

from pathlib import Path

import pytest

from knowledge_bridge.capture_store import CaptureStore
from knowledge_bridge.config import BridgeConfig
from knowledge_bridge.intake import iter_notes
from knowledge_bridge.normalize import normalize_capture, parse_frontmatter
from knowledge_bridge.sensitivity import assert_public_export_allowed, assess_sensitivity


def _capture(tmp_path: Path, content: str, path: str = "notes/item.md"):
    vault = tmp_path / "vault"
    state = tmp_path / "state"
    target = vault / path
    target.parent.mkdir(parents=True)
    target.write_text(content, encoding="utf-8")
    config = BridgeConfig(vault_path=vault, state_path=state)
    record, _ = CaptureStore(state).capture(list(iter_notes(config))[0])
    return target, state, record


def test_frontmatter_and_explicit_type_are_preserved(tmp_path: Path) -> None:
    source, state, capture = _capture(
        tmp_path,
        "---\ntitle: UI release gate\nknowledge_type: test\nstatus: approved\ntags: [ui, release]\npublic: true\n---\n# ignored title\nAcceptance criteria here.\n",
    )
    before = source.read_bytes()
    result = normalize_capture(state, capture.capture_id)
    assert result.title == "UI release gate"
    assert result.knowledge_type == "test"
    assert result.status == "approved"
    assert result.tags == ("ui", "release")
    assert result.public_export_allowed is True
    assert source.read_bytes() == before


def test_folder_is_hint_not_authority(tmp_path: Path) -> None:
    _, state, capture = _capture(tmp_path, "# Decision\n採用を決定する。\n", "specs/decision.md")
    result = normalize_capture(state, capture.capture_id)
    assert result.knowledge_type == "decision"
    assert result.confidence < 1.0


def test_malformed_frontmatter_preserves_raw_capture(tmp_path: Path) -> None:
    text = "---\nthis is malformed\n---\n# note\nbody\n"
    source, state, capture = _capture(tmp_path, text)
    result = normalize_capture(state, capture.capture_id)
    assert result.confidence <= 0.3
    assert (state / capture.content_file).read_text(encoding="utf-8") == text
    assert source.read_text(encoding="utf-8") == text


def test_secrets_are_restricted_and_public_export_is_blocked() -> None:
    result = assess_sensitivity("api_key = abcdefghijklmnop")
    assert result.level == "restricted"
    assert result.public_export_allowed is False
    with pytest.raises(PermissionError):
        assert_public_export_allowed(result)


def test_personal_categories_are_not_public_by_default() -> None:
    result = assess_sensitivity("労働問題と病院での症状についての個人メモ")
    assert result.level == "personal"
    assert result.public_export_allowed is False


def test_normalization_is_immutable_for_same_capture(tmp_path: Path) -> None:
    _, state, capture = _capture(tmp_path, "# Spec\n仕様を作る。\n")
    first = normalize_capture(state, capture.capture_id)
    output = state / "normalized" / f"{first.knowledge_id}.json"
    before = output.read_bytes()
    second = normalize_capture(state, capture.capture_id)
    assert first == second
    assert output.read_bytes() == before


def test_parse_frontmatter_without_header() -> None:
    metadata, body, valid = parse_frontmatter("# plain\n")
    assert metadata == {}
    assert body == "# plain\n"
    assert valid is True

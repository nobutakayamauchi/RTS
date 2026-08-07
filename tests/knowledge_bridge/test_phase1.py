from __future__ import annotations

from pathlib import Path

from knowledge_bridge.capture_store import CaptureStore
from knowledge_bridge.config import BridgeConfig
from knowledge_bridge.intake import iter_notes


def test_scan_is_idempotent_and_preserves_source(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    state = tmp_path / "state"
    vault.mkdir()
    note = vault / "note.md"
    original = b"# note\nhello\n"
    note.write_bytes(original)

    config = BridgeConfig(vault_path=vault, state_path=state)
    store = CaptureStore(state)

    first = list(iter_notes(config))[0]
    record1, created1 = store.capture(first)
    record2, created2 = store.capture(first)

    assert created1 is True
    assert created2 is False
    assert record1.capture_id == record2.capture_id
    assert note.read_bytes() == original


def test_changed_note_creates_new_immutable_version(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    state = tmp_path / "state"
    vault.mkdir()
    note = vault / "note.md"
    note.write_text("v1", encoding="utf-8")

    config = BridgeConfig(vault_path=vault, state_path=state)
    store = CaptureStore(state)
    first, _ = store.capture(list(iter_notes(config))[0])

    note.write_text("v2", encoding="utf-8")
    second, created = store.capture(list(iter_notes(config))[0])

    assert created is True
    assert first.capture_id != second.capture_id
    assert (state / first.content_file).read_text(encoding="utf-8") == "v1"
    assert (state / second.content_file).read_text(encoding="utf-8") == "v2"
    assert store.verify() == []


def test_missing_vault_fails_safely(tmp_path: Path) -> None:
    config = BridgeConfig(vault_path=tmp_path / "missing", state_path=tmp_path / "state")
    try:
        list(iter_notes(config))
    except FileNotFoundError:
        pass
    else:
        raise AssertionError("missing vault must fail")
    assert not config.state_path.exists()

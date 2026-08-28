#!/usr/bin/env python3

import importlib.util
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("collect_history", HERE / "collect_history.py")
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        codex_home = root / ".codex"
        sessions = codex_home / "sessions" / "2026" / "08" / "28"

        high_path = sessions / "high.jsonl"
        write_jsonl(
            high_path,
            [
                {
                    "type": "session_meta",
                    "timestamp": "2026-08-28T00:00:00Z",
                    "payload": {
                        "session_id": "S-HIGH",
                        "model": "gpt-test",
                        "cwd": "/repo",
                        "provider": "openai",
                    },
                },
                {
                    "type": "user_message",
                    "message": {"role": "user", "content": "Inspect the bounded surface."},
                },
                {
                    "type": "turn.completed",
                    "timestamp": "2026-08-28T00:01:00Z",
                    "usage": {
                        "input_tokens": 100,
                        "cached_input_tokens": 20,
                        "output_tokens": 10,
                        "reasoning_output_tokens": 4,
                    },
                },
                {
                    "type": "turn_completed",
                    "timestamp": "2026-08-28T00:02:00Z",
                    "usage": {
                        "input_tokens": 200,
                        "cached_input_tokens": 50,
                        "output_tokens": 20,
                        "reasoning_output_tokens": 8,
                    },
                },
            ],
        )

        low_path = sessions / "low.jsonl"
        write_jsonl(
            low_path,
            [
                {"type": "usage_snapshot", "usage": {"input_tokens": 1000, "output_tokens": 100}},
                {"type": "usage_snapshot", "usage": {"input_tokens": 1500, "output_tokens": 150}},
            ],
        )

        (codex_home / "auth.json").write_text('{"secret":"do-not-copy"}', encoding="utf-8")
        (codex_home / "history.jsonl").write_text("{}\n", encoding="utf-8")

        high = mod.parse_session(high_path, include_preview=False)
        assert high.usage_method == "SUM_TURN_COMPLETED", high
        assert high.usage_confidence == "HIGH", high
        assert high.input_tokens == 300, high
        assert high.cached_input_tokens == 70, high
        assert high.output_tokens == 30, high
        assert high.reasoning_output_tokens == 12, high
        assert high.task_sha256 is not None, high
        assert high.task_chars == len("Inspect the bounded surface."), high
        assert high.task_preview is None, high

        high_preview = mod.parse_session(high_path, include_preview=True)
        assert high_preview.task_preview == "Inspect the bounded surface.", high_preview

        low = mod.parse_session(low_path, include_preview=False)
        assert low.usage_method == "FINAL_GENERIC_USAGE_SNAPSHOT", low
        assert low.usage_confidence == "LOW", low
        assert low.input_tokens == 1500, low
        assert low.output_tokens == 150, low

        inventory = mod.inventory_codex_files(codex_home)
        paths = {row["path"] for row in inventory}
        assert "auth.json" not in paths, paths
        assert "history.jsonl" in paths, paths
        assert any(path.endswith("high.jsonl") for path in paths), paths

        discovered = mod.discover_sessions(codex_home)
        assert discovered == sorted([high_path, low_path]), discovered

    print("Codex history collector semantics valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

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


def token_count(total: dict, last: dict, timestamp: str) -> dict:
    return {
        "timestamp": timestamp,
        "type": "event_msg",
        "payload": {
            "type": "token_count",
            "info": {
                "total_token_usage": total,
                "last_token_usage": last,
                "model_context_window": 258400,
            },
        },
    }


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        codex_home = root / ".codex"
        sessions = codex_home / "sessions" / "2026" / "08" / "28"

        token_path = sessions / "token-count.jsonl"
        write_jsonl(
            token_path,
            [
                {
                    "type": "session_meta",
                    "timestamp": "2026-08-28T00:00:00Z",
                    "payload": {
                        "session_id": "S-TOKEN",
                        "model": "gpt-test",
                        "cwd": "/repo",
                        "provider": "openai",
                    },
                },
                {
                    "type": "user_message",
                    "message": {"role": "user", "content": "Inspect the bounded surface."},
                },
                token_count(
                    {
                        "input_tokens": 1000,
                        "cached_input_tokens": 800,
                        "cache_write_input_tokens": 0,
                        "output_tokens": 20,
                        "reasoning_output_tokens": 5,
                        "total_tokens": 1025,
                    },
                    {
                        "input_tokens": 1000,
                        "cached_input_tokens": 800,
                        "cache_write_input_tokens": 0,
                        "output_tokens": 20,
                        "reasoning_output_tokens": 5,
                        "total_tokens": 1025,
                    },
                    "2026-08-28T00:01:00Z",
                ),
                token_count(
                    {
                        "input_tokens": 1500,
                        "cached_input_tokens": 1200,
                        "cache_write_input_tokens": 0,
                        "output_tokens": 30,
                        "reasoning_output_tokens": 8,
                        "total_tokens": 1538,
                    },
                    {
                        "input_tokens": 500,
                        "cached_input_tokens": 400,
                        "cache_write_input_tokens": 0,
                        "output_tokens": 10,
                        "reasoning_output_tokens": 3,
                        "total_tokens": 513,
                    },
                    "2026-08-28T00:02:00Z",
                ),
            ],
        )

        turn_path = sessions / "turn-completed.jsonl"
        write_jsonl(
            turn_path,
            [
                {"type": "turn.completed", "usage": {"input_tokens": 100, "cached_input_tokens": 20, "output_tokens": 10, "reasoning_output_tokens": 4}},
                {"type": "turn_completed", "usage": {"input_tokens": 200, "cached_input_tokens": 50, "output_tokens": 20, "reasoning_output_tokens": 8}},
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

        token = mod.parse_session(token_path, include_preview=False)
        assert token.usage_method == "FINAL_TOKEN_COUNT_TOTAL", token
        assert token.usage_confidence == "HIGH", token
        assert token.token_count_events == 2, token
        assert token.token_count_delta_verified is True, token
        assert token.input_tokens == 1500, token
        assert token.cached_input_tokens == 1200, token
        assert token.output_tokens == 30, token
        assert token.reasoning_output_tokens == 8, token
        assert token.last_input_tokens == 500, token
        assert token.last_cached_input_tokens == 400, token
        assert token.last_output_tokens == 10, token
        assert token.last_reasoning_output_tokens == 3, token
        assert token.task_sha256 is not None, token
        assert token.task_chars == len("Inspect the bounded surface."), token
        assert token.task_preview is None, token

        token_preview = mod.parse_session(token_path, include_preview=True)
        assert token_preview.task_preview == "Inspect the bounded surface.", token_preview

        turn = mod.parse_session(turn_path, include_preview=False)
        assert turn.usage_method == "SUM_TURN_COMPLETED", turn
        assert turn.usage_confidence == "HIGH", turn
        assert turn.input_tokens == 300, turn
        assert turn.cached_input_tokens == 70, turn
        assert turn.output_tokens == 30, turn
        assert turn.reasoning_output_tokens == 12, turn

        low = mod.parse_session(low_path, include_preview=False)
        assert low.usage_method == "FINAL_GENERIC_USAGE_SNAPSHOT", low
        assert low.usage_confidence == "LOW", low
        assert low.input_tokens == 1500, low
        assert low.output_tokens == 150, low

        inventory = mod.inventory_codex_files(codex_home)
        paths = {row["path"] for row in inventory}
        assert "auth.json" not in paths, paths
        assert "history.jsonl" in paths, paths
        assert any(path.endswith("token-count.jsonl") for path in paths), paths

        discovered = mod.discover_sessions(codex_home)
        assert discovered == sorted([token_path, turn_path, low_path]), discovered

    print("Codex history collector semantics valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

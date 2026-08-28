#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
AGG = HERE / "aggregate_confirmatory.py"


def write_jsonl(path: Path, input_tokens: int, cached: int) -> None:
    path.write_text(
        json.dumps({
            "type": "turn.completed",
            "usage": {
                "input_tokens": input_tokens,
                "cached_input_tokens": cached,
                "output_tokens": 100,
                "reasoning_output_tokens": 10,
            },
        }) + "\n",
        encoding="utf-8",
    )


def write_meta(path: Path, wall: int = 20) -> None:
    path.write_text(json.dumps({
        "exit_code": 0,
        "git_head": "abc",
        "requested_model": "gpt-test",
        "wall_seconds": wall,
    }) + "\n", encoding="utf-8")


def good_text(include_exact_paths: bool = True) -> str:
    text = """STATE
RTS-FRZ-000024 is COMPLETED.
ADEQUACY
K2 is ADEQUATE only for a bounded current K2 inspection surface; zero observed defects is not zero residual defect risk.
NEXT
STOP unless a newly authorized bounded task exists.
EVIDENCE
some/current/repository/evidence.json
"""
    if include_exact_paths:
        text += """freezer/items/RTS-FRZ-000024/current.json
docs/implementation/frz000024_resolution.json
test_adequacy_gate/README.md
"""
    return text


def weak_cold_text() -> str:
    return """STATE
Current status is not restated here.
ADEQUACY
K2 is ADEQUATE, but residual risk remains and zero observed defects is not zero risk.
NEXT
STOP.
EVIDENCE
some/current/repository/evidence.json
"""


def bad_attested_text() -> str:
    return """STATE
RTS-FRZ-000024 is COMPLETED.
ADEQUACY
K2 is ADEQUATE.
NEXT
STOP.
EVIDENCE
freezer/items/RTS-FRZ-000024/current.json
docs/implementation/frz000024_resolution.json
test_adequacy_gate/README.md
"""


def run(root: Path) -> dict:
    subprocess.run(
        [sys.executable, str(AGG), "--results-dir", str(root), "--pairs", "3"],
        check=True,
        stdout=subprocess.DEVNULL,
    )
    return json.loads((root / "confirmatory_summary.json").read_text(encoding="utf-8"))


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        for i in range(1, 4):
            write_jsonl(root / f"pair{i}_cold.jsonl", 100_000 + i * 1_000, 20_000)
            write_jsonl(root / f"pair{i}_attested.jsonl", 30_000 + i * 1_000, 15_000)
            write_meta(root / f"pair{i}_cold.meta.json", 30)
            write_meta(root / f"pair{i}_attested.meta.json", 10)

        # Pair 1: baseline semantic failure, candidate passes -> IMPROVED.
        (root / "pair1_cold.final.txt").write_text(weak_cold_text(), encoding="utf-8")
        (root / "pair1_attested.final.txt").write_text(good_text(True), encoding="utf-8")

        # Pair 2: both semantic pass, but COLD lacks attested exact paths -> still PRESERVED.
        (root / "pair2_cold.final.txt").write_text(good_text(False), encoding="utf-8")
        (root / "pair2_attested.final.txt").write_text(good_text(True), encoding="utf-8")

        # Pair 3: candidate loses bounded/residual semantics -> REGRESSED and must fail.
        (root / "pair3_cold.final.txt").write_text(good_text(False), encoding="utf-8")
        (root / "pair3_attested.final.txt").write_text(bad_attested_text(), encoding="utf-8")

        first = run(root)
        assert first["pairs"][0]["quality_relation"] == "IMPROVED", first
        assert first["pairs"][0]["strict_pair_win"] is True, first
        assert first["pairs"][1]["quality_relation"] == "PRESERVED", first
        assert first["pairs"][1]["cold"]["quality"]["provenance_complete"] is False, first
        assert first["pairs"][1]["cold"]["quality"]["semantic_pass"] is True, first
        assert first["pairs"][1]["strict_pair_win"] is True, first
        assert first["pairs"][2]["quality_relation"] == "REGRESSED", first
        assert first["pairs"][2]["strict_pair_win"] is False, first
        assert first["result"] == "NOT_CONFIRMED", first

        # Repair candidate semantics only; all three must then confirm without changing token data.
        (root / "pair3_attested.final.txt").write_text(good_text(True), encoding="utf-8")
        second = run(root)
        assert second["strict_pair_wins"] == 3, second
        assert second["quality_relations"] == {
            "PRESERVED": 2,
            "IMPROVED": 1,
            "REGRESSED": 0,
            "BOTH_FAIL": 0,
        }, second
        assert second["result"] == "CONFIRMED_STRICT_WIN", second
        assert second["median_wall_time_reduction"] > 0, second
        print("confirmatory quality oracle symmetry valid")


if __name__ == "__main__":
    main()

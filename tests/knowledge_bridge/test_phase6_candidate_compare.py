from __future__ import annotations

from knowledge_bridge.candidate_compare import compare_candidates


def _candidate(path: str, score: float, *, responsibility: str = "state persistence responsibility", side_effect: str = "migration risk") -> str:
    return (
        f"{path}::save_record [role=implementation; score={score:.2f}; "
        f"responsibility={responsibility}; side_effect={side_effect}; path=storage]"
    )


def test_compare_candidates_selects_existing_boundary_and_ranks_primary() -> None:
    strategy, comparisons = compare_candidates(
        [_candidate("knowledge_bridge/storage.py", 0.81), _candidate("knowledge_bridge/state.py", 0.55)],
        ["tests/knowledge_bridge/test_storage.py::test_save [role=test; score=0.60]"],
        [],
    )
    assert strategy == "USE_EXISTING_BOUNDARY"
    assert "decision=PRIMARY" in comparisons[0]
    assert "required_tests=tests/knowledge_bridge/test_storage.py" in comparisons[0]
    assert "migration_cost_if_delayed=HIGH" in comparisons[0]


def test_compare_candidates_holds_when_foundation_is_blocking() -> None:
    strategy, comparisons = compare_candidates(
        [_candidate("knowledge_bridge/storage.py", 0.81)],
        [],
        ["rollback", "acceptance_criteria"],
    )
    assert strategy == "HOLD_FOR_FOUNDATION"
    assert "missing_foundations=rollback, acceptance_criteria" in comparisons[0]
    assert "new regression target required" in comparisons[0]


def test_compare_candidates_prefers_new_module_for_weak_evidence() -> None:
    strategy, comparisons = compare_candidates(
        [_candidate("misc/helper.py", 0.22, responsibility="module-local implementation responsibility")],
        [],
        [],
    )
    assert strategy == "CREATE_NEW_MODULE"
    assert "decision=WEAK_EVIDENCE" in comparisons[0]

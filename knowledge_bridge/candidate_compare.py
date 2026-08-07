from __future__ import annotations

import re
from pathlib import PurePosixPath

_SCORE_RE = re.compile(r"score=([0-9.]+)")
_RESPONSIBILITY_RE = re.compile(r"responsibility=([^;\]]+)")
_SIDE_EFFECT_RE = re.compile(r"side_effect=([^;\]]+)")


def _field(pattern: re.Pattern[str], value: str, default: str) -> str:
    match = pattern.search(value)
    return match.group(1).strip() if match else default


def _path(candidate: str) -> str:
    return candidate.split("::", 1)[0].strip()


def _boundary(candidate: str) -> str:
    tail = candidate.split("::", 1)[1] if "::" in candidate else "module"
    return tail.split(" [", 1)[0].strip()


def _score(candidate: str) -> float:
    try:
        return float(_field(_SCORE_RE, candidate, "0"))
    except ValueError:
        return 0.0


def _matching_tests(path: str, test_candidates: list[str]) -> list[str]:
    stem = PurePosixPath(path).stem.lower()
    parent = PurePosixPath(path).parent.name.lower()
    matches = []
    for candidate in test_candidates:
        lowered = _path(candidate).lower()
        if stem in lowered or (parent and parent in lowered):
            matches.append(_path(candidate))
    return matches[:3]


def _effort(path: str, boundary: str, side_effect: str) -> str:
    lowered = f"{path} {boundary} {side_effect}".lower()
    if any(token in lowered for token in ("migration", "durability", "orchestration", "event-order")):
        return "HIGH"
    if boundary != "module" or any(token in lowered for token in ("cli", "route", "state", "storage")):
        return "MEDIUM"
    return "LOW"


def _delay_cost(path: str, responsibility: str) -> str:
    lowered = f"{path} {responsibility}".lower()
    if any(token in lowered for token in ("state", "storage", "routing", "orchestration", "schema")):
        return "HIGH"
    if any(token in lowered for token in ("cli", "workflow", "integration")):
        return "MEDIUM"
    return "LOW"


def compare_candidates(
    insertion_candidates: list[str],
    test_candidates: list[str],
    blocking_missing_parts: list[str],
) -> tuple[str, list[str]]:
    if blocking_missing_parts:
        strategy = "HOLD_FOR_FOUNDATION"
    elif not insertion_candidates:
        strategy = "CREATE_NEW_MODULE_OR_CLARIFY_ARCHITECTURE"
    elif _score(insertion_candidates[0]) < 0.35:
        strategy = "CREATE_NEW_MODULE"
    else:
        strategy = "USE_EXISTING_BOUNDARY"

    comparisons: list[str] = []
    for index, candidate in enumerate(insertion_candidates[:4], start=1):
        path = _path(candidate)
        boundary = _boundary(candidate)
        score = _score(candidate)
        responsibility = _field(_RESPONSIBILITY_RE, candidate, "unknown responsibility")
        side_effect = _field(_SIDE_EFFECT_RE, candidate, "unknown side effect")
        tests = _matching_tests(path, test_candidates)
        decision = "PRIMARY" if index == 1 else "SECONDARY" if index == 2 else "ALTERNATIVE"
        if score < 0.35:
            decision = "WEAK_EVIDENCE"
        required_tests = ", ".join(tests) if tests else "new regression target required"
        foundations = ", ".join(blocking_missing_parts) if blocking_missing_parts else "none detected"
        comparisons.append(
            f"rank={index}; decision={decision}; path={path}; boundary={boundary}; score={score:.2f}; "
            f"responsibility={responsibility}; side_effect={side_effect}; required_tests={required_tests}; "
            f"missing_foundations={foundations}; estimated_effort={_effort(path, boundary, side_effect)}; "
            f"migration_cost_if_delayed={_delay_cost(path, responsibility)}"
        )
    return strategy, comparisons

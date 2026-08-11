"""Advisory-only decision review pressure prototype.

This module does NOT estimate probability of being wrong. It computes a transparent,
heuristic review-pressure index from information available at decision time and emits
extra-review guidance. Thresholds/weights are priors to be calibrated against future
labeled outcomes.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


class DecisionSentinelError(ValueError):
    pass


def _unit_interval(value: float, name: str) -> float:
    value = float(value)
    if not math.isfinite(value) or not 0.0 <= value <= 1.0:
        raise DecisionSentinelError(f"{name} must be in [0,1]")
    return value


def _nonnegative(value: float, name: str) -> float:
    value = float(value)
    if not math.isfinite(value) or value < 0:
        raise DecisionSentinelError(f"{name} must be finite and nonnegative")
    return value


def _sat(value: float, scale: float) -> float:
    return 1.0 - math.exp(-_nonnegative(value, "value") / scale)


@dataclass(frozen=True)
class DecisionState:
    severity: int
    evidence_quality: float
    axis_coverage: float
    recent_revision_load: float = 0.0
    recent_context_switch_load: float = 0.0
    unresolved_counterevidence: bool = False
    irreversible: bool = False


def review_pressure(state: DecisionState) -> dict[str, object]:
    """Return a transparent review-pressure advisory.

    DRP_100 is a heuristic prior, not a calibrated probability of error.
    Only launch/decision-time information belongs here; future outcomes are forbidden.
    """
    if state.severity not in (1, 2, 3):
        raise DecisionSentinelError("severity must be D1=1, D2=2, or D3=3")
    q = _unit_interval(state.evidence_quality, "evidence_quality")
    coverage = _unit_interval(state.axis_coverage, "axis_coverage")
    revision = _nonnegative(state.recent_revision_load, "recent_revision_load")
    switching = _nonnegative(state.recent_context_switch_load, "recent_context_switch_load")

    severity_pressure = {1: 0.0, 2: 0.5, 3: 1.0}[state.severity]
    components = {
        "severity": severity_pressure,
        "evidence_gap": 1.0 - q,
        "coverage_gap": 1.0 - coverage,
        "revision_pressure": _sat(revision, 5.0),
        "context_switch_pressure": _sat(switching, 4.0),
        "counterevidence": 1.0 if state.unresolved_counterevidence else 0.0,
        "irreversibility": 1.0 if state.irreversible else 0.0,
    }
    weights = {
        "severity": 0.20,
        "evidence_gap": 0.25,
        "coverage_gap": 0.10,
        "revision_pressure": 0.15,
        "context_switch_pressure": 0.10,
        "counterevidence": 0.15,
        "irreversibility": 0.05,
    }
    raw = 100.0 * sum(weights[k] * components[k] for k in weights)

    # Fail-safe rule overrides for high-impact decisions under weak evidence.
    if state.severity == 3 and (q < 0.60 or state.unresolved_counterevidence):
        level = "RED"
    elif state.irreversible and q < 0.40:
        level = "RED"
    elif raw >= 60.0:
        level = "RED"
    elif (state.severity >= 2 and q < 0.75) or raw >= 35.0:
        level = "AMBER"
    else:
        level = "GREEN"

    action = {
        "GREEN": "PROCEED_AND_LOG",
        "AMBER": "REQUIRE_ONE_INDEPENDENT_CHECK_OR_DA",
        "RED": "HOLD_IRREVERSIBLE_ACTION_UNTIL_EVIDENCE_OR_AUTHORITY_RECHECK",
    }[level]

    reasons = [k for k, v in components.items() if v >= 0.5]
    return {
        "level": level,
        "drp_100": round(raw, 2),
        "action": action,
        "reasons": reasons,
        "components": {k: round(v, 4) for k, v in components.items()},
        "semantics": "HEURISTIC_REVIEW_PRESSURE_NOT_ERROR_PROBABILITY",
    }


def classify_revision_outcome(kind: str) -> str:
    """Prevent 'later revised' from being silently treated as 'wrong'."""
    normalized = kind.strip().upper()
    allowed = {
        "CORRECTIVE_ERROR": "NEGATIVE_LABEL_CANDIDATE",
        "NEW_EVIDENCE": "NOT_ERROR_LABEL",
        "SCOPE_CHANGE": "NOT_ERROR_LABEL",
        "ROUTINE_ITERATION": "NOT_ERROR_LABEL",
        "UNKNOWN": "UNRESOLVED_LABEL",
    }
    if normalized not in allowed:
        raise DecisionSentinelError(f"unsupported revision outcome kind: {kind!r}")
    return allowed[normalized]

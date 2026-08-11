"""Evidence-bounded human->machine amplification helpers for the Human Return ETA /goal.

These helpers do not estimate human effort from commit counts. They keep human load,
causally/semantically bound governed stages, and machine-visible output as separate layers.

DA hardening:
- a lower bound in a denominator creates an UPPER bound on the corresponding ratio;
- post-hoc elapsed gate time must not be smuggled into launch-time prediction features.
"""

from __future__ import annotations

import math


class OperatorMachineModelError(ValueError):
    pass


def _nonnegative(value: float, name: str) -> float:
    value = float(value)
    if not math.isfinite(value) or value < 0:
        raise OperatorMachineModelError(f"{name} must be finite and nonnegative")
    return value


def stages_per_decision_unit(bound_stages: float, decision_units: float) -> float:
    """Governed/bound machine stages per evidence-bound decision-load unit (DLU)."""
    stages = _nonnegative(bound_stages, "bound_stages")
    decisions = _nonnegative(decision_units, "decision_units")
    if decisions <= 0:
        raise OperatorMachineModelError("decision_units must be positive")
    return stages / decisions


def visible_output_per_stage(machine_visible_output: float, governed_stages: float) -> float:
    """Machine-visible output per governed stage; never a human-effort measure."""
    output = _nonnegative(machine_visible_output, "machine_visible_output")
    stages = _nonnegative(governed_stages, "governed_stages")
    if stages <= 0:
        raise OperatorMachineModelError("governed_stages must be positive")
    return output / stages


def visible_output_per_decision_unit(machine_visible_output: float, decision_units: float) -> float:
    """Visible-output amplification per DLU. Output may be commits only when explicitly labeled proxy."""
    output = _nonnegative(machine_visible_output, "machine_visible_output")
    decisions = _nonnegative(decision_units, "decision_units")
    if decisions <= 0:
        raise OperatorMachineModelError("decision_units must be positive")
    return output / decisions


def factorized_visible_output_amplification(
    machine_visible_output: float,
    governed_stages: float,
    decision_units: float,
) -> float:
    """Verify Lambda = (output/stage) * (stage/DLU) = output/DLU."""
    return visible_output_per_stage(machine_visible_output, governed_stages) * stages_per_decision_unit(
        governed_stages, decision_units
    )


def ratio_upper_bound_from_denominator_lower_bound(numerator: float, denominator_lower_bound: float) -> float:
    """Return numerator / denominator_lower_bound as an upper bound on the true ratio.

    If D_true >= D_lower > 0, then N / D_true <= N / D_lower.
    This is the correct interpretation for Gamma_J or Lambda when J is only J>=k.
    """
    top = _nonnegative(numerator, "numerator")
    lower = _nonnegative(denominator_lower_bound, "denominator_lower_bound")
    if lower <= 0:
        raise OperatorMachineModelError("denominator_lower_bound must be positive")
    return top / lower


def amplification_with_decision_lower_bound(
    machine_visible_output: float,
    governed_stages: float,
    decision_units_lower_bound: float,
) -> dict[str, float | str]:
    """Bound-aware amplification summary when J is only known as a lower bound."""
    gamma_m = visible_output_per_stage(machine_visible_output, governed_stages)
    gamma_j_upper = ratio_upper_bound_from_denominator_lower_bound(
        governed_stages, decision_units_lower_bound
    )
    lambda_upper = ratio_upper_bound_from_denominator_lower_bound(
        machine_visible_output, decision_units_lower_bound
    )
    return {
        "gamma_j_upper": gamma_j_upper,
        "gamma_m_point_proxy": gamma_m,
        "lambda_upper": lambda_upper,
        "decision_denominator_semantics": "LOWER_BOUND",
    }


def launch_safe_orchestration(governed_stages_known_at_launch: float) -> float:
    """Launch-time orchestration feature that contains no future elapsed gate time.

    Historical/post-hoc O may include elapsed gate time. That term is forbidden here because
    using future elapsed time to predict return time would leak the target into the features.
    """
    return _nonnegative(governed_stages_known_at_launch, "governed_stages_known_at_launch")


def observed_control_pressure(E: float, J: float, O: float, R: float) -> float:
    """(J+O+R)/E on observed components only.

    This is a descriptive proxy, NOT coverage-invariant and NOT a fatigue/clinical score.
    Missing components must not be passed as semantic zero. Because both numerator and
    denominator can be partially observed, this ratio is not generally a lower or upper bound.
    """
    execution = _nonnegative(E, "E")
    if execution <= 0:
        raise OperatorMachineModelError("E must be positive")
    return (
        _nonnegative(J, "J")
        + _nonnegative(O, "O")
        + _nonnegative(R, "R")
    ) / execution

"""Evidence-bounded human->machine amplification helpers for the Human Return ETA /goal.

These helpers do not estimate human effort from commit counts. They keep human load,
causally/semantically bound governed stages, and machine-visible output as separate layers.
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


def observed_control_pressure(E: float, J: float, O: float, R: float) -> float:
    """(J+O+R)/E on observed lower-bound components only.

    This is a descriptive proxy, NOT coverage-invariant and NOT a fatigue/clinical score.
    Missing components must not be passed as semantic zero.
    """
    execution = _nonnegative(E, "E")
    if execution <= 0:
        raise OperatorMachineModelError("E must be positive")
    return (
        _nonnegative(J, "J")
        + _nonnegative(O, "O")
        + _nonnegative(R, "R")
    ) / execution

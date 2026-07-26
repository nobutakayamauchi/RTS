from __future__ import annotations

import re
from typing import Any

from .common import (
    PilotRunContractError,
    exact,
    fingerprint_material,
    sha256_value,
    string_list,
    text,
)

SCHEMA_VERSION = "RTS-PILOT-SEED-V1"
SEED_ID_PATTERN = re.compile(r"^RTS-PILOT-SEED-[A-Z0-9-]{3,96}$")
ROOT_FIELDS = {
    "schema_version", "seed_id", "seed_fingerprint", "project", "objective",
    "constraints", "work_policy", "inputs", "outputs", "authority", "readiness",
}
REQUIRED_FORBIDDEN_ACTIONS = {
    "automatic contract acceptance",
    "automatic external publication",
    "automatic human ranking",
    "automatic outreach or application",
    "automatic support-recipient selection",
    "credential or private-data persistence",
    "provider use without a new approval gate",
    "target or adjacent-repository write without a new approval gate",
}


def _digest(value: Any, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or set(value) - set("0123456789abcdef"):
        raise PilotRunContractError(f"{label} must be a lowercase SHA-256 digest")
    return value


def _false(value: Any, label: str) -> None:
    if value is not False:
        raise PilotRunContractError(f"{label} authority boundary widened")


def validate_seed(seed: dict[str, Any]) -> dict[str, Any]:
    seed = exact(seed, ROOT_FIELDS, "pilot seed")
    if seed["schema_version"] != SCHEMA_VERSION:
        raise PilotRunContractError("pilot seed schema_version mismatch")
    seed_id = text(seed["seed_id"], "seed_id", 128)
    if not SEED_ID_PATTERN.fullmatch(seed_id):
        raise PilotRunContractError("invalid seed_id")
    _digest(seed["seed_fingerprint"], "seed_fingerprint")

    project = exact(seed["project"], {"title", "case_id", "purpose", "current_scope"}, "project")
    for field in project:
        text(project[field], f"project.{field}")

    objective = exact(seed["objective"], {"final_goal", "current_goal", "completion_conditions"}, "objective")
    text(objective["final_goal"], "objective.final_goal")
    text(objective["current_goal"], "objective.current_goal")
    string_list(objective["completion_conditions"], "objective.completion_conditions")

    constraints = exact(seed["constraints"], {"wip_limit", "human_gate_required", "forbidden_actions"}, "constraints")
    if constraints["wip_limit"] != 1:
        raise PilotRunContractError("pilot wip_limit must remain 1")
    if constraints["human_gate_required"] is not True:
        raise PilotRunContractError("human gate must remain required")
    forbidden_actions = set(string_list(constraints["forbidden_actions"], "constraints.forbidden_actions"))
    missing_forbidden = sorted(REQUIRED_FORBIDDEN_ACTIONS - forbidden_actions)
    if missing_forbidden:
        raise PilotRunContractError(
            "pilot safety boundary removed required forbidden actions: " + ", ".join(missing_forbidden)
        )

    policy = exact(seed["work_policy"], {"selection", "checkpoint", "resume", "stop_conditions"}, "work_policy")
    for field in ("selection", "checkpoint", "resume"):
        text(policy[field], f"work_policy.{field}")
    string_list(policy["stop_conditions"], "work_policy.stop_conditions")

    inputs = exact(seed["inputs"], {"source_refs"}, "inputs")
    string_list(inputs["source_refs"], "inputs.source_refs")
    outputs = exact(seed["outputs"], {"required_artifacts"}, "outputs")
    string_list(outputs["required_artifacts"], "outputs.required_artifacts")

    authority = exact(
        seed["authority"],
        {
            "mode", "advisory_only", "external_execution_authorized", "provider_authorized",
            "publication_authorized", "target_write_authorized",
            "adjacent_repository_write_authorized", "automatic_approval_authorized",
        },
        "authority",
    )
    if authority["mode"] != "GOVERNED_PILOT" or authority["advisory_only"] is not True:
        raise PilotRunContractError("pilot authority mode widened")
    for field in (
        "external_execution_authorized", "provider_authorized", "publication_authorized",
        "target_write_authorized", "adjacent_repository_write_authorized",
        "automatic_approval_authorized",
    ):
        _false(authority[field], f"authority.{field}")

    readiness = exact(seed["readiness"], {"state", "known_gaps"}, "readiness")
    if readiness["state"] != "READY_FOR_PILOT":
        raise PilotRunContractError("pilot readiness state mismatch")
    string_list(readiness["known_gaps"], "readiness.known_gaps")

    expected = sha256_value(fingerprint_material(seed))
    if seed["seed_fingerprint"] != expected:
        raise PilotRunContractError("pilot seed fingerprint mismatch")
    return seed

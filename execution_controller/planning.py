from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from .governance import _governed_state, _relative_or_absolute
from .models import (
    AUTHORITY,
    PLAN_SCHEMA_VERSION,
    ControllerError,
    load_json,
    sha256_file,
    sha256_value,
    validate_authorization,
    validate_budgets,
    validate_plan,
)

def plan_execution(root: Path, authorization_path: Path) -> dict[str, Any]:
    root = root.resolve()
    authorization_path = authorization_path.resolve()
    authorization = validate_authorization(load_json(authorization_path))
    budgets = validate_budgets(authorization["budgets"])
    if budgets["max_events"] < 5:
        raise ControllerError("max_events must allow authorization, dispatch, running, verification, and one terminal event")
    evidence, governed_paths = _governed_state(root, authorization)
    paths = governed_paths + [authorization_path]
    input_rows = [
        {"path": _relative_or_absolute(path, root), "sha256": sha256_file(path)}
        for path in sorted(paths, key=lambda candidate: _relative_or_absolute(candidate, root))
    ]
    plan: dict[str, Any] = {
        "schema_version": PLAN_SCHEMA_VERSION,
        "plan_id": "0" * 64,
        "authority": AUTHORITY,
        "external_execution_authorized": False,
        "item_id": authorization["item_id"],
        "item_version": authorization["item_version"],
        "authorization_id": authorization["authorization_id"],
        "authorization_fingerprint": authorization["authorization_fingerprint"],
        "adapter_id": authorization["adapter_id"],
        "execution_identifiers": {
            "skill_id": authorization["skill_id"],
            "drive_id": authorization["drive_id"],
            "pack_id": authorization["pack_id"],
            "trigger": authorization["trigger"],
        },
        "allowed_capabilities": list(authorization["allowed_capabilities"]),
        "budgets": dict(authorization["budgets"]),
        "stop_conditions": list(authorization["stop_conditions"]),
        "initial_state": "PLANNED",
        "inputs": input_rows,
        "gate_evidence": evidence,
    }
    material = copy.deepcopy(plan)
    material.pop("plan_id")
    plan["plan_id"] = sha256_value(material)
    validate_plan(plan)
    return plan

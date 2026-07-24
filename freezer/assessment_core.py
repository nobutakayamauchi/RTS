"""Core scoring and validation for FREEZER build assessments."""
from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

PACKAGE_DIR = Path(__file__).resolve().parent
DEFAULT_ROOT = PACKAGE_DIR.parent
ITEM_ID_PREFIX = "RTS-FRZ-"
RECOMMENDATIONS = {"BUILD_NOW", "BUILD_NEXT", "DEFER", "RESEARCH_REQUIRED", "REJECT"}
REUSE_MODES = {"DIRECT", "ADAPT", "REFERENCE", "NONE"}
LICENSE_STATUSES = {"OWNED", "COMPATIBLE", "REVIEW_REQUIRED", "UNKNOWN"}
ASSET_KINDS = {"code", "schema", "test", "workflow", "documentation", "data", "design"}
ASSESSMENT_PLAN_FIELDS = (
    "item_id", "title", "type", "summary", "original_problem", "why_it_matters",
    "preserved_value", "negative_triggers", "dependencies", "source_refs",
    "possible_destinations", "estimated_hours",
)
BENEFIT_FIELDS = {
    "impact", "strategic_fit", "revenue_leverage", "risk_reduction", "recurrence", "confidence"
}
BENEFIT_WEIGHTS = {
    "impact": 2.0, "strategic_fit": 1.5, "revenue_leverage": 1.2,
    "risk_reduction": 1.3, "recurrence": 1.0, "confidence": 1.0,
}
IMPLEMENTATION_FIELDS = {
    "from_scratch_hours", "integration_hours", "validation_hours", "unknown_buffer_hours"
}
GITHUB_SCAN_FIELDS = {"performed", "repositories", "queries", "assets", "gaps"}
ASSET_FIELDS = {
    "repository", "path", "ref", "kind", "reuse_mode", "license_status",
    "estimated_hours_saved", "notes",
}
INPUT_FIELDS = {"assessor", "rationale", "expected_effect", "implementation", "github_scan", "risks"}
GENERATED_FIELDS = {
    "assessment_id", "item_id", "assessment_version", "item_version_snapshot",
    "item_fingerprint", "derived", "created_at",
}
RECORD_FIELDS = INPUT_FIELDS | GENERATED_FIELDS
DERIVED_FIELDS = {
    "benefit_score", "cost_score", "reuse_score", "decision_score",
    "reuse_hours_saved", "net_hours", "time_saved_ratio",
    "implementation_efficiency", "cost_effectiveness", "recommendation",
}


class BuildAssessmentError(RuntimeError):
    """Raised for invalid, stale, or missing build assessments."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise BuildAssessmentError(f"missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise BuildAssessmentError(f"invalid JSON: {path}: {exc}") from exc


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def items_root(root: Path) -> Path:
    return root / "freezer" / "items"


def item_current_path(root: Path, item_id: str) -> Path:
    return items_root(root) / item_id / "current.json"


def all_item_ids(root: Path) -> list[str]:
    base = items_root(root)
    if not base.exists():
        return []
    return sorted(p.name for p in base.iterdir() if p.is_dir() and p.name.startswith(ITEM_ID_PREFIX))


def load_current_item(root: Path, item_id: str) -> dict[str, Any]:
    pointer = load_json(item_current_path(root, item_id))
    version = pointer.get("current_version")
    if pointer.get("item_id") != item_id or not isinstance(version, int):
        raise BuildAssessmentError(f"{item_id}: invalid item current pointer")
    item = load_json(items_root(root) / item_id / f"v{version:03d}.json")
    if item.get("item_id") != item_id or item.get("version") != version:
        raise BuildAssessmentError(f"{item_id}: item pointer/version mismatch")
    return item


def iter_current_items(root: Path) -> Iterable[dict[str, Any]]:
    for item_id in all_item_ids(root):
        yield load_current_item(root, item_id)


def load_config(root: Path) -> dict[str, Any]:
    return load_json(root / "freezer" / "config.json")


def canonical_plan(item: dict[str, Any]) -> dict[str, Any]:
    missing = [field for field in ASSESSMENT_PLAN_FIELDS if field not in item]
    if missing:
        raise BuildAssessmentError(
            f"{item.get('item_id', '<unknown>')}: missing assessment plan fields: {', '.join(missing)}"
        )
    return {field: item[field] for field in ASSESSMENT_PLAN_FIELDS}


def item_fingerprint(item: dict[str, Any]) -> str:
    payload = json.dumps(canonical_plan(item), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _number(value: Any, *, field: str, minimum: float = 0.0) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise BuildAssessmentError(f"{field} must be numeric")
    number = float(value)
    if not math.isfinite(number) or number < minimum:
        raise BuildAssessmentError(f"{field} must be finite and >= {minimum}")
    return number


def _score(value: Any, *, field: str) -> float:
    number = _number(value, field=field)
    if number > 5:
        raise BuildAssessmentError(f"{field} must be between 0 and 5")
    return number


def _string_list(value: Any, *, field: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(v, str) for v in value):
        raise BuildAssessmentError(f"{field} must be a string list")
    return value


def _exact(value: Any, expected: set[str], *, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise BuildAssessmentError(f"{field} must be an object")
    missing = sorted(expected - value.keys())
    extra = sorted(value.keys() - expected)
    if missing:
        raise BuildAssessmentError(f"{field} missing fields: {', '.join(missing)}")
    if extra:
        raise BuildAssessmentError(f"{field} unknown fields: {', '.join(extra)}")
    return value


def validate_input(raw: dict[str, Any]) -> None:
    _exact(raw, INPUT_FIELDS, field="assessment input")
    if not isinstance(raw["assessor"], str) or not raw["assessor"].strip():
        raise BuildAssessmentError("assessor is required")
    if not isinstance(raw["rationale"], str) or not raw["rationale"].strip():
        raise BuildAssessmentError("rationale is required")
    _string_list(raw["risks"], field="risks")

    effect = _exact(raw["expected_effect"], BENEFIT_FIELDS, field="expected_effect")
    for name, value in effect.items():
        _score(value, field=f"expected_effect.{name}")

    implementation = _exact(raw["implementation"], IMPLEMENTATION_FIELDS, field="implementation")
    for name, value in implementation.items():
        _number(value, field=f"implementation.{name}")
    if float(implementation["from_scratch_hours"]) <= 0:
        raise BuildAssessmentError("implementation.from_scratch_hours must be > 0")

    scan = _exact(raw["github_scan"], GITHUB_SCAN_FIELDS, field="github_scan")
    if not isinstance(scan["performed"], bool):
        raise BuildAssessmentError("github_scan.performed must be boolean")
    repositories = _string_list(scan["repositories"], field="github_scan.repositories")
    queries = _string_list(scan["queries"], field="github_scan.queries")
    _string_list(scan["gaps"], field="github_scan.gaps")
    if scan["performed"] and (not repositories or not queries):
        raise BuildAssessmentError("a performed GitHub scan requires repositories and queries")
    if not isinstance(scan["assets"], list):
        raise BuildAssessmentError("github_scan.assets must be a list")
    for i, asset in enumerate(scan["assets"]):
        asset = _exact(asset, ASSET_FIELDS, field=f"github_scan.assets[{i}]")
        for field in ("repository", "path", "ref", "notes"):
            if not isinstance(asset[field], str):
                raise BuildAssessmentError(f"github_scan.assets[{i}].{field} must be a string")
        if asset["kind"] not in ASSET_KINDS:
            raise BuildAssessmentError(f"github_scan.assets[{i}].kind must be one of {sorted(ASSET_KINDS)}")
        if asset["reuse_mode"] not in REUSE_MODES:
            raise BuildAssessmentError(f"github_scan.assets[{i}].reuse_mode must be one of {sorted(REUSE_MODES)}")
        if asset["license_status"] not in LICENSE_STATUSES:
            raise BuildAssessmentError(
                f"github_scan.assets[{i}].license_status must be one of {sorted(LICENSE_STATUSES)}"
            )
        saved = _number(asset["estimated_hours_saved"], field=f"github_scan.assets[{i}].estimated_hours_saved")
        if asset["reuse_mode"] == "NONE" and saved != 0:
            raise BuildAssessmentError(f"github_scan.assets[{i}] with reuse_mode NONE must save 0 hours")


def derive(raw: dict[str, Any]) -> dict[str, Any]:
    validate_input(raw)
    effect = raw["expected_effect"]
    benefit = sum(_score(effect[k], field=f"expected_effect.{k}") * w for k, w in BENEFIT_WEIGHTS.items())
    benefit_score = round(benefit / (5 * sum(BENEFIT_WEIGHTS.values())) * 100, 2)

    implementation = raw["implementation"]
    from_scratch = float(implementation["from_scratch_hours"])
    assets = raw["github_scan"]["assets"]
    license_blocked = any(
        a["reuse_mode"] in {"DIRECT", "ADAPT"}
        and a["license_status"] in {"REVIEW_REQUIRED", "UNKNOWN"}
        for a in assets
    )
    reusable = sum(
        float(a["estimated_hours_saved"])
        for a in assets
        if a["reuse_mode"] == "REFERENCE"
        or (a["reuse_mode"] in {"DIRECT", "ADAPT"} and a["license_status"] in {"OWNED", "COMPATIBLE"})
    )
    reuse_hours_saved = round(min(reusable, from_scratch), 2)
    net_hours = round(
        max(from_scratch - reuse_hours_saved, 0)
        + float(implementation["integration_hours"])
        + float(implementation["validation_hours"])
        + float(implementation["unknown_buffer_hours"]),
        2,
    )
    time_saved_ratio = round(reuse_hours_saved / from_scratch, 4)
    implementation_efficiency = round(from_scratch / max(net_hours, 0.01), 2)
    cost_score = round(100 / (1 + net_hours / 8), 2)
    reuse_score = round(time_saved_ratio * 100, 2)
    decision_score = round(benefit_score * 0.55 + cost_score * 0.30 + reuse_score * 0.15, 2)
    cost_effectiveness = round(benefit_score / max(net_hours, 0.5), 2)

    confidence = float(effect["confidence"])
    if not raw["github_scan"]["performed"] or confidence < 2 or license_blocked:
        recommendation = "RESEARCH_REQUIRED"
    elif decision_score >= 70:
        recommendation = "BUILD_NOW"
    elif decision_score >= 55:
        recommendation = "BUILD_NEXT"
    elif decision_score >= 40:
        recommendation = "DEFER"
    else:
        recommendation = "REJECT"

    return {
        "benefit_score": benefit_score,
        "cost_score": cost_score,
        "reuse_score": reuse_score,
        "decision_score": decision_score,
        "reuse_hours_saved": reuse_hours_saved,
        "net_hours": net_hours,
        "time_saved_ratio": time_saved_ratio,
        "implementation_efficiency": implementation_efficiency,
        "cost_effectiveness": cost_effectiveness,
        "recommendation": recommendation,
    }


def validate_timestamp(value: Any, *, item_id: str) -> None:
    if not isinstance(value, str) or not value:
        raise BuildAssessmentError(f"{item_id}: created_at must be a date-time string")
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise BuildAssessmentError(f"{item_id}: invalid created_at={value!r}") from exc


def validate_record(record: dict[str, Any]) -> None:
    _exact(record, RECORD_FIELDS, field="assessment record")
    raw = {field: record[field] for field in INPUT_FIELDS}
    validate_input(raw)
    item_id = record["item_id"]
    if not isinstance(item_id, str) or not item_id.startswith(ITEM_ID_PREFIX):
        raise BuildAssessmentError(f"invalid assessment item_id: {item_id!r}")
    suffix = item_id.removeprefix(ITEM_ID_PREFIX)
    if len(suffix) != 6 or not suffix.isdigit():
        raise BuildAssessmentError(f"invalid assessment item_id: {item_id!r}")
    version = record["assessment_version"]
    if not isinstance(version, int) or version < 1:
        raise BuildAssessmentError(f"{item_id}: invalid assessment_version")
    expected_id = f"RTS-BA-{suffix}-{version:03d}"
    if record["assessment_id"] != expected_id:
        raise BuildAssessmentError(f"{item_id}: assessment_id mismatch; expected={expected_id!r}")
    if not isinstance(record["item_version_snapshot"], int) or record["item_version_snapshot"] < 1:
        raise BuildAssessmentError(f"{item_id}: invalid item_version_snapshot")
    fingerprint = record["item_fingerprint"]
    if not isinstance(fingerprint, str) or len(fingerprint) != 64 or any(c not in "0123456789abcdef" for c in fingerprint):
        raise BuildAssessmentError(f"{item_id}: invalid item_fingerprint")
    validate_timestamp(record["created_at"], item_id=item_id)
    derived = _exact(record["derived"], DERIVED_FIELDS, field="derived")
    if derived["recommendation"] not in RECOMMENDATIONS:
        raise BuildAssessmentError(f"{item_id}: invalid recommendation={derived['recommendation']!r}")
    if derived != derive(raw):
        raise BuildAssessmentError(f"{item_id}: derived assessment values do not match inputs")

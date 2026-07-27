from __future__ import annotations

import base64
import copy
import hashlib
import json
import zlib
from pathlib import Path
from typing import Any

from .core import ProofEngineError, fingerprint, load
from .report_template import REQUIRED_SECTIONS

P = Path(__file__).resolve().parent
ROOT = P.parent
ROUND = P / "product_readiness" / "round_0004"
BUNDLE = ROUND / "package_bundle.b64"
STATUS = ROOT / "docs/status/RTS_CURRENT_POSITION.json"
SPEED = ROOT / "docs/status/RTS_DEVELOPMENT_SPEED_BASELINE.json"
CHECKPOINT = ROOT / "pilot_runs/reconnect_pilot_p3/evidence_report_third_case_checkpoint_0025.json"
PRIOR = {
    P / "report_operational_validation_build.py": "8c2a269a26a0b31420258cd2cd2869a1beab469c",
    P / "report_operational_validation_build_v2.py": "ea5e7f5fdd36a15c087abed770449c1143a5e854",
}
E = {
    "bundle": "dba5dd90d3ffbbcb9892c4167a0b64cfba3fd569db96c372aa132a45181a8125",
    "selection": "4f1786333ea197cb53b43537abdd0063f78ea044c9212f41299df504e314ffc3",
    "manifest": "7ded6921108cc748da62d0487c7bbc3525e89e6bb12724ff2c622324a6e742c7",
    "report": "540dd27d967cd0658026b5aab3060059187060063c628200292c7fea7e6c438d",
    "markdown": "2b5d8d5f09a27b7b6219a1eedf08b4f3e33401937e370403795fb1bd7bcb2472",
    "inventory": "3d8ec84ca320b0e6290f0d7abfa22e66ca355c76ea18a820f1c707d36f8a7503",
    "comparison": "a2a7b875b12509c2e94995b6bac1a434fe6d740bac141a5b4a3cd2b2c4013d41",
    "acceptance": "fff9a21630fd7974b7f4c3c64e19948496c0e95dea0b7cf47df1920123787efd",
    "verification": "0b8ac9b7df89feb5d1b11933ad7dcce8cba3897cb53fafe5455230e571e56a85",
    "rollback": "7a195758e8974b323be3715bcef2a790d9ca4aed6228a8ac9aea0ee7dafd0554",
    "speed": "fd61a24882e77273586d081ebf02b86a77b2a6a59e2f622399a9ed8a2ca2de56",
    "result": "2c8f2ceb0e59b71b113b4387ceff11052517dc225b45ac50b50ac9d5f1fe09f3",
    "status": "824b41c985fa7cb20f72bdfe4c03ede18a3eaf365b3d77c488f870be4ccfc12a",
    "checkpoint": "5d93792679d3550693f70c282949d30ed6a773bce8519baa2b699e9b49ebee81",
}
FALSE = {
    "contract_authorized", "customer_intake_authorized", "customer_pilot_authorized",
    "delivery_authorized", "external_execution_authorized", "outreach_authorized",
    "pricing_authorized", "publication_authorized", "source_repository_write_authorized",
    "target_repository_write_authorized",
}
PRS = [55, 56, 57, 59, 62, 63, 64, 65]
WITHHELD = [
    "RUN_ID_COLLISION_RESISTANCE", "EXTERNAL_API_OPERATION",
    "AUTOMATED_PUBLICATION_OR_SENDING", "CONTENT_EFFECTIVENESS", "PRODUCTION_READINESS",
]


def _signed(v: dict[str, Any], field: str, expected: str, label: str) -> dict[str, Any]:
    m = copy.deepcopy(v)
    actual = m.pop(field, None)
    if actual != expected or fingerprint(m) != actual:
        raise ProofEngineError(f"{label} fingerprint mismatch")
    return v


def _false(v: dict[str, Any], label: str) -> None:
    if not FALSE.issubset(v) or any(v[k] is not False for k in FALSE):
        raise ProofEngineError(f"{label} authority widened")


def _blob(path: Path) -> str:
    b = path.read_bytes()
    return hashlib.sha1(f"blob {len(b)}\0".encode() + b).hexdigest()


def verify_prior_builder_unchanged() -> dict[str, str]:
    got = {str(path.name): _blob(path) for path in PRIOR}
    if any(_blob(path) != expected for path, expected in PRIOR.items()):
        raise ProofEngineError("prior generic builder surface changed")
    return got


def verify_bundle(value: dict[str, Any] | None = None) -> dict[str, Any]:
    if value is None:
        try:
            value = json.loads(zlib.decompress(base64.b64decode(BUNDLE.read_text())).decode())
        except (OSError, ValueError, zlib.error, json.JSONDecodeError) as exc:
            raise ProofEngineError("invalid third-case bundle") from exc
    _signed(value, "bundle_fingerprint", E["bundle"], "bundle")
    keys = {
        "case_selection", "source_manifest", "report_json", "report_markdown",
        "evidence_inventory", "three_case_comparison", "acceptance_packet",
        "verification_summary", "rollback_index", "hardening_execution_result",
    }
    if value.get("logical_artifact_count") != 8 or set(value.get("artifacts", {})) != keys:
        raise ProofEngineError("bundle shape mismatch")
    return value


def _a(name: str) -> Any:
    return copy.deepcopy(verify_bundle()["artifacts"][name])


def verify_selection(value: dict[str, Any] | None = None) -> dict[str, Any]:
    v = _signed(value or _a("case_selection"), "selection_fingerprint", E["selection"], "selection")
    s = v.get("selected_case", {})
    expected = {
        "repository": "nobutakayamauchi/RTS-AGE", "visibility": "PUBLIC",
        "source_mode": "READ_ONLY_FIXED_COMMIT",
        "snapshot_ref": "b5493b3dfb19955f24fac8134a2f77c2d4d8bb71",
        "source_entrypoint": "src/generate.py",
        "source_entrypoint_blob_sha": "549d85702db9d28d3db07e188d84921bc56b0e11",
        "selected_pr_numbers": PRS,
    }
    if s != expected or [x.get("pr_number") for x in v.get("excluded_sources", [])] != [66, 67]:
        raise ProofEngineError("source boundary mismatch")
    if v.get("prior_builder_bindings", {}).get("prior_builder_files_modified") is not False:
        raise ProofEngineError("builder modification claimed")
    _false(v.get("authority", {}), "selection")
    return v


def verify_manifest(value: dict[str, Any] | None = None) -> dict[str, Any]:
    v = _signed(value or _a("source_manifest"), "manifest_fingerprint", E["manifest"], "manifest")
    profile = v.get("structural_profile", {})
    if v.get("selection_fingerprint") != E["selection"] or v.get("selected_pr_count") != 8:
        raise ProofEngineError("manifest binding mismatch")
    if [x.get("number") for x in v.get("selected_merged_prs", [])] != PRS:
        raise ProofEngineError("manifest PR mismatch")
    if len(profile.get("implementation_layers", [])) != 7 or profile.get("generated_reviewable_outputs") != 6:
        raise ProofEngineError("manifest profile mismatch")
    if profile.get("runtime_external_api_calls") is not False or profile.get("runtime_publication") is not False or profile.get("human_review_required") is not True:
        raise ProofEngineError("manifest safety mismatch")
    _false(v.get("authority", {}), "manifest")
    return v


def verify_report(value: dict[str, Any] | None = None) -> dict[str, Any]:
    v = _signed(value or _a("report_json"), "report_fingerprint", E["report"], "report")
    sections = v.get("sections", {})
    if v.get("source_manifest_fingerprint") != E["manifest"] or list(sections) != REQUIRED_SECTIONS:
        raise ProofEngineError("report binding or section mismatch")
    records = sections.get("effective_achievement_records", [])
    if [x.get("candidate_id") for x in records] != [f"AGE-00{i}" for i in range(1, 7)]:
        raise ProofEngineError("record set mismatch")
    for record in records:
        m = copy.deepcopy(record)
        actual = m.pop("achievement_record_fingerprint", None)
        if fingerprint(m) != actual or not set(record.get("evidence_prs", [])) <= set(PRS) or not record.get("evidence_prs"):
            raise ProofEngineError("record evidence mismatch")
    withheld = sections.get("withheld_or_unsupported_claims", [])
    if [x.get("topic") for x in withheld] != WITHHELD or any(x.get("status") != "WITHHELD_UNSUPPORTED" for x in withheld):
        raise ProofEngineError("withheld claims mismatch")
    decision = sections.get("human_review_decision", {})
    if decision.get("decision") != "ACCEPT_THIRD_CASE_GENERALIZATION" or decision.get("external_human_review_performed") is not False or decision.get("customer_review_performed") is not False:
        raise ProofEngineError("review boundary mismatch")
    _false(v.get("authority", {}), "report")
    _false(decision.get("authority", {}), "decision")
    return v


def verify_markdown(value: str | None = None) -> str:
    v = _a("report_markdown") if value is None else value
    required = ["## Verified now", "## Not verified", "## Allowed now", "## Not allowed now", "RUN_ID_COLLISION_RESISTANCE", "INTERNAL_THREE_CASE_GENERALIZATION_VALIDATED"]
    forbidden = ["READY_FOR_PRODUCTION_SERVICE", "READY_FOR_CUSTOMER_PILOT", "ARBITRARY_REPOSITORY_GENERALIZATION_VALIDATED"]
    if fingerprint(v) != E["markdown"] or any(x not in v for x in required) or any(x in v for x in forbidden):
        raise ProofEngineError("reader Markdown boundary mismatch")
    return v


def verify_inventory(value: dict[str, Any] | None = None) -> dict[str, Any]:
    v = _signed(value or _a("evidence_inventory"), "inventory_fingerprint", E["inventory"], "inventory")
    if v.get("source_manifest_fingerprint") != E["manifest"] or v.get("effective_record_count") != 6 or v.get("withheld_claim_count") != 5:
        raise ProofEngineError("inventory count mismatch")
    if v.get("selected_pr_numbers") != PRS or v.get("excluded_pr_numbers") != [66, 67]:
        raise ProofEngineError("inventory PR mismatch")
    return v


def verify_comparison(value: dict[str, Any] | None = None) -> dict[str, Any]:
    v = _signed(value or _a("three_case_comparison"), "comparison_fingerprint", E["comparison"], "comparison")
    rows = v.get("rows", [])
    if v.get("dimension_count") != 12 or len(rows) != 12 or any(not str(x.get("result", "")).startswith("PASS") for x in rows):
        raise ProofEngineError("comparison failed")
    if v.get("overall") != "PASS_BOUNDED_THREE_CASE_GENERALIZATION" or v.get("not_proven") != "ARBITRARY_REPOSITORY_GENERALIZATION":
        raise ProofEngineError("generalization boundary mismatch")
    return v


def verify_acceptance(value: dict[str, Any] | None = None) -> dict[str, Any]:
    v = _signed(value or _a("acceptance_packet"), "packet_fingerprint", E["acceptance"], "acceptance")
    criteria = v.get("criteria_results", [])
    if [x.get("criterion_id") for x in criteria] != [f"GEN-{i:03d}" for i in range(1, 15)]:
        raise ProofEngineError("acceptance criteria mismatch")
    if any(x.get("result") != "PASS" or not x.get("evidence") or not x.get("note") for x in criteria):
        raise ProofEngineError("acceptance failed")
    if v.get("decision") != "ACCEPT_THIRD_CASE_GENERALIZATION" or v.get("external_human_review_performed") is not False or v.get("customer_review_performed") is not False:
        raise ProofEngineError("acceptance boundary mismatch")
    _false(v.get("authority", {}), "acceptance")
    return v


def verify_verification_summary(value: dict[str, Any] | None = None) -> dict[str, Any]:
    v = _signed(value or _a("verification_summary"), "verification_fingerprint", E["verification"], "verification")
    if v.get("pass_count") != 14 or len(v.get("checks", [])) != 14:
        raise ProofEngineError("verification count mismatch")
    if v.get("double_build_match") is not True or v.get("prior_builder_files_unchanged") is not True:
        raise ProofEngineError("determinism/reuse mismatch")
    if v.get("repository_specific_conditionals") is not False or v.get("external_actions_performed") is not False:
        raise ProofEngineError("verification boundary widened")
    return v


def verify_rollback(value: dict[str, Any] | None = None) -> dict[str, Any]:
    v = _signed(value or _a("rollback_index"), "rollback_index_fingerprint", E["rollback"], "rollback")
    if (v.get("artifact_count"), v.get("indexed_artifact_count"), v.get("self_record_is_eighth_artifact")) != (8, 7, True):
        raise ProofEngineError("rollback artifact mismatch")
    policy = v.get("rollback_policy", {})
    if any(policy.get(k) is not False for k in ("delete_or_rewrite_prior_records", "modify_source_repository", "modify_target_repository", "external_actions_allowed")):
        raise ProofEngineError("rollback boundary widened")
    return v


def verify_speed_baseline(value: dict[str, Any] | None = None) -> dict[str, Any]:
    v = _signed(value or load(SPEED), "baseline_fingerprint", E["speed"], "speed")
    expected = {"sample_count": 4, "changed_files": 51, "additions": 3486, "commits": 66, "total_pr_gate_seconds": 3373, "median_pr_gate_seconds": 415.5, "total_sequential_stage_seconds": 6857, "median_sequential_stage_seconds": 1469.0, "largest_observed_stage_seconds": 2624}
    if v.get("aggregate") != expected or v.get("measurement_policy", {}).get("claim_boundary") != "Observed internal session baseline, not an SLA or guarantee.":
        raise ProofEngineError("speed baseline mismatch")
    level = v.get("level_assessment", {})
    if level.get("level") != "HIGH_VELOCITY_GOVERNED_SOLO_AI_DEVELOPMENT" or len(level.get("limitations", [])) != 3:
        raise ProofEngineError("speed level mismatch")
    return v


def verify_result(value: dict[str, Any] | None = None) -> dict[str, Any]:
    v = _signed(value or _a("hardening_execution_result"), "result_fingerprint", E["result"], "result")
    done = v.get("completed_work_item", {})
    progress = v.get("completion_update", {})
    if done.get("work_id") != "HARD-004" or done.get("result") != "PASS_INTERNAL" or len(done.get("acceptance_results", [])) != 6 or any(x.get("result") != "PASS" for x in done.get("acceptance_results", [])):
        raise ProofEngineError("HARD-004 completion mismatch")
    if (progress.get("rts_overall_planning_estimate_percent"), progress.get("short_term_internal_product_candidate_percent"), progress.get("product_readiness_baseline_score_unchanged")) != (75, 99, 82):
        raise ProofEngineError("HARD-004 progress mismatch")
    if v.get("state") != "INTERNAL_THREE_CASE_GENERALIZATION_VALIDATED" or v.get("next_gate") != "HUMAN_PRIVACY_AND_OPERATING_METRICS_EXECUTION_REVIEW_REQUIRED" or v.get("remaining_work_items") != ["HARD-005"]:
        raise ProofEngineError("HARD-004 terminal mismatch")
    if v.get("authority", {}).get("bounded_internal_third_case_authorized") is not True:
        raise ProofEngineError("HARD-004 authority missing")
    _false(v.get("authority", {}), "result")
    return v


def verify_progress_map(value: dict[str, Any] | None = None) -> dict[str, Any]:
    v = _signed(value or load(STATUS), "map_fingerprint", E["status"], "progress")
    axes = v.get("final_shape", {}).get("axes", [])
    current = v.get("current_position", {})
    if sum(x.get("score", -1) for x in axes) != 75 or sum(x.get("maximum", -1) for x in axes) != 100:
        raise ProofEngineError("overall progress mismatch")
    if current.get("short_term_completion_percent") != 99 or current.get("current_step") != "HARD-005" or current.get("completed") != ["HARD-001", "HARD-002", "HARD-003", "HARD-004"]:
        raise ProofEngineError("current position mismatch")
    if current.get("development_speed_baseline_fingerprint") != E["speed"] or current.get("observed_median_sequential_stage_seconds") != 1469.0:
        raise ProofEngineError("speed progress binding mismatch")
    _false(v.get("authority", {}), "progress")
    return v


def verify_checkpoint(value: dict[str, Any] | None = None) -> dict[str, Any]:
    v = _signed(value or load(CHECKPOINT), "checkpoint_fingerprint", E["checkpoint"], "checkpoint")
    bindings = {"case_selection_fingerprint": "selection", "source_manifest_fingerprint": "manifest", "report_fingerprint": "report", "report_markdown_fingerprint": "markdown", "inventory_fingerprint": "inventory", "comparison_fingerprint": "comparison", "acceptance_packet_fingerprint": "acceptance", "verification_fingerprint": "verification", "rollback_index_fingerprint": "rollback", "development_speed_baseline_fingerprint": "speed", "hardening_execution_result_fingerprint": "result", "progress_map_fingerprint": "status"}
    if any(v.get(field) != E[key] for field, key in bindings.items()):
        raise ProofEngineError("checkpoint binding mismatch")
    if any(v[k] is not False for k in v if k.endswith("_performed")):
        raise ProofEngineError("checkpoint external action")
    return v


def build_third_case_package_bindings() -> dict[str, str]:
    verify_prior_builder_unchanged()
    verify_selection(); verify_manifest(); verify_report(); verify_markdown()
    verify_inventory(); verify_comparison(); verify_acceptance(); verify_verification_summary(); verify_rollback()
    return {"source_manifest": E["manifest"], "report_json": E["report"], "report_markdown": E["markdown"], "evidence_inventory": E["inventory"], "three_case_comparison": E["comparison"], "acceptance_packet": E["acceptance"], "verification_summary": E["verification"], "rollback_index": E["rollback"]}


def verify_third_case_generalization_stage() -> dict[str, Any]:
    bundle = verify_bundle()
    first = build_third_case_package_bindings()
    if first != build_third_case_package_bindings():
        raise ProofEngineError("double-build mismatch")
    speed, result, progress, checkpoint = verify_speed_baseline(), verify_result(), verify_progress_map(), verify_checkpoint()
    expected_outputs = {"case_selection_fingerprint": E["selection"], "source_manifest_fingerprint": E["manifest"], "report_fingerprint": E["report"], "report_markdown_fingerprint": E["markdown"], "inventory_fingerprint": E["inventory"], "comparison_fingerprint": E["comparison"], "acceptance_packet_fingerprint": E["acceptance"], "verification_fingerprint": E["verification"], "rollback_index_fingerprint": E["rollback"], "development_speed_baseline_fingerprint": E["speed"]}
    if result["completed_work_item"]["outputs"] != expected_outputs:
        raise ProofEngineError("HARD-004 output binding mismatch")
    return {"bundle": bundle, "package_bindings": first, "speed": speed, "result": result, "progress": progress, "checkpoint": checkpoint, "summary": {"state": result["state"], "next_gate": result["next_gate"], "rts_overall_planning_estimate_percent": 75, "short_term_internal_product_candidate_percent": 99, "product_readiness_baseline_score": 82, "current_step": "HARD-005", "third_case_repository": "nobutakayamauchi/RTS-AGE", "selected_pr_count": 8, "effective_record_count": 6, "withheld_claim_count": 5, "package_artifact_count": 8, "comparison_dimension_count": 12, "development_speed_level": speed["level_assessment"]["level"], "median_pr_gate_seconds": speed["aggregate"]["median_pr_gate_seconds"], "median_sequential_stage_seconds": speed["aggregate"]["median_sequential_stage_seconds"], "speed_is_sla": False, "remaining_work_items": ["HARD-005"]}}

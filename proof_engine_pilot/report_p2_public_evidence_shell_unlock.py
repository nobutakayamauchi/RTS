from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
ROUND = "proof_engine_pilot/product_readiness/round_0011"
ARTIFACTS = {
    "contract": (f"{ROUND}/p2_public_shell_unlock_contract.json", "contract_fingerprint"),
    "binding": (f"{ROUND}/approved_p3_output_binding.json", "binding_fingerprint"),
    "inventory": (f"{ROUND}/public_surface_inventory.json", "inventory_fingerprint"),
    "policy": (f"{ROUND}/disclosure_policy.json", "policy_fingerprint"),
    "architecture": (f"{ROUND}/public_shell_information_architecture.json", "architecture_fingerprint"),
    "decision": (f"{ROUND}/p2_unlock_decision.json", "decision_fingerprint"),
    "score": (f"{ROUND}/readiness_score_hold.json", "score_hold_fingerprint"),
    "completion": (f"{ROUND}/p2_public_shell_plan_completion.json", "completion_fingerprint"),
}
POSITION_PATH = "docs/status/RTS_CURRENT_POSITION_P2_PUBLIC_SHELL_PLAN.json"
CHECKPOINT_PATH = "pilot_runs/reconnect_pilot_p3/p2_public_evidence_shell_unlock_checkpoint_0032.json"
PROPOSED_PUBLIC_SHELL_PATH = "docs/public/RTS_PUBLIC_EVIDENCE_SHELL.md"
PRIOR_POSITION_PATH = "docs/status/RTS_CURRENT_POSITION_OUTREACH_WAITING.json"
PRIOR_COMPLETION_PATH = "proof_engine_pilot/product_readiness/round_0010/outreach_waiting_completion.json"
PRIOR_CHECKPOINT_PATH = "pilot_runs/reconnect_pilot_p3/evidence_report_customer_pilot_outreach_waiting_checkpoint_0031.json"

SOURCE_BLOB_CHECKS = {
    "README.md": "bb0c915879a76cd9de6c21fd3f11eb1c4f2220e5",
    "docs/overview/POSITION.md": "9f8f7be578b450fb39a3ae597a319bd5b88a0b47",
    "docs/portfolio/RTS_EVIDENCE_BACKED_PROJECT_OUTPUTS.md": "c6fa8e3d165b053143f1a179914c0a9879f29867",
    "pilot_runs/reconnect_pilot_p1/MASTER_PRODUCT_SPECIFICATION_V1.md": "99687bf1456dde3c9fbb14461d73cdd8d7ea5da3",
    "pilot_runs/reconnect_pilot_p1/FUTURE_BRANCH_UNLOCK_TRIGGERS_V1.md": "3aaf0d4608c73bdd64d83f06aa5e1773ed8cf773",
    "pilot_run_contract/packs/reconnect_seed_pack_v1/scope_profiles.json": "dd786d3768f8b84de5b1c63bca3164fed6c6cd24",
    "proof_engine_pilot/releases/round_0001/release_authorization.json": "379e20ee936e800bc8405f2fcfc5324e84bbd16a",
    "pilot_runs/reconnect_pilot_p3/publication_release_checkpoint_0008.json": "a320fbf96037ce0ea0dd751bac450ab88f552d3f",
    PRIOR_POSITION_PATH: "974b4385f589c16d59e8b093187fc6b3b1b91f8b",
    PRIOR_COMPLETION_PATH: "8a6209ec59498ccad5382068f12e746463777c16",
    PRIOR_CHECKPOINT_PATH: "a91eb0ca358a806d29da0b287b8b45d8563e017d",
}
EXPECTED_AUTHORITY = {
    "additional_outreach_authorized": False,
    "analysis_authorized": False,
    "contract_authorized": False,
    "customer_intake_authorized": False,
    "customer_pilot_execution_authorized": False,
    "delivery_authorized": False,
    "external_execution_authorized": False,
    "internal_disclosure_policy_review_authorized": True,
    "internal_p2_unlock_assessment_authorized": True,
    "p2_public_shell_build_authorized": False,
    "pricing_authorized": False,
    "publication_authorized": False,
    "root_readme_promotion_authorized": False,
    "social_posting_authorized": False,
    "source_repository_write_authorized": False,
    "target_repository_write_authorized": False,
}
SECTION_IDS = [
    "PROJECT_OVERVIEW",
    "CURRENT_BUILD_SCOPE",
    "DEVELOPMENT_EVIDENCE_LOG",
    "CASE_001_DEVELOPER_TRANSPARENCY",
    "CONTACT_AND_OPPORTUNITY_ENTRY",
]


class P2PublicShellError(RuntimeError):
    pass


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def fingerprint(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def path(relative: str) -> Path:
    return ROOT / relative


def load(relative: str) -> dict:
    try:
        value = json.loads(path(relative).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise P2PublicShellError(f"invalid or missing JSON: {relative}") from exc
    if not isinstance(value, dict):
        raise P2PublicShellError(f"JSON root must be object: {relative}")
    return value


def verify_fingerprint(value: dict, field: str, label: str) -> str:
    material = copy.deepcopy(value)
    actual = material.pop(field, None)
    if actual != fingerprint(material):
        raise P2PublicShellError(f"{label} fingerprint mismatch")
    return actual


def artifact(name: str) -> dict:
    relative, field = ARTIFACTS[name]
    value = load(relative)
    verify_fingerprint(value, field, name)
    return value


def reject(condition: bool, message: str) -> None:
    if condition:
        raise P2PublicShellError(message)


def verify_bound_sources() -> dict:
    for relative, expected in SOURCE_BLOB_CHECKS.items():
        try:
            data = path(relative).read_bytes()
        except FileNotFoundError as exc:
            raise P2PublicShellError(f"missing bound source: {relative}") from exc
        reject(git_blob_sha(data) != expected, f"bound source drift: {relative}")
    reject(path(PROPOSED_PUBLIC_SHELL_PATH).exists(), "public shell created without build authorization")
    return {"bound_source_count": len(SOURCE_BLOB_CHECKS), "planned_surface_absent": True}


def verify_prior_wait_state() -> dict:
    position = load(PRIOR_POSITION_PATH)
    completion = load(PRIOR_COMPLETION_PATH)
    checkpoint = load(PRIOR_CHECKPOINT_PATH)
    verify_fingerprint(position, "map_fingerprint", "prior position")
    verify_fingerprint(completion, "completion_fingerprint", "prior completion")
    verify_fingerprint(checkpoint, "checkpoint_fingerprint", "prior checkpoint")
    current = position.get("current_position", {})
    reject(position["map_fingerprint"] != "3104e170b73c647845b9790ce3e81415cdfd5f86b864784da3d3052af3059108", "prior position substitution")
    reject(current.get("current_state") != "HUMAN_ATTESTED_ONE_TIME_OUTREACH_RECORDED", "external wait state changed")
    reject(current.get("wait_window_expiry_local") != "2026-08-12T15:48:19+09:00", "external wait expiry changed")
    reject((current.get("message_send_event_count"), current.get("response_event_count"), current.get("follow_up_event_count")) != (1, 0, 0), "external event counts changed")
    reject(completion["completion_fingerprint"] != "2f4b1a01513cd8cf8a33f217006e43a110114db76439f683ca974d5142b60d13", "prior completion substitution")
    reject(checkpoint["checkpoint_fingerprint"] != "dbf892c1398703fd904a0992d22899a483ba5d703b9a214e7b417e3331558f0a", "prior checkpoint substitution")
    reject(completion.get("response_event_count") != 0 or checkpoint.get("response_event_count") != 0, "response manufactured")
    reject(checkpoint.get("follow_up_performed") is not False, "follow-up manufactured")
    return {"position_fingerprint": position["map_fingerprint"], "completion_fingerprint": completion["completion_fingerprint"], "checkpoint_fingerprint": checkpoint["checkpoint_fingerprint"]}


def verify_contract() -> dict:
    value = artifact("contract")
    reject(value.get("authority") != EXPECTED_AUTHORITY, "contract authority changed")
    reject(value.get("selected_branch") != "P2_PUBLIC_EVIDENCE_SHELL", "wrong selected branch")
    provenance = value.get("instruction_provenance", {})
    reject(provenance.get("raw_instruction_stored") is not False, "raw instruction stored")
    reject(provenance.get("raw_instruction_sha256") != "599cf0d8e1cc79a3ea4c364062d2c9e5a5ace95503b0276cbfa557e9d25e1b05", "raw instruction binding changed")
    reject(provenance.get("normalized_instruction_sha256") != "7dbf69e0eaa24e081c2a2310ec5d11f889a95f113ef20971c8805287d8b5dda0", "normalized instruction binding changed")
    boundary = value.get("operating_boundary", {})
    reject(boundary.get("active_external_wait_preserved") is not True or boundary.get("wip_limit") != 1, "operating boundary changed")
    for field in ["new_public_document_creation_authorized", "public_release_authorized", "root_readme_change_authorized", "contact_entry_activation_authorized"]:
        reject(boundary.get(field) is not False, f"contract widened: {field}")
    prior = verify_prior_wait_state()
    bound = value.get("prior_state", {})
    for field, key in [("outreach_waiting_position_fingerprint", "position_fingerprint"), ("outreach_waiting_completion_fingerprint", "completion_fingerprint"), ("outreach_waiting_checkpoint_fingerprint", "checkpoint_fingerprint")]:
        reject(bound.get(field) != prior[key], f"contract prior linkage changed: {field}")
    return value


def verify_binding() -> dict:
    value = artifact("binding")
    reject(value.get("contract_fingerprint") != verify_contract()["contract_fingerprint"], "binding/contract mismatch")
    expected = {
        "document_path": "docs/portfolio/RTS_EVIDENCE_BACKED_PROJECT_OUTPUTS.md",
        "document_blob_sha": "c6fa8e3d165b053143f1a179914c0a9879f29867",
        "document_fingerprint": "682ec3d73373ea2228c4d270b5ca74bec8c59050781e7322dbfcfba1c9b50369",
        "effective_output_count": 6,
        "publication_state": "PUBLISHED_TO_AUTHORIZED_REPOSITORY_DOCUMENT",
    }
    reject(value.get("approved_output") != expected, "approved P3 output changed")
    reject(value.get("unlock_criterion_result") != "PASS", "P3 output unlock failed")
    release = load("proof_engine_pilot/releases/round_0001/release_authorization.json")
    checkpoint = load("pilot_runs/reconnect_pilot_p3/publication_release_checkpoint_0008.json")
    verify_fingerprint(release, "authorization_fingerprint", "release authorization")
    verify_fingerprint(checkpoint, "checkpoint_fingerprint", "release checkpoint")
    reject(release["authorization_fingerprint"] != value["release_authorization"]["fingerprint"], "release authorization mismatch")
    reject(checkpoint["checkpoint_fingerprint"] != value["release_checkpoint"]["fingerprint"], "release checkpoint mismatch")
    reject(release.get("release_surface", {}).get("root_readme_link_authorized") is not False, "historical README promotion authorized")
    reject(any(checkpoint.get(x) is not False for x in ["root_readme_promotion_performed", "social_posting_performed", "direct_outreach_performed"]), "historical release scope widened")
    return value


def verify_inventory() -> dict:
    value = artifact("inventory")
    reject(value.get("contract_fingerprint") != verify_contract()["contract_fingerprint"], "inventory/contract mismatch")
    reject(value.get("binding_fingerprint") != verify_binding()["binding_fingerprint"], "inventory/binding mismatch")
    reject(value.get("result") != "INTEGRATE_EXISTING_ASSETS_DO_NOT_REBUILD_FROM_ZERO", "inventory result changed")
    expected_paths = ["README.md", "docs/overview/POSITION.md", "docs/portfolio/RTS_EVIDENCE_BACKED_PROJECT_OUTPUTS.md", PRIOR_POSITION_PATH]
    surfaces = value.get("surfaces")
    reject(not isinstance(surfaces, list) or [x.get("path") for x in surfaces] != expected_paths, "surface inventory changed")
    reject(any(x.get("change_in_this_stage") is not False for x in surfaces), "source surface changed")
    exclusions = canonical_json(value.get("private_or_contextual_material_excluded", []))
    for item in ["private DM", "response status", "credentials", "sensitive personal"]:
        reject(item not in exclusions, f"inventory exclusion missing: {item}")
    return value


def verify_policy() -> dict:
    value = artifact("policy")
    reject(value.get("contract_fingerprint") != verify_contract()["contract_fingerprint"], "policy/contract mismatch")
    reject(value.get("authority") != EXPECTED_AUTHORITY, "policy authority changed")
    reject(value.get("state") != "ACCEPTED_AS_MANDATORY_INTERNAL_P2_BUILD_CONSTRAINT", "policy state changed")
    reject(value.get("unlock_criterion_result") != "PASS_FOR_INTERNAL_BUILD_PLANNING_ONLY", "policy unlock scope changed")
    required_gates = {
        "new_public_document_requires_separate_human_authorization": True,
        "root_readme_link_requires_separate_human_authorization": True,
        "active_contact_entry_requires_separate_human_authorization": True,
        "social_or_external_surface_requires_separate_human_authorization": True,
        "content_fingerprint_required_before_release": True,
    }
    reject(value.get("release_gates") != required_gates, "release gates weakened")
    permitted = canonical_json(value.get("permitted_content", []))
    for item in ["private messages", "credentials", "sensitive personal", "active sales promises"]:
        reject(item in permitted, f"prohibited material permitted: {item}")
    prohibited = canonical_json(value.get("prohibited_content", []))
    for item in ["private messages", "recipient response status", "credentials", "sensitive personal", "raw prompts", "unsupported production", "human ranking", "active sales promises", "automatic publication"]:
        reject(item not in prohibited, f"policy prohibition missing: {item}")
    reject(value.get("review_attribution", {}).get("public_release_decision") != "NOT_MADE", "release decision manufactured")
    reject("jbexta" in canonical_json(value) or "Discord" in canonical_json(value), "contact context leaked into policy")
    return value


def verify_architecture() -> dict:
    value = artifact("architecture")
    reject(value.get("contract_fingerprint") != verify_contract()["contract_fingerprint"], "architecture/contract mismatch")
    reject(value.get("disclosure_policy_fingerprint") != verify_policy()["policy_fingerprint"], "architecture/policy mismatch")
    expected_surface = {"path": PROPOSED_PUBLIC_SHELL_PATH, "status": "PLANNED_NOT_CREATED", "visibility_if_later_authorized": "PUBLIC_REPOSITORY_DOCUMENT", "root_readme_link_status": "NOT_AUTHORIZED", "active_contact_route_status": "INACTIVE_NOT_AUTHORIZED"}
    reject(value.get("proposed_surface") != expected_surface, "proposed surface changed")
    sections = value.get("sections")
    reject(not isinstance(sections, list) or [x.get("id") for x in sections] != SECTION_IDS, "section architecture changed")
    reject(sections[-1].get("current_state") != "INACTIVE_PLACEHOLDER_ONLY" or sections[-1].get("activation_requires") != "SEPARATE_HUMAN_AUTHORIZATION", "contact entry activated")
    reject(value.get("stage_result") != "P2_BUILD_BLUEPRINT_COMPLETE_NO_SURFACE_CREATED", "architecture stage widened")
    text = canonical_json(value)
    for item in ["Discord DM", "2026-08-12T15:48:19", "private message body"]:
        reject(item in text, "response-wait detail leaked into architecture")
    return value


def verify_decision() -> dict:
    value = artifact("decision")
    expected_links = {
        "contract_fingerprint": verify_contract()["contract_fingerprint"],
        "binding_fingerprint": verify_binding()["binding_fingerprint"],
        "inventory_fingerprint": verify_inventory()["inventory_fingerprint"],
        "disclosure_policy_fingerprint": verify_policy()["policy_fingerprint"],
        "architecture_fingerprint": verify_architecture()["architecture_fingerprint"],
    }
    for field, expected in expected_links.items():
        reject(value.get(field) != expected, f"decision linkage mismatch: {field}")
    reject(value.get("decision") != "UNLOCK_P2_FOR_SEPARATE_INTERNAL_BUILD_REVIEW", "unlock decision changed")
    reject(value.get("p2_state") != "UNLOCKED_NOT_STARTED", "P2 started without authorization")
    for field in ["public_shell_build_authorized", "public_shell_document_created", "publication_authorized", "release_authorized", "root_readme_change_authorized", "active_contact_entry_authorized"]:
        reject(value.get(field) is not False, f"decision widened: {field}")
    reject(value.get("next_gate") != "HUMAN_P2_PUBLIC_SHELL_BUILD_AUTHORIZATION_REQUIRED", "decision gate changed")
    return value


def verify_score_hold() -> dict:
    value = artifact("score")
    reject(value.get("architecture_fingerprint") != verify_architecture()["architecture_fingerprint"], "score/architecture mismatch")
    reject(value.get("decision_fingerprint") != verify_decision()["decision_fingerprint"], "score/decision mismatch")
    reject((value.get("product_readiness_score"), value.get("product_readiness_score_change")) != (93, 0), "product readiness inflated")
    reject((value.get("rts_overall_planning_estimate_percent"), value.get("rts_overall_planning_estimate_change")) != (82, 1), "RTS score changed")
    return value


def verify_completion() -> dict:
    value = artifact("completion")
    expected = {
        "approved_p3_output_binding": verify_binding()["binding_fingerprint"],
        "public_surface_inventory": verify_inventory()["inventory_fingerprint"],
        "disclosure_policy": verify_policy()["policy_fingerprint"],
        "information_architecture": verify_architecture()["architecture_fingerprint"],
        "unlock_decision": verify_decision()["decision_fingerprint"],
        "readiness_score_hold": verify_score_hold()["score_hold_fingerprint"],
    }
    reject(value.get("artifact_fingerprints") != expected, "completion linkage changed")
    reject(value.get("authority") != EXPECTED_AUTHORITY, "completion authority changed")
    reject(value.get("state") != "INTERNAL_P2_PUBLIC_EVIDENCE_SHELL_UNLOCK_AND_PLAN_COMPLETE", "completion state changed")
    reject(value.get("p2_state") != "UNLOCKED_NOT_STARTED", "completion starts P2")
    reject(value.get("next_gate") != "HUMAN_P2_PUBLIC_SHELL_BUILD_AUTHORIZATION_REQUIRED", "completion gate changed")
    reject(value.get("external_wait_state") != "HUMAN_ATTESTED_ONE_TIME_OUTREACH_RECORDED" or value.get("external_wait_next_gate") != "HUMAN_RESPONSE_EVENT_OR_NO_RESPONSE_WINDOW_EXPIRY_REQUIRED", "external wait changed")
    for field in ["new_public_document_created", "publication_performed", "root_readme_promotion_performed", "active_contact_entry_performed", "additional_outreach_performed", "customer_intake_performed", "analysis_performed"]:
        reject(value.get(field) is not False, f"completion widened: {field}")
    reject((value.get("product_readiness_score"), value.get("rts_overall_planning_estimate_percent")) != (93, 82), "completion score changed")
    results = value.get("acceptance_results")
    reject(not isinstance(results, list) or [x.get("criterion_id") for x in results] != [f"P2U-{i:02d}" for i in range(1, 11)] or any(x.get("result") != "PASS" for x in results), "acceptance set changed")
    return value


def verify_progress() -> dict:
    value = load(POSITION_PATH)
    verify_fingerprint(value, "map_fingerprint", "current position")
    reject(value.get("authority") != EXPECTED_AUTHORITY, "position authority changed")
    current = value.get("current_position", {})
    expected = {
        "active_contact_entry_performed": False,
        "current_state": "INTERNAL_P2_PUBLIC_EVIDENCE_SHELL_UNLOCK_AND_PLAN_COMPLETE",
        "current_step": "P2_PUBLIC_EVIDENCE_SHELL_BUILD_AUTHORIZATION",
        "external_response_wait_preserved": True,
        "external_wait_next_gate": "HUMAN_RESPONSE_EVENT_OR_NO_RESPONSE_WINDOW_EXPIRY_REQUIRED",
        "external_wait_state": "HUMAN_ATTESTED_ONE_TIME_OUTREACH_RECORDED",
        "external_wait_expiry_local": "2026-08-12T15:48:19+09:00",
        "follow_up_authorized": False,
        "historical_approved_public_output_count": 6,
        "historical_bounded_repository_publication_performed": True,
        "new_public_document_created": False,
        "next_gate": "HUMAN_P2_PUBLIC_SHELL_BUILD_AUTHORIZATION_REQUIRED",
        "p2_disclosure_policy_state": "ACCEPTED_AS_MANDATORY_INTERNAL_P2_BUILD_CONSTRAINT",
        "p2_information_architecture_complete": True,
        "p2_public_shell_build_authorized": False,
        "p2_public_shell_state": "UNLOCKED_NOT_STARTED",
        "product_readiness_score": 93,
        "publication_authorized": False,
        "root_readme_promotion_performed": False,
        "rts_overall_planning_estimate_percent": 82,
        "short_term_internal_hardening_percent": 100,
    }
    reject(current != expected, "current position changed")
    axes = value.get("final_shape", {}).get("axes")
    reject(not isinstance(axes, list) or [x.get("score") for x in axes] != [25, 18, 16, 23], "progress axes changed")
    reject(verify_completion()["rts_overall_planning_estimate_percent"] != 82, "completion/progress mismatch")
    return value


def verify_checkpoint() -> dict:
    value = load(CHECKPOINT_PATH)
    verify_fingerprint(value, "checkpoint_fingerprint", "checkpoint")
    exact = {
        "state": "INTERNAL_P2_PUBLIC_EVIDENCE_SHELL_UNLOCK_AND_PLAN_COMPLETE",
        "next_gate": "HUMAN_P2_PUBLIC_SHELL_BUILD_AUTHORIZATION_REQUIRED",
        "p2_state": "UNLOCKED_NOT_STARTED",
        "new_public_document_created": False,
        "p2_public_shell_build_performed": False,
        "publication_performed": False,
        "root_readme_promotion_performed": False,
        "active_contact_entry_performed": False,
        "social_posting_performed": False,
        "additional_outreach_performed": False,
        "customer_intake_performed": False,
        "analysis_performed": False,
        "pilot_execution_performed": False,
        "pricing_performed": False,
        "contract_action_performed": False,
        "delivery_performed": False,
        "external_execution_performed": False,
        "source_or_target_repository_writes_performed": False,
        "historical_bounded_repository_publication_performed": True,
        "external_wait_state": "HUMAN_ATTESTED_ONE_TIME_OUTREACH_RECORDED",
        "external_wait_next_gate": "HUMAN_RESPONSE_EVENT_OR_NO_RESPONSE_WINDOW_EXPIRY_REQUIRED",
        "product_readiness_score": 93,
        "rts_overall_planning_estimate_percent": 82,
        "short_term_internal_hardening_percent": 100,
    }
    for field, expected in exact.items():
        reject(value.get(field) != expected, f"checkpoint changed: {field}")
    links = {
        "contract_fingerprint": verify_contract()["contract_fingerprint"],
        "approved_p3_output_binding_fingerprint": verify_binding()["binding_fingerprint"],
        "inventory_fingerprint": verify_inventory()["inventory_fingerprint"],
        "disclosure_policy_fingerprint": verify_policy()["policy_fingerprint"],
        "information_architecture_fingerprint": verify_architecture()["architecture_fingerprint"],
        "architecture_fingerprint": verify_architecture()["architecture_fingerprint"],
        "unlock_decision_fingerprint": verify_decision()["decision_fingerprint"],
        "readiness_score_hold_fingerprint": verify_score_hold()["score_hold_fingerprint"],
        "completion_fingerprint": verify_completion()["completion_fingerprint"],
        "progress_map_fingerprint": verify_progress()["map_fingerprint"],
        "prior_outreach_waiting_position_fingerprint": "3104e170b73c647845b9790ce3e81415cdfd5f86b864784da3d3052af3059108",
        "prior_outreach_waiting_completion_fingerprint": "2f4b1a01513cd8cf8a33f217006e43a110114db76439f683ca974d5142b60d13",
        "prior_outreach_waiting_checkpoint_fingerprint": "dbf892c1398703fd904a0992d22899a483ba5d703b9a214e7b417e3331558f0a",
    }
    for field, expected in links.items():
        reject(value.get(field) != expected, f"checkpoint linkage changed: {field}")
    allowed = set(exact) | set(links) | {"checkpoint_id", "checkpoint_fingerprint", "schema_version"}
    reject(set(value) != allowed, "checkpoint unknown or missing fields")
    return value


def verify_all() -> dict:
    verify_bound_sources()
    contract = verify_contract()
    binding = verify_binding()
    inventory = verify_inventory()
    policy = verify_policy()
    architecture = verify_architecture()
    decision = verify_decision()
    score = verify_score_hold()
    completion = verify_completion()
    progress = verify_progress()
    checkpoint = verify_checkpoint()
    return {
        "state": completion["state"],
        "next_gate": completion["next_gate"],
        "rts_overall_planning_estimate_percent": 82,
        "short_term_internal_hardening_percent": 100,
        "product_readiness_score": 93,
        "p2_state": completion["p2_state"],
        "approved_p3_output_count": binding["approved_output"]["effective_output_count"],
        "planned_section_count": len(architecture["sections"]),
        "new_public_document_created": False,
        "publication_performed": False,
        "root_readme_promotion_performed": False,
        "active_contact_entry_performed": False,
        "external_wait_state": completion["external_wait_state"],
        "external_wait_next_gate": completion["external_wait_next_gate"],
        "contract_fingerprint": contract["contract_fingerprint"],
        "inventory_fingerprint": inventory["inventory_fingerprint"],
        "disclosure_policy_fingerprint": policy["policy_fingerprint"],
        "architecture_fingerprint": architecture["architecture_fingerprint"],
        "decision_fingerprint": decision["decision_fingerprint"],
        "score_hold_fingerprint": score["score_hold_fingerprint"],
        "completion_fingerprint": completion["completion_fingerprint"],
        "progress_map_fingerprint": progress["map_fingerprint"],
        "checkpoint_fingerprint": checkpoint["checkpoint_fingerprint"],
    }


def required_paths() -> list[str]:
    values = [relative for relative, _ in ARTIFACTS.values()]
    values += [POSITION_PATH, CHECKPOINT_PATH, PRIOR_POSITION_PATH, PRIOR_COMPLETION_PATH, PRIOR_CHECKPOINT_PATH]
    values += list(SOURCE_BLOB_CHECKS)
    return sorted(set(values))

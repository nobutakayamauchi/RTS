from __future__ import annotations

import copy
import re
from pathlib import Path
from typing import Any

from .core import ProofEngineError, fingerprint, load, verify_run
from .review import (
    APPROVED_ORIGINAL_IDS,
    DECISION_INDEX_PATH,
    REVISED_IDS,
    REVISIONS_PATH,
    load_decision_chain,
    verify_review_round,
)

PACKAGE_DIR = Path(__file__).resolve().parent
ROOT = PACKAGE_DIR.parent
DATA_DIR = PACKAGE_DIR / "learning_data" / "round_0001"
DATASET_PATH = DATA_DIR / "dataset.json"
RULESET_PATH = DATA_DIR / "ruleset.json"
REPLAY_PATH = DATA_DIR / "replay.json"
POLICY_PATH = DATA_DIR / "policy_state.json"
CHECKPOINT_PATH = ROOT / "pilot_runs" / "reconnect_pilot_p3" / "learning_checkpoint_0003.json"

REQUIRED_FIELDS = {
    "candidate_id", "claim", "record_kind", "factuality_note", "contribution_map",
    "evidence_label", "evidence_prs", "public_disclosure",
}
ALLOWED_KINDS = {
    "PERSONAL_ACHIEVEMENT", "PROJECT_OUTPUT", "PROCESS_BYPRODUCT",
    "INTEGRATION_BYPRODUCT", "AUDIT_REMEDIATION_BYPRODUCT", "REUSABILITY_SIGNAL",
}
AUTHORITY_FALSE = {
    "automatic_approval_authorized": False,
    "automatic_rewrite_authorized": False,
    "publication_authorized": False,
}
STRONG_PREFIX = re.compile(
    r"^(built|created|designed and implemented|implemented|integrated|resolved|established|decomposed)\b",
    re.IGNORECASE,
)


def _verify_fingerprint(value: dict[str, Any], field: str, label: str) -> str:
    material = copy.deepcopy(value)
    actual = material.pop(field, None)
    if actual != fingerprint(material):
        raise ProofEngineError(f"{label} fingerprint mismatch")
    return actual


def verify_dataset(dataset: dict[str, Any]) -> dict[str, Any]:
    _verify_fingerprint(dataset, "dataset_fingerprint", "learning dataset")
    review = verify_review_round()
    base = verify_run()
    revisions = load(REVISIONS_PATH)
    index = load(DECISION_INDEX_PATH)
    decisions = load_decision_chain(index)
    base_by_id = {item["candidate_id"]: item for item in base["candidates"]}
    revision_by_id = {item["candidate_id"]: item for item in revisions["revisions"]}
    decision_by_key = {
        (item["target"]["candidate_id"], item["target"]["candidate_version"], item["decision_type"]): item
        for item in decisions
    }

    expected_sources = {
        "base_run": base["run_fingerprint"],
        "revision_ledger": revisions["revisions_fingerprint"],
        "decision_index": index["decision_index_fingerprint"],
        "review_summary": review["summary_fingerprint"],
    }
    if dataset.get("source_fingerprints") != expected_sources:
        raise ProofEngineError("learning dataset source links mismatch")
    boundary = dataset.get("usage_boundary")
    if not isinstance(boundary, dict) or boundary.get("mode") != "REPOSITORY_LOCAL_RULE_LEARNING":
        raise ProofEngineError("learning dataset usage boundary mismatch")
    for field in (
        "model_weight_training_authorized", "automatic_rewrite_authorized",
        "automatic_approval_authorized", "publication_authorized",
    ):
        if boundary.get(field) is not False:
            raise ProofEngineError(f"learning dataset authority widened: {field}")

    positives = dataset.get("positive_examples")
    if not isinstance(positives, list) or len(positives) != 7:
        raise ProofEngineError("learning dataset positive-example count mismatch")
    seen_positive = set()
    for item in positives:
        cid = item.get("candidate_id")
        if cid not in APPROVED_ORIGINAL_IDS or cid in seen_positive:
            raise ProofEngineError("learning dataset positive example mismatch")
        seen_positive.add(cid)
        candidate = base_by_id[cid]
        decision = decision_by_key[(cid, 1, "APPROVE")]
        if item.get("candidate_fingerprint") != candidate["candidate_fingerprint"]:
            raise ProofEngineError("positive example candidate mismatch")
        if item.get("decision_fingerprint") != decision["decision_fingerprint"]:
            raise ProofEngineError("positive example decision mismatch")
        if item.get("expected_action") != "APPROVE" or item.get("error_labels") != []:
            raise ProofEngineError("positive example label mismatch")
    if seen_positive != APPROVED_ORIGINAL_IDS:
        raise ProofEngineError("positive example set incomplete")

    pairs = dataset.get("correction_pairs")
    if not isinstance(pairs, list) or len(pairs) != 5:
        raise ProofEngineError("learning dataset correction-pair count mismatch")
    seen_revised = set()
    for pair in pairs:
        cid = pair.get("candidate_id")
        if cid not in REVISED_IDS or cid in seen_revised:
            raise ProofEngineError("learning dataset correction pair mismatch")
        seen_revised.add(cid)
        original = base_by_id[cid]
        revision = revision_by_id[cid]
        revise = decision_by_key[(cid, 1, "REVISE")]
        approve = decision_by_key[(cid, 2, "APPROVE")]
        checks = {
            "original_fingerprint": original["candidate_fingerprint"],
            "original_claim": original["claim"],
            "revise_decision_fingerprint": revise["decision_fingerprint"],
            "revision_fingerprint": revision["candidate_fingerprint"],
            "revision_id": revision["revision_id"],
            "revised_claim": revision["claim"],
            "record_kind": revision["record_kind"],
            "factuality_note": revision["factuality_note"],
            "approval_decision_fingerprint": approve["decision_fingerprint"],
        }
        for field, expected in checks.items():
            if pair.get(field) != expected:
                raise ProofEngineError(f"learning correction link mismatch: {cid}/{field}")
        if not pair.get("error_labels"):
            raise ProofEngineError("learning correction has no error labels")
    if seen_revised != REVISED_IDS:
        raise ProofEngineError("learning correction set incomplete")

    if dataset.get("counts") != {
        "positive_examples": 7,
        "correction_pairs": 5,
        "human_decisions_represented": 17,
    }:
        raise ProofEngineError("learning dataset counts mismatch")
    return dataset


def verify_ruleset(ruleset: dict[str, Any], dataset: dict[str, Any]) -> dict[str, Any]:
    _verify_fingerprint(ruleset, "ruleset_fingerprint", "learning ruleset")
    if ruleset.get("dataset_fingerprint") != dataset["dataset_fingerprint"]:
        raise ProofEngineError("learning ruleset/dataset mismatch")
    activation = ruleset.get("activation", {})
    if activation != {
        "state": "ACTIVE_FOR_FUTURE_RUNS",
        "mode": "SUGGEST_ONLY",
        "applies_after_run_id": "PROOF-ENGINE-P3-RUN-0001",
        "retroactive_mutation": False,
    }:
        raise ProofEngineError("learning ruleset activation mismatch")
    if set(ruleset.get("required_future_candidate_fields", [])) != REQUIRED_FIELDS:
        raise ProofEngineError("learning ruleset required fields mismatch")
    if set(ruleset.get("allowed_record_kinds", [])) != ALLOWED_KINDS:
        raise ProofEngineError("learning ruleset record kinds mismatch")
    rules = ruleset.get("rules")
    if not isinstance(rules, list) or len(rules) != 6:
        raise ProofEngineError("learning ruleset rule count mismatch")
    if any(rule.get("state") != "ACTIVE" or rule.get("automatic_application_authorized") is not False for rule in rules):
        raise ProofEngineError("learning rule authority widened")
    authority = ruleset.get("authority", {})
    if authority != {**AUTHORITY_FALSE, "model_weight_training_authorized": False}:
        raise ProofEngineError("learning ruleset authority mismatch")
    return ruleset


def verify_learning_bundle(checkpoint: dict[str, Any] | None = None) -> dict[str, Any]:
    dataset = verify_dataset(load(DATASET_PATH))
    ruleset = verify_ruleset(load(RULESET_PATH), dataset)

    replay = load(REPLAY_PATH)
    _verify_fingerprint(replay, "replay_fingerprint", "learning replay")
    if replay.get("dataset_fingerprint") != dataset["dataset_fingerprint"] or replay.get("ruleset_fingerprint") != ruleset["ruleset_fingerprint"]:
        raise ProofEngineError("learning replay link mismatch")
    if replay.get("result") != "PASS_LEARNING_DATA_REFLECTED":
        raise ProofEngineError("learning replay result mismatch")
    if replay.get("counts") != {
        "positive_examples_preserved": 7,
        "corrections_learned": 5,
        "revisions_accepted": 5,
        "unresolved_examples": 0,
    }:
        raise ProofEngineError("learning replay counts mismatch")
    if replay.get("future_policy", {}).get("base_run_mutated") is not False:
        raise ProofEngineError("learning replay mutated base run")

    policy = load(POLICY_PATH)
    _verify_fingerprint(policy, "policy_fingerprint", "learning policy")
    if policy.get("active_dataset_fingerprint") != dataset["dataset_fingerprint"]:
        raise ProofEngineError("learning policy dataset mismatch")
    if policy.get("active_ruleset_fingerprint") != ruleset["ruleset_fingerprint"]:
        raise ProofEngineError("learning policy ruleset mismatch")
    if policy.get("latest_replay_fingerprint") != replay["replay_fingerprint"]:
        raise ProofEngineError("learning policy replay mismatch")
    if policy.get("state") != "ACTIVE_FOR_FUTURE_RUNS" or policy.get("mode") != "SUGGEST_ONLY":
        raise ProofEngineError("learning policy activation mismatch")
    if policy.get("original_records_preserved") is not True or policy.get("model_weight_update_performed") is not False:
        raise ProofEngineError("learning policy preservation mismatch")
    if policy.get("authority") != {**AUTHORITY_FALSE, "external_execution_authorized": False}:
        raise ProofEngineError("learning policy authority mismatch")

    checkpoint = load(CHECKPOINT_PATH) if checkpoint is None else checkpoint
    _verify_fingerprint(checkpoint, "checkpoint_fingerprint", "learning checkpoint")
    links = {
        "dataset_fingerprint": dataset["dataset_fingerprint"],
        "ruleset_fingerprint": ruleset["ruleset_fingerprint"],
        "replay_fingerprint": replay["replay_fingerprint"],
        "policy_fingerprint": policy["policy_fingerprint"],
    }
    for field, expected in links.items():
        if checkpoint.get(field) != expected:
            raise ProofEngineError(f"learning checkpoint mismatch: {field}")
    if checkpoint.get("state") != "LEARNING_DATA_ACTIVE_SUGGEST_ONLY":
        raise ProofEngineError("learning checkpoint state mismatch")
    if checkpoint.get("original_records_preserved") is not True or checkpoint.get("model_weight_update_performed") is not False:
        raise ProofEngineError("learning checkpoint preservation mismatch")
    if checkpoint.get("external_actions_performed") is not False:
        raise ProofEngineError("learning checkpoint records an unauthorized external action")
    return {"dataset": dataset, "ruleset": ruleset, "replay": replay, "policy": policy, "checkpoint": checkpoint}


def preflight_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    issues = []
    missing = sorted(REQUIRED_FIELDS - set(candidate))
    if missing:
        issues.append({"rule_id": "REVIEW-RULE-002", "code": "MISSING_LEARNING_FIELDS", "detail": ", ".join(missing)})

    candidate_id = candidate.get("candidate_id")
    if "candidate_id" in candidate and (not isinstance(candidate_id, str) or not candidate_id.strip()):
        issues.append({"rule_id": "REVIEW-RULE-002", "code": "INVALID_CANDIDATE_ID", "detail": "candidate_id must be a non-empty string."})

    claim = candidate.get("claim")
    if "claim" in candidate and (not isinstance(claim, str) or not claim.strip()):
        issues.append({"rule_id": "REVIEW-RULE-001", "code": "INVALID_CLAIM", "detail": "claim must be a non-empty string."})

    kind = candidate.get("record_kind")
    if kind is not None and kind not in ALLOWED_KINDS:
        issues.append({"rule_id": "REVIEW-RULE-002", "code": "UNKNOWN_RECORD_KIND", "detail": str(kind)})

    contribution = candidate.get("contribution_map", {})
    ai_work = contribution.get("ai_tool") if isinstance(contribution, dict) else None
    if isinstance(claim, str) and ai_work and STRONG_PREFIX.search(claim.strip()):
        issues.append({"rule_id": "REVIEW-RULE-001", "code": "DIRECT_AUTHORSHIP_REQUIRES_REVIEW", "detail": "Strong direct-action wording is combined with material AI-tool contribution; bound the claim itself to the observed result and supported human actions."})

    lower = claim.lower() if isinstance(claim, str) else ""
    if any(term in lower for term in ("reusable", "repeatable", "future projects", "across projects")):
        if candidate.get("record_kind") != "REUSABILITY_SIGNAL" or candidate.get("evidence_label") != "INFERRED":
            issues.append({"rule_id": "REVIEW-RULE-004", "code": "GENERALIZATION_EXCEEDS_EVIDENCE", "detail": "Cross-project reuse remains an INFERRED REUSABILITY_SIGNAL until externally observed."})

    disclosure = candidate.get("public_disclosure")
    if disclosure is not None and disclosure not in {"INTERNAL_UNTIL_APPROVED", "INTERNAL_UNTIL_SEPARATE_PUBLICATION_APPROVAL"}:
        issues.append({"rule_id": "REVIEW-RULE-006", "code": "PUBLICATION_BOUNDARY_NOT_EXPLICIT", "detail": "Candidate approval must not imply publication authority."})

    return {
        "schema_version": "PROOF-ENGINE-LEARNING-PREFLIGHT-V1",
        "candidate_id": candidate_id,
        "mode": "SUGGEST_ONLY",
        "result": "SUGGEST_REVIEW" if issues else "PASS",
        "issues": issues,
        "authority": {"automatic_rewrite_authorized": False, "automatic_approval_authorized": False},
    }

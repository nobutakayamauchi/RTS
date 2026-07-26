from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

PACKAGE_DIR = Path(__file__).resolve().parent
REPOSITORY_ROOT = PACKAGE_DIR.parent
SOURCE_PATH = PACKAGE_DIR / "source" / "prs_242_261.json"
CONFIG_PATH = PACKAGE_DIR / "config" / "candidate_blueprints.json"
RUN_PATH = PACKAGE_DIR / "runs" / "p3_run_0001.json"
BUILD_DECISION_PATH = REPOSITORY_ROOT / "pilot_runs" / "reconnect_pilot_p3" / "HUMAN_BUILD_DECISION_0001.json"
PILOT_RECORD_PATH = REPOSITORY_ROOT / "pilot_runs" / "reconnect_pilot_p3" / "run_record.json"

ALLOWED_EVIDENCE = {"VERIFIED", "INFERRED", "SELF_REPORTED", "UNVERIFIED", "CONFLICTED"}
EXPECTED_AUTHORITY_FIELDS = {
    "adjacent_repository_write_authorized",
    "automatic_approval_authorized",
    "contract_authorized",
    "external_execution_authorized",
    "outreach_authorized",
    "provider_authorized",
    "publication_authorized",
}
EXPECTED_ALL_PR_NUMBERS = set(range(242, 262))
EXPECTED_ELIGIBLE_PR_NUMBERS = EXPECTED_ALL_PR_NUMBERS - {251}


class ProofEngineError(RuntimeError):
    pass


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def fingerprint(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise ProofEngineError(f"invalid or missing JSON: {path}") from exc
    if not isinstance(value, dict):
        raise ProofEngineError("JSON root must be an object")
    return value


def _verify_fingerprint(value: dict, field: str, label: str) -> str:
    material = copy.deepcopy(value)
    actual = material.pop(field, None)
    if actual != fingerprint(material):
        raise ProofEngineError(f"{label} fingerprint mismatch")
    return actual


def eligible_pr_numbers(source: dict) -> set[int]:
    return {
        item["number"]
        for item in source["prs"]
        if item.get("merged") is True and item.get("status") == "MERGED"
    }


def verify_source(source: dict) -> dict:
    _verify_fingerprint(source, "source_fingerprint", "source")
    if source.get("repository") != "nobutakayamauchi/RTS" or source.get("visibility") != "PUBLIC":
        raise ProofEngineError("source boundary widened")
    prs = source.get("prs")
    if not isinstance(prs, list):
        raise ProofEngineError("source PRs must be a list")
    numbers = [item.get("number") for item in prs]
    if len(numbers) != len(set(numbers)) or set(numbers) != EXPECTED_ALL_PR_NUMBERS:
        raise ProofEngineError("source PR range mismatch")
    for item in prs:
        if item["number"] == 251:
            if item.get("merged") is not False or item.get("status") != "SUPERSEDED":
                raise ProofEngineError("PR 251 must remain superseded and ineligible")
        elif item.get("merged") is not True or item.get("status") != "MERGED":
            raise ProofEngineError("unexpected unmerged PR in source range")
    if eligible_pr_numbers(source) != EXPECTED_ELIGIBLE_PR_NUMBERS:
        raise ProofEngineError("eligible source PR set mismatch")
    return source


def verify_config(config: dict, eligible_prs: set[int]) -> dict:
    _verify_fingerprint(config, "config_fingerprint", "config")
    if config.get("schema_version") != "PROOF-ENGINE-CANDIDATE-CONFIG-V1":
        raise ProofEngineError("candidate config schema mismatch")
    candidates = config.get("candidates")
    if not isinstance(candidates, list) or len(candidates) < 10:
        raise ProofEngineError("candidate config requires at least ten blueprints")
    ids: set[str] = set()
    for candidate in candidates:
        cid = candidate.get("candidate_id")
        if not isinstance(cid, str) or cid in ids:
            raise ProofEngineError("duplicate or invalid candidate blueprint ID")
        ids.add(cid)
        if "candidate_fingerprint" in candidate:
            raise ProofEngineError("candidate blueprint must not contain output fingerprint")
        refs = candidate.get("evidence_prs")
        if not refs or not set(refs) <= eligible_prs:
            raise ProofEngineError("candidate blueprint evidence escapes source boundary")
    return config


def verify_build_decision(decision: dict, source: dict) -> dict:
    _verify_fingerprint(decision, "decision_fingerprint", "build decision")
    if decision.get("decision") != "APPROVE_P3_BUILD" or decision.get("status") != "APPROVED":
        raise ProofEngineError("P3 build decision is not approved")
    boundary = decision.get("source_boundary")
    expected = {
        "prs": [242, 261],
        "repository": source["repository"],
        "snapshot_ref": source["snapshot_ref"],
    }
    if boundary != expected:
        raise ProofEngineError("build decision/source boundary mismatch")
    return decision


def generate_run() -> dict:
    source = verify_source(load(SOURCE_PATH))
    eligible_prs = eligible_pr_numbers(source)
    config = verify_config(load(CONFIG_PATH), eligible_prs)
    verify_build_decision(load(BUILD_DECISION_PATH), source)

    candidates: list[dict] = []
    for blueprint in config["candidates"]:
        candidate = copy.deepcopy(blueprint)
        candidate["candidate_fingerprint"] = fingerprint(candidate)
        candidates.append(candidate)

    run = {
        "authority": {field: False for field in sorted(EXPECTED_AUTHORITY_FIELDS)},
        "candidate_count": len(candidates),
        "candidates": candidates,
        "next_action": "Human reviews the 12 candidates and records approve, revise, reject, redact, or expire decisions.",
        "output_asset": {
            "publication_status": "NOT_PUBLISHED",
            "reason": "No candidate has a human approval decision.",
            "source_candidate_ids": [],
            "state": "BLOCKED",
        },
        "result": "PASS_CANDIDATES_READY",
        "review_queue": {
            "allowed_decisions": ["APPROVE", "REVISE", "REJECT", "REDACT", "EXPIRE"],
            "decisions": [],
            "state": "HUMAN_REVIEW_REQUIRED",
        },
        "run_id": "PROOF-ENGINE-P3-RUN-0001",
        "schema_version": "PROOF-ENGINE-P3-RUN-V1",
        "source_fingerprint": source["source_fingerprint"],
        "source_set_id": source["source_set_id"],
    }
    run["run_fingerprint"] = fingerprint(run)
    return run


def _verify_candidate(candidate: dict, eligible_prs: set[int], ids: set[str]) -> None:
    cid = candidate.get("candidate_id")
    if not isinstance(cid, str) or cid in ids:
        raise ProofEngineError("duplicate or invalid candidate ID")
    ids.add(cid)
    _verify_fingerprint(candidate, "candidate_fingerprint", f"candidate {cid}")
    if candidate.get("evidence_label") not in ALLOWED_EVIDENCE:
        raise ProofEngineError("unknown evidence label")
    refs = candidate.get("evidence_prs")
    if not refs or not set(refs) <= eligible_prs:
        raise ProofEngineError("candidate evidence escapes source boundary")
    if candidate.get("status") != "REVIEW_REQUIRED":
        raise ProofEngineError("candidate status must remain REVIEW_REQUIRED")


def verify_pilot_record(record: dict, decision: dict, source: dict, run: dict) -> dict:
    _verify_fingerprint(record, "record_fingerprint", "pilot record")
    if record.get("decision_fingerprint") != decision["decision_fingerprint"]:
        raise ProofEngineError("pilot record/build decision mismatch")
    if record.get("source_fingerprint") != source["source_fingerprint"]:
        raise ProofEngineError("pilot record/source mismatch")
    if record.get("proof_engine_run_fingerprint") != run["run_fingerprint"]:
        raise ProofEngineError("pilot record/run mismatch")
    if record.get("candidate_count") != run["candidate_count"]:
        raise ProofEngineError("pilot record candidate count mismatch")
    if record.get("state") != "HUMAN_REVIEW_REQUIRED" or record.get("external_actions_performed") is not False:
        raise ProofEngineError("pilot record authority widened")
    return record


def verify_run(run: dict | None = None) -> dict:
    source = verify_source(load(SOURCE_PATH))
    eligible_prs = eligible_pr_numbers(source)
    verify_config(load(CONFIG_PATH), eligible_prs)
    decision = verify_build_decision(load(BUILD_DECISION_PATH), source)
    run = load(RUN_PATH) if run is None else run

    _verify_fingerprint(run, "run_fingerprint", "run")
    if run.get("source_fingerprint") != source["source_fingerprint"]:
        raise ProofEngineError("source drift")

    authority = run.get("authority")
    if not isinstance(authority, dict) or set(authority) != EXPECTED_AUTHORITY_FIELDS:
        raise ProofEngineError("authority fields missing or unknown")
    for field in EXPECTED_AUTHORITY_FIELDS:
        if authority[field] is not False:
            raise ProofEngineError(f"authority widened: {field}")

    candidates = run.get("candidates")
    if not isinstance(candidates, list) or len(candidates) < 10:
        raise ProofEngineError("at least ten candidates required")
    if run.get("candidate_count") != len(candidates):
        raise ProofEngineError("candidate count mismatch")
    ids: set[str] = set()
    for candidate in candidates:
        _verify_candidate(candidate, eligible_prs, ids)

    review = run.get("review_queue", {})
    if review.get("state") != "HUMAN_REVIEW_REQUIRED" or review.get("decisions") != []:
        raise ProofEngineError("human decisions were manufactured")
    output = run.get("output_asset", {})
    if output.get("state") != "BLOCKED" or output.get("publication_status") != "NOT_PUBLISHED":
        raise ProofEngineError("output authority widened")

    if run != generate_run():
        raise ProofEngineError("run does not match deterministic source/config generation")

    verify_pilot_record(load(PILOT_RECORD_PATH), decision, source, run)
    return run

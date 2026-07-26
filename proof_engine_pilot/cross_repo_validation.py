from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

from .core import ProofEngineError, fingerprint, load
from .learning import preflight_candidate, verify_learning_bundle

PACKAGE_DIR = Path(__file__).resolve().parent
ROOT = PACKAGE_DIR.parent
DATA_DIR = PACKAGE_DIR / "cross_repo" / "campaign_0001"
CAMPAIGN_PATH = DATA_DIR / "campaign.json"
MANIFEST_PATH = DATA_DIR / "manifest.json"
CHECKPOINT_PATH = ROOT / "pilot_runs" / "reconnect_pilot_p3" / "cross_repo_validation_checkpoint_0009.json"

CAMPAIGN_SCHEMA = "PROOF-ENGINE-CROSS-REPO-CAMPAIGN-V1"
RUN_SCHEMA = "PROOF-ENGINE-CROSS-REPO-RUN-V1"
MANIFEST_SCHEMA = "PROOF-ENGINE-CROSS-REPO-MANIFEST-V1"
CHECKPOINT_SCHEMA = "PROOF-ENGINE-CROSS-REPO-CHECKPOINT-V1"
ROUND_ORDER = ["ROUND-2", "ROUND-3", "ROUND-4"]
ALLOWED_DECISIONS = ["APPROVE", "REVISE", "REJECT", "REDACT", "EXPIRE"]
AUTHORITY_FIELDS = {
    "adjacent_repository_write_authorized",
    "automatic_approval_authorized",
    "automatic_rewrite_authorized",
    "contract_authorized",
    "external_execution_authorized",
    "model_weight_training_authorized",
    "outreach_authorized",
    "provider_execution_authorized",
    "publication_authorized",
    "target_repository_write_authorized",
}
ROUND_SPECS = {
    "ROUND-2": {
        "repository": "nobutakayamauchi/seminar-compass",
        "visibility": "PUBLIC",
        "role": "GENERALIZATION_TEST",
        "source_mode": "READ_ONLY_SNAPSHOT",
        "readme_blob_sha": "7741b49d7c33c4b229de8f71a591ea96cdb70503",
        "pr_numbers": {12, 13, 14, 15, 16, 17, 18, 19, 28},
        "eligible_prs": {12, 13, 14, 15, 16, 19, 28},
        "candidate_count": 6,
        "withheld_count": 0,
    },
    "ROUND-3": {
        "repository": "nobutakayamauchi/RTS-minicompany",
        "visibility": "PRIVATE",
        "role": "PRIVATE_BUSINESS_REPOSITORY_TEST",
        "source_mode": "READ_ONLY_METADATA_SNAPSHOT",
        "readme_blob_sha": "c04bfd012176ee9fe16158b8e5990e2fd1608205",
        "pr_numbers": {92, 93, 95, 97, 99, 101, 103, 105, 107, 109},
        "eligible_prs": {92, 93, 95, 97, 99, 101, 103, 105, 107, 109},
        "candidate_count": 8,
        "withheld_count": 2,
    },
    "ROUND-4": {
        "repository": "nobutakayamauchi/rts-video-flow",
        "visibility": "PUBLIC",
        "role": "NEGATIVE_CONTROL",
        "source_mode": "READ_ONLY_SNAPSHOT",
        "readme_blob_sha": "bf1dc0f75da08202c2a07dced5d0885b43fac5b5",
        "pr_numbers": {1, 2},
        "eligible_prs": {1, 2},
        "candidate_count": 2,
        "withheld_count": 3,
    },
}
CHECKPOINT_FIELDS = {
    "schema_version",
    "checkpoint_id",
    "campaign_fingerprint",
    "run_fingerprint",
    "manifest_fingerprint",
    "completed_rounds",
    "candidate_count",
    "state",
    "publication_performed",
    "external_actions_performed",
    "target_repository_writes_performed",
    "private_repository_payload_copied",
    "original_source_repositories_modified",
    "next_action",
    "checkpoint_fingerprint",
}


def _verify_fingerprint(value: dict[str, Any], field: str, label: str) -> str:
    material = copy.deepcopy(value)
    actual = material.pop(field, None)
    if actual != fingerprint(material):
        raise ProofEngineError(f"{label} fingerprint mismatch")
    return actual


def _verify_false_authority(value: Any, label: str) -> dict[str, bool]:
    if not isinstance(value, dict) or set(value) != AUTHORITY_FIELDS:
        raise ProofEngineError(f"{label} authority fields mismatch")
    if any(value[field] is not False for field in AUTHORITY_FIELDS):
        raise ProofEngineError(f"{label} authority widened")
    return value


def _eligible_prs(round_value: dict[str, Any]) -> set[int]:
    return {
        item["number"]
        for item in round_value["selected_prs"]
        if item.get("merged") is True and item.get("status") == "MERGED"
    }


def verify_campaign(campaign: dict[str, Any] | None = None) -> dict[str, Any]:
    value = load(CAMPAIGN_PATH) if campaign is None else copy.deepcopy(campaign)
    _verify_fingerprint(value, "campaign_fingerprint", "cross-repo campaign")
    if value.get("schema_version") != CAMPAIGN_SCHEMA or value.get("campaign_id") != "PROOF-ENGINE-CROSS-REPO-CAMPAIGN-0001":
        raise ProofEngineError("cross-repo campaign identity mismatch")
    if value.get("execution_order") != ROUND_ORDER:
        raise ProofEngineError("cross-repo campaign order mismatch")
    _verify_false_authority(value.get("authority"), "campaign")
    learning = value.get("learning_policy")
    if learning != {
        "ruleset_id": "PROOF-ENGINE-LEARNING-RULESET-0001",
        "mode": "SUGGEST_ONLY",
        "automatic_rewrite_authorized": False,
        "automatic_approval_authorized": False,
    }:
        raise ProofEngineError("cross-repo learning policy mismatch")
    verify_learning_bundle()

    rounds = value.get("rounds")
    if not isinstance(rounds, list) or [item.get("round_id") for item in rounds] != ROUND_ORDER:
        raise ProofEngineError("cross-repo campaign rounds mismatch")
    candidate_ids: set[str] = set()
    for round_value in rounds:
        round_id = round_value["round_id"]
        spec = ROUND_SPECS[round_id]
        for field in ("repository", "visibility", "role", "source_mode", "readme_blob_sha"):
            if round_value.get(field) != spec[field]:
                raise ProofEngineError(f"{round_id} source boundary mismatch: {field}")
        if round_value.get("snapshot_ref") != "main":
            raise ProofEngineError(f"{round_id} snapshot ref mismatch")
        prs = round_value.get("selected_prs")
        if not isinstance(prs, list):
            raise ProofEngineError(f"{round_id} PR source must be a list")
        numbers = [item.get("number") for item in prs]
        if len(numbers) != len(set(numbers)) or set(numbers) != spec["pr_numbers"]:
            raise ProofEngineError(f"{round_id} PR set mismatch")
        eligible = _eligible_prs(round_value)
        if eligible != spec["eligible_prs"]:
            raise ProofEngineError(f"{round_id} eligible PR set mismatch")
        for item in prs:
            number = item["number"]
            if number in eligible:
                if item.get("merged") is not True or item.get("status") != "MERGED":
                    raise ProofEngineError(f"{round_id} merged PR state mismatch")
            elif item.get("merged") is not False or item.get("status") != "NOT_MERGED":
                raise ProofEngineError(f"{round_id} unmerged PR state mismatch")

        candidates = round_value.get("candidates")
        if not isinstance(candidates, list) or len(candidates) != spec["candidate_count"]:
            raise ProofEngineError(f"{round_id} candidate blueprint count mismatch")
        for candidate in candidates:
            candidate_id = candidate.get("candidate_id")
            if not isinstance(candidate_id, str) or candidate_id in candidate_ids:
                raise ProofEngineError("cross-repo candidate ID mismatch")
            candidate_ids.add(candidate_id)
            if candidate.get("round_id") != round_id or candidate.get("repository") != spec["repository"]:
                raise ProofEngineError(f"{candidate_id} round or repository mismatch")
            if "candidate_fingerprint" in candidate:
                raise ProofEngineError(f"{candidate_id} blueprint contains output fingerprint")
            refs = candidate.get("evidence_prs")
            if not refs or not set(refs) <= eligible:
                raise ProofEngineError(f"{candidate_id} evidence includes unmerged or out-of-scope PR")
            if candidate.get("status") != "REVIEW_REQUIRED":
                raise ProofEngineError(f"{candidate_id} status mismatch")
            if preflight_candidate(candidate).get("result") != "PASS":
                raise ProofEngineError(f"{candidate_id} failed active learning preflight")
        withheld = round_value.get("withheld_claims")
        if not isinstance(withheld, list) or len(withheld) != spec["withheld_count"]:
            raise ProofEngineError(f"{round_id} withheld-claim count mismatch")
        for item in withheld:
            if not isinstance(item.get("claim"), str) or not item["claim"].strip() or not isinstance(item.get("reason"), str) or not item["reason"].strip():
                raise ProofEngineError(f"{round_id} invalid withheld claim")
        if round_id == "ROUND-3" and round_value.get("source_mode") != "READ_ONLY_METADATA_SNAPSHOT":
            raise ProofEngineError("private repository payload boundary widened")
    return value


def generate_run(campaign: dict[str, Any] | None = None) -> dict[str, Any]:
    source = verify_campaign(campaign)
    run_rounds = []
    total = 0
    for round_value in source["rounds"]:
        eligible = _eligible_prs(round_value)
        excluded = set(ROUND_SPECS[round_value["round_id"]]["pr_numbers"]) - eligible
        candidates = []
        for blueprint in round_value["candidates"]:
            candidate = copy.deepcopy(blueprint)
            candidate["candidate_fingerprint"] = fingerprint(candidate)
            candidates.append(candidate)
        total += len(candidates)
        generated = {
            "round_id": round_value["round_id"],
            "repository": round_value["repository"],
            "role": round_value["role"],
            "visibility": round_value["visibility"],
            "source_mode": round_value["source_mode"],
            "readme_blob_sha": round_value["readme_blob_sha"],
            "selected_pr_count": len(round_value["selected_prs"]),
            "eligible_merged_prs": sorted(eligible),
            "excluded_unmerged_prs": sorted(excluded),
            "candidate_count": len(candidates),
            "candidates": candidates,
            "withheld_claims": copy.deepcopy(round_value["withheld_claims"]),
            "review_state": "HUMAN_REVIEW_REQUIRED",
            "publication_status": "NOT_PUBLISHED",
            "target_repository_write_performed": False,
        }
        generated["round_fingerprint"] = fingerprint(generated)
        run_rounds.append(generated)

    run = {
        "schema_version": RUN_SCHEMA,
        "run_id": "PROOF-ENGINE-CROSS-REPO-RUN-0001",
        "campaign_fingerprint": source["campaign_fingerprint"],
        "execution_order": ROUND_ORDER,
        "authority": {field: False for field in sorted(AUTHORITY_FIELDS)},
        "rounds": run_rounds,
        "comparison": {
            "candidate_count_by_round": {item["round_id"]: item["candidate_count"] for item in run_rounds},
            "excluded_unmerged_pr_count_by_round": {item["round_id"]: len(item["excluded_unmerged_prs"]) for item in run_rounds},
            "withheld_claim_count_by_round": {item["round_id"]: len(item["withheld_claims"]) for item in run_rounds},
            "learning_effectiveness_state": "HUMAN_REVIEW_REQUIRED",
            "reason": "Candidate generation and learning preflight can be measured now; improvement in human approval or revision rate requires the next human review round.",
        },
        "candidate_count": total,
        "result": "PASS_THREE_REPOSITORY_CANDIDATES_READY",
        "review_queue": {"state": "HUMAN_REVIEW_REQUIRED", "allowed_decisions": ALLOWED_DECISIONS, "decisions": []},
        "publication_status": "NOT_PUBLISHED",
        "external_actions_performed": False,
        "target_repository_writes_performed": False,
        "next_action": "Human reviews Round 2, Round 3, and Round 4 candidates in order and records corrections for the next learning dataset.",
    }
    run["run_fingerprint"] = fingerprint(run)
    return run


def verify_run(run: dict[str, Any] | None = None) -> dict[str, Any]:
    campaign = verify_campaign()
    value = generate_run(campaign) if run is None else copy.deepcopy(run)
    _verify_fingerprint(value, "run_fingerprint", "cross-repo run")
    if value.get("schema_version") != RUN_SCHEMA or value.get("run_id") != "PROOF-ENGINE-CROSS-REPO-RUN-0001":
        raise ProofEngineError("cross-repo run identity mismatch")
    if value.get("campaign_fingerprint") != campaign["campaign_fingerprint"] or value.get("execution_order") != ROUND_ORDER:
        raise ProofEngineError("cross-repo run source mismatch")
    _verify_false_authority(value.get("authority"), "run")
    if value.get("candidate_count") != 16:
        raise ProofEngineError("cross-repo total candidate count mismatch")
    if value.get("result") != "PASS_THREE_REPOSITORY_CANDIDATES_READY":
        raise ProofEngineError("cross-repo run result mismatch")
    review = value.get("review_queue", {})
    if review != {"state": "HUMAN_REVIEW_REQUIRED", "allowed_decisions": ALLOWED_DECISIONS, "decisions": []}:
        raise ProofEngineError("cross-repo human decisions were manufactured")
    if value.get("publication_status") != "NOT_PUBLISHED" or value.get("external_actions_performed") is not False or value.get("target_repository_writes_performed") is not False:
        raise ProofEngineError("cross-repo run authority widened")
    if value.get("comparison", {}).get("learning_effectiveness_state") != "HUMAN_REVIEW_REQUIRED":
        raise ProofEngineError("cross-repo run overclaims learning effectiveness")
    if value != generate_run(campaign):
        raise ProofEngineError("cross-repo run does not match deterministic campaign generation")
    return value


def verify_bundle(
    *,
    run: dict[str, Any] | None = None,
    checkpoint: dict[str, Any] | None = None,
) -> dict[str, Any]:
    generated = verify_run(run)
    manifest = load(MANIFEST_PATH)
    _verify_fingerprint(manifest, "manifest_fingerprint", "cross-repo manifest")
    if manifest.get("schema_version") != MANIFEST_SCHEMA or manifest.get("manifest_id") != "PROOF-ENGINE-CROSS-REPO-MANIFEST-0001":
        raise ProofEngineError("cross-repo manifest identity mismatch")
    if manifest.get("campaign_fingerprint") != generated["campaign_fingerprint"] or manifest.get("expected_run_fingerprint") != generated["run_fingerprint"]:
        raise ProofEngineError("cross-repo manifest run link mismatch")
    if manifest.get("expected_round_fingerprints") != {item["round_id"]: item["round_fingerprint"] for item in generated["rounds"]}:
        raise ProofEngineError("cross-repo manifest round links mismatch")
    if manifest.get("expected_candidate_count") != 16 or manifest.get("expected_round_order") != ROUND_ORDER:
        raise ProofEngineError("cross-repo manifest counts mismatch")
    if manifest.get("terminal_state") != "HUMAN_REVIEW_REQUIRED" or manifest.get("publication_status") != "NOT_PUBLISHED":
        raise ProofEngineError("cross-repo manifest authority widened")

    cp = load(CHECKPOINT_PATH) if checkpoint is None else copy.deepcopy(checkpoint)
    if set(cp) != CHECKPOINT_FIELDS:
        raise ProofEngineError("cross-repo checkpoint schema fields mismatch")
    _verify_fingerprint(cp, "checkpoint_fingerprint", "cross-repo checkpoint")
    if cp.get("schema_version") != CHECKPOINT_SCHEMA or cp.get("checkpoint_id") != "PROOF-ENGINE-CROSS-REPO-CHECKPOINT-0009":
        raise ProofEngineError("cross-repo checkpoint identity mismatch")
    links = {
        "campaign_fingerprint": generated["campaign_fingerprint"],
        "run_fingerprint": generated["run_fingerprint"],
        "manifest_fingerprint": manifest["manifest_fingerprint"],
    }
    for field, expected in links.items():
        if cp.get(field) != expected:
            raise ProofEngineError(f"cross-repo checkpoint link mismatch: {field}")
    if cp.get("completed_rounds") != ROUND_ORDER or cp.get("candidate_count") != 16:
        raise ProofEngineError("cross-repo checkpoint counts mismatch")
    if cp.get("state") != "THREE_REPOSITORY_HUMAN_REVIEW_REQUIRED":
        raise ProofEngineError("cross-repo checkpoint state mismatch")
    for field in (
        "publication_performed",
        "external_actions_performed",
        "target_repository_writes_performed",
        "private_repository_payload_copied",
        "original_source_repositories_modified",
    ):
        if cp.get(field) is not False:
            raise ProofEngineError(f"cross-repo checkpoint exceeded boundary: {field}")
    return {"campaign": verify_campaign(), "run": generated, "manifest": manifest, "checkpoint": cp}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Verify three sequential cross-repository Proof Engine validation rounds")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("verify")
    sub.add_parser("summary")
    sub.add_parser("review-template")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        bundle = verify_bundle()
        if args.command == "verify":
            print(f"Cross-repository validation passed ({bundle['run']['run_id']})")
        elif args.command == "summary":
            print(json.dumps({
                "run_id": bundle["run"]["run_id"],
                "result": bundle["run"]["result"],
                "candidate_count": bundle["run"]["candidate_count"],
                "comparison": bundle["run"]["comparison"],
                "state": bundle["checkpoint"]["state"],
                "publication_status": bundle["run"]["publication_status"],
            }, ensure_ascii=False, sort_keys=True, indent=2))
        else:
            print(json.dumps({
                "run_id": bundle["run"]["run_id"],
                "review_order": ROUND_ORDER,
                "allowed_decisions": ALLOWED_DECISIONS,
                "rounds": [
                    {
                        "round_id": item["round_id"],
                        "repository": item["repository"],
                        "candidate_ids": [candidate["candidate_id"] for candidate in item["candidates"]],
                        "withheld_claims": item["withheld_claims"],
                    }
                    for item in bundle["run"]["rounds"]
                ],
                "publication_authorized": False,
                "target_repository_write_authorized": False,
            }, ensure_ascii=False, sort_keys=True, indent=2))
    except ProofEngineError as exc:
        print(f"cross-repository validation failed closed: {exc}")
        return 1
    return 0

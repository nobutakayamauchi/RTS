from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from .core import ProofEngineError, fingerprint, load
from .cross_repo_campaign_close import verify_campaign_close
from .cross_repo_review import verify_round_two_review_bundle

PACKAGE_DIR = Path(__file__).resolve().parent
ROOT = PACKAGE_DIR.parent
ROUND_DIR = PACKAGE_DIR / "reporting" / "round_0001"
CONTRACT_PATH = ROUND_DIR / "template_contract.json"
MANIFEST_PATH = ROUND_DIR / "template_manifest.json"
CHECKPOINT_PATH = ROOT / "pilot_runs" / "reconnect_pilot_p3" / "evidence_report_template_checkpoint_0013.json"

SOURCE_CHECKPOINT_FINGERPRINT = "71dabc086ccb7aed49da559e812f2cdf2505cb172800d9830f67d338728bf832"
CONTRACT_FINGERPRINT = "483c0e377c415c6be05f218a0f7a3bb06fac720a6f2b12f1c8b3916df3501a69"
MANIFEST_FINGERPRINT = "b47f479e19516d51d58f29f94030111f16b9d12f854fca110b86b9ebda257d2c"
ROUND_ORDER = ["ROUND-2", "ROUND-3", "ROUND-4"]
REQUIRED_SECTIONS = [
    "executive_summary",
    "repository_scope",
    "methodology",
    "evidence_inventory",
    "effective_achievement_records",
    "human_and_ai_contribution_map",
    "withheld_or_unsupported_claims",
    "limitations",
    "human_review_decision",
]
REQUIRED_ACHIEVEMENT_FIELDS = [
    "candidate_id",
    "claim",
    "record_kind",
    "factuality_note",
    "contribution_map",
    "evidence_label",
    "evidence_prs",
    "source_candidate_fingerprint",
    "review_status",
    "public_disclosure",
]
AUTHORITY_FIELDS = {
    "automatic_approval_authorized",
    "automatic_rewrite_authorized",
    "contract_authorized",
    "external_execution_authorized",
    "outreach_authorized",
    "pricing_authorized",
    "publication_authorized",
    "target_repository_write_authorized",
}
CHECKPOINT_FIELDS = {
    "schema_version", "checkpoint_id", "source_campaign_close_checkpoint_fingerprint",
    "template_contract_fingerprint", "template_manifest_fingerprint", "report_count",
    "effective_candidate_count", "withheld_claim_count", "state",
    "publication_performed", "delivery_performed", "pricing_performed",
    "outreach_performed", "contract_action_performed", "external_actions_performed",
    "target_repository_writes_performed", "next_action", "checkpoint_fingerprint",
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


def verify_template_contract(contract: dict[str, Any] | None = None) -> dict[str, Any]:
    value = load(CONTRACT_PATH) if contract is None else copy.deepcopy(contract)
    _verify_fingerprint(value, "contract_fingerprint", "report template contract")
    if value.get("contract_fingerprint") != CONTRACT_FINGERPRINT:
        raise ProofEngineError("report template contract deterministic fingerprint mismatch")
    expected_authorization = {
        "type": "HUMAN", "identity": "nobutakayamauchi",
        "identity_source": "CURRENT_CHAT_EXPLICIT_NEXT_WORK_INSTRUCTION",
        "role": "PROJECT_OWNER", "instruction": "ラウンド4確定次の作業に移る",
    }
    expected_designer = {
        "type": "AI_ASSISTANT", "role": "REPORT_TEMPLATE_DESIGNER",
        "decision_origin": "AI_DESIGN_UNDER_EXPLICIT_HUMAN_NEXT_WORK_AUTHORIZATION",
    }
    if value.get("schema_version") != "PROOF-ENGINE-EVIDENCE-REPORT-TEMPLATE-CONTRACT-V1":
        raise ProofEngineError("report template contract schema mismatch")
    if value.get("contract_id") != "PROOF-ENGINE-EVIDENCE-REPORT-TEMPLATE-CONTRACT-0001":
        raise ProofEngineError("report template contract identity mismatch")
    if value.get("design_authorization") != expected_authorization:
        raise ProofEngineError("report template is not bound to the explicit next-work instruction")
    if value.get("designer") != expected_designer:
        raise ProofEngineError("report template designer attribution mismatch")
    if value.get("source") != {
        "campaign_close_checkpoint_fingerprint": SOURCE_CHECKPOINT_FINGERPRINT,
        "source_run_fingerprint": "413304aa513efe09cae300de23909318e8bfcc6ecfef5be7a35ab79a70def5bb",
        "effective_candidate_count": 16,
        "withheld_claim_count": 5,
    }:
        raise ProofEngineError("report template source mismatch")
    if value.get("required_sections") != REQUIRED_SECTIONS:
        raise ProofEngineError("report template section contract mismatch")
    if value.get("required_achievement_fields") != REQUIRED_ACHIEVEMENT_FIELDS:
        raise ProofEngineError("report template achievement field contract mismatch")
    if value.get("allowed_source_modes") != ["READ_ONLY_SNAPSHOT", "READ_ONLY_METADATA_SNAPSHOT"]:
        raise ProofEngineError("report template source modes mismatch")
    if value.get("required_report_states") != {
        "draft_state": "HUMAN_REPORT_REVIEW_REQUIRED",
        "publication_status": "NOT_PUBLISHED",
        "delivery_status": "NOT_DELIVERED",
    }:
        raise ProofEngineError("report template state contract mismatch")
    _verify_false_authority(value.get("authority"), "report template contract")
    return value


def verify_template_manifest(manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    value = load(MANIFEST_PATH) if manifest is None else copy.deepcopy(manifest)
    _verify_fingerprint(value, "manifest_fingerprint", "report template manifest")
    if value.get("manifest_fingerprint") != MANIFEST_FINGERPRINT:
        raise ProofEngineError("report template manifest deterministic fingerprint mismatch")
    expected = {
        "schema_version": "PROOF-ENGINE-EVIDENCE-REPORT-TEMPLATE-MANIFEST-V1",
        "manifest_id": "PROOF-ENGINE-EVIDENCE-REPORT-TEMPLATE-MANIFEST-0001",
        "template_contract_fingerprint": CONTRACT_FINGERPRINT,
        "source_campaign_close_checkpoint_fingerprint": SOURCE_CHECKPOINT_FINGERPRINT,
        "expected_report_count": 3,
        "expected_effective_candidate_count": 16,
        "expected_withheld_claim_count": 5,
        "required_sections": REQUIRED_SECTIONS,
        "draft_state": "HUMAN_REPORT_TEMPLATE_REVIEW_REQUIRED",
        "publication_status": "NOT_PUBLISHED",
        "delivery_status": "NOT_DELIVERED",
    }
    material = copy.deepcopy(value)
    material.pop("manifest_fingerprint")
    if material != expected:
        raise ProofEngineError("report template manifest content mismatch")
    return value


def build_template(contract: dict[str, Any] | None = None) -> dict[str, Any]:
    source = verify_template_contract(contract)
    template = {
        "schema_version": "PROOF-ENGINE-EVIDENCE-REPORT-TEMPLATE-V1",
        "template_id": "PROOF-ENGINE-EVIDENCE-REPORT-TEMPLATE-0001",
        "template_contract_fingerprint": source["contract_fingerprint"],
        "purpose": "Convert reviewed repository evidence into a fact-bounded achievement discovery report without manufacturing authorship, commercial outcomes, or release authority.",
        "input_contract": {
            "required_repository_fields": ["repository", "visibility", "source_mode", "snapshot_ref"],
            "required_evidence_fields": ["selected_prs", "readme_blob_sha"],
            "required_review_fields": ["effective_candidates", "withheld_claims"],
            "allowed_source_modes": copy.deepcopy(source["allowed_source_modes"]),
        },
        "section_contract": {
            section: {"required": True, "human_review_required": section == "human_review_decision"}
            for section in REQUIRED_SECTIONS
        },
        "achievement_record_contract": {
            "required_fields": copy.deepcopy(REQUIRED_ACHIEVEMENT_FIELDS),
            "original_or_revision_lineage_required": True,
            "contribution_separation_required": True,
            "unsupported_generalization_prohibited": True,
        },
        "rendering_policy": {
            "fact_bounded_language_required": True,
            "withheld_claims_must_be_visible": True,
            "limitations_must_be_visible": True,
            "pricing_or_sales_copy_generated": False,
            "publication_or_delivery_performed": False,
        },
        "allowed_human_decisions": ["APPROVE", "REVISE", "REJECT", "REDACT", "EXPIRE"],
        "required_report_states": copy.deepcopy(source["required_report_states"]),
        "authority": copy.deepcopy(source["authority"]),
    }
    template["template_fingerprint"] = fingerprint(template)
    return template


def _find_round(values: list[dict[str, Any]], round_id: str, label: str) -> dict[str, Any]:
    value = next((item for item in values if item["round_id"] == round_id), None)
    if value is None:
        raise ProofEngineError(f"missing {label} round: {round_id}")
    return value


def _effective_records(run_round: dict[str, Any], review: dict[str, Any]) -> list[dict[str, Any]]:
    originals = {item["candidate_id"]: item for item in run_round["candidates"]}
    revision = review.get("revision")
    records = []
    for effective in review["effective_candidates"]:
        candidate_id = effective["candidate_id"]
        if effective["source"] == "REVISION_LEDGER":
            if not isinstance(revision, dict) or revision.get("candidate_id") != candidate_id:
                raise ProofEngineError(f"missing effective revision: {candidate_id}")
            candidate = revision
        else:
            candidate = originals.get(candidate_id)
            if candidate is None:
                raise ProofEngineError(f"missing effective original: {candidate_id}")
        if candidate.get("candidate_fingerprint") != effective["candidate_fingerprint"]:
            raise ProofEngineError(f"effective candidate fingerprint mismatch: {candidate_id}")
        record = {
            "candidate_id": candidate_id,
            "claim": candidate["claim"],
            "record_kind": candidate["record_kind"],
            "factuality_note": candidate["factuality_note"],
            "contribution_map": copy.deepcopy(candidate["contribution_map"]),
            "evidence_label": candidate["evidence_label"],
            "evidence_prs": copy.deepcopy(candidate["evidence_prs"]),
            "source_candidate_fingerprint": candidate["candidate_fingerprint"],
            "review_status": effective["status"],
            "public_disclosure": candidate["public_disclosure"],
            "lineage": {
                "source": effective["source"],
                "candidate_version": effective["candidate_version"],
                "approval_decision_fingerprint": effective["approval_decision_fingerprint"],
            },
        }
        if set(REQUIRED_ACHIEVEMENT_FIELDS) - set(record):
            raise ProofEngineError(f"report achievement record incomplete: {candidate_id}")
        record["achievement_record_fingerprint"] = fingerprint(record)
        records.append(record)
    return records


def _limitations(round_id: str) -> list[str]:
    common = [
        "The report is limited to the selected repository snapshot and reviewed evidence records.",
        "The report does not establish commercial effectiveness, customer value, or revenue.",
        "The report is an internal draft and has not been delivered or published.",
    ]
    specific = {
        "ROUND-2": [
            "Unmerged pull requests are excluded from completed-achievement evidence.",
            "The evidence does not establish learning effectiveness across arbitrary educational content.",
        ],
        "ROUND-3": [
            "The private repository analysis uses metadata-only evidence and copies no customer-specific payload.",
            "Manual publication records do not prove automatic publishing or independent platform verification.",
        ],
        "ROUND-4": [
            "The repository is a frozen scaffold rather than a validated end-to-end product.",
            "Transcription accuracy, runtime behavior, and production readiness remain unverified.",
        ],
    }
    return common + specific[round_id]


def _contribution_section(records: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "records": [{
            "candidate_id": item["candidate_id"],
            "human": copy.deepcopy(item["contribution_map"].get("human", [])),
            "ai_tool": copy.deepcopy(item["contribution_map"].get("ai_tool", [])),
            "collaborator": copy.deepcopy(item["contribution_map"].get("collaborator", [])),
            "inherited": copy.deepcopy(item["contribution_map"].get("inherited", [])),
        } for item in records],
        "policy": "Human decisions, constraints, and approvals remain separate from AI-tool implementation, drafting, and verification support.",
    }


def _build_repository_report(
    *,
    round_id: str,
    campaign_round: dict[str, Any],
    run_round: dict[str, Any],
    review: dict[str, Any],
) -> dict[str, Any]:
    records = _effective_records(run_round, review)
    merged_prs = [
        {"number": item["number"], "title": item["title"], "status": item["status"]}
        for item in campaign_round["selected_prs"]
        if item.get("merged") is True and item.get("status") == "MERGED"
    ]
    excluded_prs = [item["number"] for item in campaign_round["selected_prs"] if item.get("merged") is not True]
    withheld = [{
        "claim": item["claim"], "reason": item["reason"], "status": "WITHHELD_UNSUPPORTED"
    } for item in campaign_round.get("withheld_claims", [])]
    repository = campaign_round["repository"]
    sections = {
        "executive_summary": {
            "text": f"This internal draft identifies {len(records)} reviewed evidence-backed records from {repository} and retains {len(withheld)} unsupported claims as withheld.",
            "achievement_count": len(records), "withheld_claim_count": len(withheld),
        },
        "repository_scope": {
            "repository": repository, "visibility": campaign_round["visibility"],
            "source_mode": campaign_round["source_mode"], "snapshot_ref": campaign_round["snapshot_ref"],
            "role": campaign_round["role"],
        },
        "methodology": {
            "steps": [
                "Use the fixed read-only source snapshot.",
                "Treat only eligible merged pull requests as completed-achievement evidence.",
                "Apply the active factuality and classification preflight.",
                "Use append-only human review decisions and factual revisions.",
                "Preserve unsupported claims as withheld rather than silently deleting them.",
            ],
            "automatic_approval": False, "automatic_rewrite": False,
        },
        "evidence_inventory": {
            "readme_blob_sha": campaign_round["readme_blob_sha"],
            "merged_prs": merged_prs,
            "excluded_unmerged_prs": excluded_prs,
            "source_round_fingerprint": run_round["round_fingerprint"],
        },
        "effective_achievement_records": records,
        "human_and_ai_contribution_map": _contribution_section(records),
        "withheld_or_unsupported_claims": withheld,
        "limitations": _limitations(round_id),
        "human_review_decision": {
            "state": "HUMAN_REPORT_REVIEW_REQUIRED",
            "allowed_decisions": ["APPROVE", "REVISE", "REJECT", "REDACT", "EXPIRE"],
            "decisions": [], "publication_authorized": False, "delivery_authorized": False,
        },
    }
    if list(sections) != REQUIRED_SECTIONS:
        raise ProofEngineError(f"report section order mismatch: {round_id}")
    report = {
        "schema_version": "PROOF-ENGINE-EVIDENCE-REPORT-DRAFT-V1",
        "report_id": f"PROOF-ENGINE-EVIDENCE-REPORT-DEMO-{round_id}",
        "report_version": 1, "round_id": round_id, "repository": repository,
        "sections": sections,
        "draft_state": "HUMAN_REPORT_REVIEW_REQUIRED",
        "publication_status": "NOT_PUBLISHED", "delivery_status": "NOT_DELIVERED",
        "authority": {
            "pricing_authorized": False, "outreach_authorized": False,
            "publication_authorized": False, "delivery_authorized": False,
            "contract_authorized": False,
        },
    }
    report["report_fingerprint"] = fingerprint(report)
    return report


def build_demonstration_pack(contract: dict[str, Any] | None = None) -> dict[str, Any]:
    template = build_template(contract)
    close = verify_campaign_close()
    if close["checkpoint"]["checkpoint_fingerprint"] != SOURCE_CHECKPOINT_FINGERPRINT:
        raise ProofEngineError("report template source checkpoint drift")
    campaign_rounds = close["source_bundle"]["campaign"]["rounds"]
    run_rounds = close["source_bundle"]["run"]["rounds"]
    reviews = {
        "ROUND-2": verify_round_two_review_bundle()["review"],
        "ROUND-3": close["previous"]["review"],
        "ROUND-4": close["review"],
    }
    reports = [
        _build_repository_report(
            round_id=round_id,
            campaign_round=_find_round(campaign_rounds, round_id, "campaign"),
            run_round=_find_round(run_rounds, round_id, "run"),
            review=reviews[round_id],
        )
        for round_id in ROUND_ORDER
    ]
    pack = {
        "schema_version": "PROOF-ENGINE-EVIDENCE-REPORT-DEMONSTRATION-PACK-V1",
        "pack_id": "PROOF-ENGINE-EVIDENCE-REPORT-DEMONSTRATION-PACK-0001",
        "template_fingerprint": template["template_fingerprint"],
        "source_campaign_evaluation_fingerprint": close["evaluation"]["evaluation_fingerprint"],
        "reports": reports,
        "counts": {
            "reports": len(reports),
            "effective_achievement_records": sum(len(item["sections"]["effective_achievement_records"]) for item in reports),
            "withheld_claims": sum(len(item["sections"]["withheld_or_unsupported_claims"]) for item in reports),
        },
        "state": "HUMAN_REPORT_TEMPLATE_REVIEW_REQUIRED",
        "publication_status": "NOT_PUBLISHED", "delivery_status": "NOT_DELIVERED",
    }
    pack["pack_fingerprint"] = fingerprint(pack)
    return {"template": template, "pack": pack, "campaign_close": close}


def render_demonstration_markdown(bundle: dict[str, Any] | None = None) -> str:
    value = build_demonstration_pack() if bundle is None else bundle
    lines = [
        "# Evidence-Backed Achievement Discovery Report — Internal Demonstration", "",
        "Status: HUMAN_REPORT_TEMPLATE_REVIEW_REQUIRED / NOT_PUBLISHED / NOT_DELIVERED", "",
    ]
    for report in value["pack"]["reports"]:
        sections = report["sections"]
        lines.extend([f"## {report['repository']}", "", sections["executive_summary"]["text"], "",
                      "### Reviewed achievement records", ""])
        for record in sections["effective_achievement_records"]:
            lines.extend([
                f"- **{record['candidate_id']} — {record['record_kind']}**",
                f"  - Claim: {record['claim']}",
                f"  - Evidence PRs: {', '.join('#' + str(number) for number in record['evidence_prs'])}",
                f"  - Limitation: {record['factuality_note']}",
            ])
        lines.extend(["", "### Withheld claims", ""])
        withheld = sections["withheld_or_unsupported_claims"]
        lines.extend(
            [f"- {item['claim']} — {item['reason']}" for item in withheld]
            if withheld else ["- None in the selected evidence boundary."]
        )
        lines.extend(["", "### Report limitations", ""])
        lines.extend(f"- {item}" for item in sections["limitations"])
        lines.append("")
    lines.extend(["## Human review gate", "",
                  "No report in this demonstration has been approved for pricing, outreach, delivery, or publication.", ""])
    return "\n".join(lines)


def verify_report_template(
    *, contract: dict[str, Any] | None = None,
    manifest: dict[str, Any] | None = None,
    checkpoint: dict[str, Any] | None = None,
) -> dict[str, Any]:
    verified_manifest = verify_template_manifest(manifest)
    bundle = build_demonstration_pack(contract)
    template, pack = bundle["template"], bundle["pack"]
    _verify_fingerprint(template, "template_fingerprint", "report template")
    _verify_fingerprint(pack, "pack_fingerprint", "report demonstration pack")
    if pack["counts"] != {"reports": 3, "effective_achievement_records": 16, "withheld_claims": 5}:
        raise ProofEngineError("report demonstration pack counts mismatch")
    if pack["state"] != verified_manifest["draft_state"]:
        raise ProofEngineError("report demonstration pack state mismatch")
    if pack["publication_status"] != "NOT_PUBLISHED" or pack["delivery_status"] != "NOT_DELIVERED":
        raise ProofEngineError("report demonstration pack release boundary widened")
    for report in pack["reports"]:
        if list(report["sections"]) != REQUIRED_SECTIONS:
            raise ProofEngineError("report section set mismatch")
        for record in report["sections"]["effective_achievement_records"]:
            if set(REQUIRED_ACHIEVEMENT_FIELDS) - set(record):
                raise ProofEngineError("report achievement record fields missing")
        if report["sections"]["human_review_decision"]["decisions"]:
            raise ProofEngineError("report template manufactured a human decision")

    cp = load(CHECKPOINT_PATH) if checkpoint is None else copy.deepcopy(checkpoint)
    if set(cp) != CHECKPOINT_FIELDS:
        raise ProofEngineError("report template checkpoint schema fields mismatch")
    _verify_fingerprint(cp, "checkpoint_fingerprint", "report template checkpoint")
    expected_links = {
        "schema_version": "PROOF-ENGINE-EVIDENCE-REPORT-TEMPLATE-CHECKPOINT-V1",
        "checkpoint_id": "PROOF-ENGINE-EVIDENCE-REPORT-TEMPLATE-CHECKPOINT-0013",
        "source_campaign_close_checkpoint_fingerprint": SOURCE_CHECKPOINT_FINGERPRINT,
        "template_contract_fingerprint": CONTRACT_FINGERPRINT,
        "template_manifest_fingerprint": MANIFEST_FINGERPRINT,
    }
    for field, expected in expected_links.items():
        if cp.get(field) != expected:
            raise ProofEngineError(f"report template checkpoint link mismatch: {field}")
    if (cp.get("report_count"), cp.get("effective_candidate_count"), cp.get("withheld_claim_count")) != (3, 16, 5):
        raise ProofEngineError("report template checkpoint counts mismatch")
    if cp.get("state") != "HUMAN_REPORT_TEMPLATE_REVIEW_REQUIRED":
        raise ProofEngineError("report template checkpoint state mismatch")
    for field in (
        "publication_performed", "delivery_performed", "pricing_performed", "outreach_performed",
        "contract_action_performed", "external_actions_performed", "target_repository_writes_performed",
    ):
        if cp.get(field) is not False:
            raise ProofEngineError(f"report template checkpoint exceeded boundary: {field}")
    return {**bundle, "manifest": verified_manifest, "checkpoint": cp}

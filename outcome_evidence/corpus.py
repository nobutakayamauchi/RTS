from __future__ import annotations

from pathlib import Path
from typing import Any

from .models import (
    OutcomeEvidenceError,
    SCENARIOS,
    load_json,
    sha256_file,
    validate_bundle,
    validate_evidence_source,
)

PACKAGE_DIR = Path(__file__).resolve().parent
DEFAULT_ROOT = PACKAGE_DIR.parent
DEFAULT_EXAMPLES = Path("outcome_evidence/examples")


def _inside(path: Path, directory: Path) -> bool:
    path = path.resolve()
    directory = directory.resolve()
    return path == directory or directory in path.parents


def bundle_paths(root: Path) -> list[Path]:
    base = root.resolve() / DEFAULT_EXAMPLES
    if not base.exists():
        raise OutcomeEvidenceError(f"missing corpus directory: {base}")
    paths = sorted(base.glob("*.json"))
    if not paths:
        raise OutcomeEvidenceError("outcome corpus is empty")
    return paths


def validate_bundle_file(root: Path, path: Path) -> dict[str, Any]:
    root = root.resolve()
    path = path.resolve()
    if not _inside(path, root / DEFAULT_EXAMPLES):
        raise OutcomeEvidenceError("bundle path escaped corpus directory")
    bundle = validate_bundle(load_json(path))
    for ref in bundle["evidence_refs"]:
        source_path = (root / ref["source_ref"]).resolve()
        evidence_root = root / "outcome_evidence" / "evidence"
        if not _inside(source_path, evidence_root):
            raise OutcomeEvidenceError("evidence source escaped governed evidence directory")
        expected_hash = bundle["evidence_integrity"][ref["evidence_id"]]
        if sha256_file(source_path) != expected_hash:
            raise OutcomeEvidenceError(
                f"{bundle['bundle_id']}: evidence hash mismatch for {ref['evidence_id']}"
            )
        evidence = validate_evidence_source(load_json(source_path))
        if evidence["evidence_id"] != ref["evidence_id"]:
            raise OutcomeEvidenceError(f"{bundle['bundle_id']}: evidence ID mismatch")
        if evidence["scenario"] != bundle["scenario"]:
            raise OutcomeEvidenceError(f"{bundle['bundle_id']}: evidence scenario mismatch")
        controller = bundle["controller"]
        comparisons = {
            "plan_fingerprint": controller["plan_fingerprint"],
            "authorization_fingerprint": controller["authorization_fingerprint"],
            "terminal_state": controller["terminal_state"],
            "usage": controller["budget_usage"],
            "external_execution_performed": controller["external_execution_performed"],
        }
        for field, expected in comparisons.items():
            if evidence[field] != expected:
                raise OutcomeEvidenceError(
                    f"{bundle['bundle_id']}: evidence/controller mismatch: {field}"
                )
        if evidence["timestamp"] != bundle["execution_record"]["timestamp"]:
            raise OutcomeEvidenceError(f"{bundle['bundle_id']}: evidence timestamp mismatch")
    return bundle


def load_corpus(root: Path = DEFAULT_ROOT) -> list[dict[str, Any]]:
    root = root.resolve()
    bundles = [validate_bundle_file(root, path) for path in bundle_paths(root)]
    if len(bundles) < 3:
        raise OutcomeEvidenceError("outcome corpus requires at least three bundles")
    scenarios = {bundle["scenario"] for bundle in bundles}
    missing = sorted(SCENARIOS - scenarios)
    if missing:
        raise OutcomeEvidenceError(f"outcome corpus missing scenarios: {', '.join(missing)}")
    bundle_ids = [bundle["bundle_id"] for bundle in bundles]
    if len(bundle_ids) != len(set(bundle_ids)):
        raise OutcomeEvidenceError("outcome corpus contains duplicate bundle IDs")
    evidence_ids = [
        ref["evidence_id"]
        for bundle in bundles
        for ref in bundle["evidence_refs"]
    ]
    if len(evidence_ids) != len(set(evidence_ids)):
        raise OutcomeEvidenceError("outcome corpus contains duplicate evidence IDs")
    if any(bundle["promotion_eligibility"] != "NOT_ELIGIBLE" for bundle in bundles):
        raise OutcomeEvidenceError("simulated corpus cannot contain promotion-eligible bundles")
    return bundles


def corpus_summary(root: Path = DEFAULT_ROOT) -> dict[str, Any]:
    bundles = load_corpus(root)
    return {
        "schema_version": "RTS-OUTCOME-CORPUS-SUMMARY-V1",
        "bundle_count": len(bundles),
        "scenarios": sorted({bundle["scenario"] for bundle in bundles}),
        "classifications": sorted({bundle["outcome_classification"] for bundle in bundles}),
        "execution_scope": "SIMULATED_ONLY",
        "promotion_eligibility": "NOT_ELIGIBLE",
        "bundle_ids": sorted(bundle["bundle_id"] for bundle in bundles),
    }

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from .common import LearningProposalError, load_json, pretty_json, sha256_file
from .generation import generate_pending_review, generate_proposal
from .models import validate_proposal, validate_review

PACKAGE_DIR = Path(__file__).resolve().parent
DEFAULT_ROOT = PACKAGE_DIR.parent
PROPOSAL_PATH = "learning_proposals/proposals/feature-build-v1.json"
REVIEW_PATH = "learning_proposals/reviews/feature-build-v1.pending.json"
FORBIDDEN_IMPORTS = {"subprocess", "socket", "requests", "urllib", "http", "ftplib"}


def _verify_forbidden_imports(root: Path) -> None:
    package = root / "learning_proposals"
    for path in sorted(package.glob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            raise LearningProposalError(f"invalid Python syntax: {path}: {exc}") from exc
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                names.append(node.module)
            for name in names:
                root_name = name.split(".", 1)[0]
                if root_name in FORBIDDEN_IMPORTS:
                    raise LearningProposalError(f"forbidden external-action import in {path}: {name}")


def load_committed(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    proposal = load_json(root / PROPOSAL_PATH)
    review = load_json(root / REVIEW_PATH)
    if not isinstance(proposal, dict) or not isinstance(review, dict):
        raise LearningProposalError("committed proposal and review must be objects")
    return proposal, review


def verify_all(root: Path = DEFAULT_ROOT) -> dict[str, Any]:
    root = root.resolve()
    governed_paths = [
        root / PROPOSAL_PATH,
        root / REVIEW_PATH,
        root / "outcome_evidence/examples/success.json",
        root / "outcome_evidence/examples/escalation.json",
        root / "outcome_evidence/examples/recovery.json",
        root / "skill_regression/results/feature-build-v1.json",
        root / "skill_regression/datasets/feature-build-v1.json",
        root / "skill_regression/rollback/feature-build-v1.json",
        root / "skill_regression/snapshots/feature-build/candidate.json",
    ]
    before = {path: sha256_file(path) for path in governed_paths}
    _verify_forbidden_imports(root)
    committed_proposal, committed_review = load_committed(root)
    validate_proposal(committed_proposal)
    validate_review(committed_review, committed_pending_only=True)

    first = generate_proposal(root)
    second = generate_proposal(root)
    if pretty_json(first) != pretty_json(second):
        raise LearningProposalError("proposal generation is not deterministic")
    if pretty_json(first) != pretty_json(committed_proposal):
        raise LearningProposalError("committed proposal is stale")
    pending = generate_pending_review(first)
    if pretty_json(pending) != pretty_json(committed_review):
        raise LearningProposalError("committed pending review is stale")
    if committed_review["proposal_id"] != committed_proposal["proposal_id"]:
        raise LearningProposalError("review proposal_id mismatch")
    if committed_review["proposal_fingerprint"] != committed_proposal["proposal_fingerprint"]:
        raise LearningProposalError("review proposal fingerprint mismatch")
    after = {path: sha256_file(path) for path in governed_paths}
    if before != after:
        raise LearningProposalError("read-only verification failed: governed input changed")

    return {
        "proposal_id": committed_proposal["proposal_id"],
        "proposal_fingerprint": committed_proposal["proposal_fingerprint"],
        "proposal_status": committed_proposal["proposal_status"],
        "review_status": committed_review["status"],
        "recommendation": committed_proposal["recommendation"]["action"],
        "approval_status": committed_proposal["safeguards"]["approval_status"],
        "application_status": committed_proposal["safeguards"]["application_status"],
    }

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from learning_proposals.common import LearningProposalError, sha256_value
from learning_proposals.corpus import _verify_forbidden_imports, verify_all
from learning_proposals.generation import generate_pending_review, generate_proposal
from learning_proposals.models import (
    proposal_material,
    review_material,
    validate_proposal,
    validate_review,
)


class LearningProposalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]

    def test_committed_records_verify(self) -> None:
        summary = verify_all(self.root)
        self.assertEqual(summary["proposal_status"], "REVIEW_REQUIRED")
        self.assertEqual(summary["review_status"], "PENDING")
        self.assertEqual(summary["application_status"], "NOT_APPLIED")

    def test_generation_is_deterministic(self) -> None:
        self.assertEqual(generate_proposal(self.root), generate_proposal(self.root))

    def test_proposal_fingerprint_mutation_is_rejected(self) -> None:
        proposal = generate_proposal(self.root)
        proposal["recommendation"]["rationale"] += " changed"
        with self.assertRaisesRegex(LearningProposalError, "fingerprint mismatch"):
            validate_proposal(proposal)

    def test_simulated_outcome_scope_cannot_widen(self) -> None:
        proposal = generate_proposal(self.root)
        proposal["generated_from"]["outcome_bundles"][0]["execution_scope"] = "EXTERNAL"
        proposal["proposal_fingerprint"] = sha256_value(proposal_material(proposal))
        with self.assertRaisesRegex(LearningProposalError, "SIMULATED_ONLY"):
            validate_proposal(proposal)

    def test_regression_eligibility_cannot_widen(self) -> None:
        proposal = generate_proposal(self.root)
        proposal["generated_from"]["regression"]["promotion_eligibility"] = "ELIGIBLE"
        proposal["proposal_fingerprint"] = sha256_value(proposal_material(proposal))
        with self.assertRaisesRegex(LearningProposalError, "NOT_ELIGIBLE"):
            validate_proposal(proposal)

    def test_proposal_cannot_authorize_mutation(self) -> None:
        proposal = generate_proposal(self.root)
        proposal["safeguards"]["mutation_authorized"] = True
        proposal["proposal_fingerprint"] = sha256_value(proposal_material(proposal))
        with self.assertRaisesRegex(LearningProposalError, "must be false"):
            validate_proposal(proposal)

    def test_pending_review_cannot_claim_human_identity(self) -> None:
        review = generate_pending_review(generate_proposal(self.root))
        review["reviewer"] = {"type": "HUMAN", "identity": "reviewer-1"}
        review["decision_fingerprint"] = sha256_value(review_material(review))
        with self.assertRaisesRegex(LearningProposalError, "remain unassigned"):
            validate_review(review)

    def test_generator_cannot_self_approve(self) -> None:
        review = generate_pending_review(generate_proposal(self.root))
        review["status"] = "APPROVED"
        review["reviewer"] = {
            "type": "HUMAN",
            "identity": review["generator_identity"],
        }
        review["decision_fingerprint"] = sha256_value(review_material(review))
        with self.assertRaisesRegex(LearningProposalError, "cannot review its own"):
            validate_review(review)

    def test_committed_v1_review_must_remain_pending(self) -> None:
        review = generate_pending_review(generate_proposal(self.root))
        review["status"] = "REJECTED"
        review["reviewer"] = {"type": "HUMAN", "identity": "human-reviewer-1"}
        review["rationale"] = "Rejected by a human reviewer."
        review["decision_fingerprint"] = sha256_value(review_material(review))
        with self.assertRaisesRegex(LearningProposalError, "must remain PENDING"):
            validate_review(review, committed_pending_only=True)

    def test_private_content_field_is_rejected(self) -> None:
        proposal = generate_proposal(self.root)
        proposal["recommendation"]["provider_payload"] = "not allowed"
        proposal["proposal_fingerprint"] = sha256_value(proposal_material(proposal))
        with self.assertRaisesRegex(LearningProposalError, "forbidden private field"):
            validate_proposal(proposal)

    def test_forbidden_external_action_import_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            shutil.copytree(self.root / "learning_proposals", root / "learning_proposals")
            (root / "learning_proposals" / "unsafe.py").write_text(
                "import subprocess\n", encoding="utf-8"
            )
            with self.assertRaisesRegex(LearningProposalError, "forbidden external-action import"):
                _verify_forbidden_imports(root)


if __name__ == "__main__":
    unittest.main()

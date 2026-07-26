from __future__ import annotations

import copy
import unittest

from proof_engine_pilot.core import ProofEngineError, fingerprint, load
from proof_engine_pilot.learning import CHECKPOINT_PATH, preflight_candidate, verify_learning_bundle
from proof_engine_pilot.learning_cli import build_parser


class ReviewLearningTests(unittest.TestCase):
    def test_committed_learning_bundle_is_verified(self):
        bundle = verify_learning_bundle()
        self.assertEqual(bundle["dataset"]["counts"], {
            "positive_examples": 7,
            "correction_pairs": 5,
            "human_decisions_represented": 17,
        })
        self.assertEqual(bundle["policy"]["state"], "ACTIVE_FOR_FUTURE_RUNS")
        self.assertEqual(bundle["policy"]["mode"], "SUGGEST_ONLY")
        self.assertFalse(bundle["policy"]["model_weight_update_performed"])
        self.assertTrue(bundle["policy"]["original_records_preserved"])
        self.assertFalse(bundle["checkpoint"]["external_actions_performed"])

    def test_checkpoint_external_action_fails_closed(self):
        checkpoint = copy.deepcopy(load(CHECKPOINT_PATH))
        checkpoint["external_actions_performed"] = True
        material = copy.deepcopy(checkpoint)
        material.pop("checkpoint_fingerprint")
        checkpoint["checkpoint_fingerprint"] = fingerprint(material)
        with self.assertRaisesRegex(ProofEngineError, "unauthorized external action"):
            verify_learning_bundle(checkpoint=checkpoint)

    def test_factually_bounded_revision_passes_preflight(self):
        candidate = {
            "candidate_id": "ACH-NEXT",
            "claim": "Inside RTS, the project repeatedly used the pattern; this is a potential reuse signal.",
            "record_kind": "REUSABILITY_SIGNAL",
            "factuality_note": "External reuse is not yet observed.",
            "contribution_map": {"human": ["set thresholds"], "ai_tool": ["implemented checks"], "collaborator": []},
            "evidence_label": "INFERRED",
            "evidence_prs": [264],
            "public_disclosure": "INTERNAL_UNTIL_SEPARATE_PUBLICATION_APPROVAL",
        }
        self.assertEqual(preflight_candidate(candidate)["result"], "PASS")

    def test_missing_core_identity_and_claim_require_review(self):
        candidate = {
            "record_kind": "PROJECT_OUTPUT",
            "factuality_note": "Repository result only.",
            "contribution_map": {"human": ["approved"], "ai_tool": ["implemented"], "collaborator": []},
            "evidence_label": "VERIFIED",
            "evidence_prs": [264],
            "public_disclosure": "INTERNAL_UNTIL_APPROVED",
        }
        result = preflight_candidate(candidate)
        self.assertEqual(result["result"], "SUGGEST_REVIEW")
        self.assertIn("MISSING_LEARNING_FIELDS", {item["code"] for item in result["issues"]})

    def test_empty_core_identity_and_claim_require_review(self):
        candidate = {
            "candidate_id": "",
            "claim": " ",
            "record_kind": "PROJECT_OUTPUT",
            "factuality_note": "Repository result only.",
            "contribution_map": {"human": ["approved"], "ai_tool": ["implemented"], "collaborator": []},
            "evidence_label": "VERIFIED",
            "evidence_prs": [264],
            "public_disclosure": "INTERNAL_UNTIL_APPROVED",
        }
        codes = {item["code"] for item in preflight_candidate(candidate)["issues"]}
        self.assertIn("INVALID_CANDIDATE_ID", codes)
        self.assertIn("INVALID_CLAIM", codes)

    def test_authorship_overclaim_is_suggested_for_review(self):
        candidate = {
            "candidate_id": "ACH-NEXT",
            "claim": "Built the complete system.",
            "record_kind": "PERSONAL_ACHIEVEMENT",
            "contribution_map": {"human": ["approved"], "ai_tool": ["implemented code"], "collaborator": []},
            "evidence_label": "VERIFIED",
            "evidence_prs": [264],
            "public_disclosure": "INTERNAL_UNTIL_APPROVED",
        }
        result = preflight_candidate(candidate)
        codes = {item["code"] for item in result["issues"]}
        self.assertEqual(result["result"], "SUGGEST_REVIEW")
        self.assertIn("MISSING_LEARNING_FIELDS", codes)
        self.assertIn("DIRECT_AUTHORSHIP_REQUIRES_REVIEW", codes)

    def test_factuality_note_does_not_bypass_authorship_review(self):
        candidate = {
            "candidate_id": "ACH-NEXT",
            "claim": "Built the complete system.",
            "record_kind": "PERSONAL_ACHIEVEMENT",
            "factuality_note": "The AI implemented all code.",
            "contribution_map": {"human": ["approved"], "ai_tool": ["implemented all code"], "collaborator": []},
            "evidence_label": "VERIFIED",
            "evidence_prs": [264],
            "public_disclosure": "INTERNAL_UNTIL_APPROVED",
        }
        result = preflight_candidate(candidate)
        self.assertIn("DIRECT_AUTHORSHIP_REQUIRES_REVIEW", {item["code"] for item in result["issues"]})

    def test_cross_project_generalization_is_downgraded(self):
        candidate = {
            "candidate_id": "ACH-NEXT",
            "claim": "Established a repeatable pattern across future projects.",
            "record_kind": "PERSONAL_ACHIEVEMENT",
            "factuality_note": "Observed only inside RTS.",
            "contribution_map": {"human": ["set policy"], "ai_tool": ["implemented"], "collaborator": []},
            "evidence_label": "VERIFIED",
            "evidence_prs": [264],
            "public_disclosure": "INTERNAL_UNTIL_APPROVED",
        }
        result = preflight_candidate(candidate)
        self.assertIn("GENERALIZATION_EXCEEDS_EVIDENCE", {item["code"] for item in result["issues"]})

    def test_cli_has_no_apply_or_approve_command(self):
        parser = build_parser()
        action = next(action for action in parser._actions if getattr(action, "choices", None))
        self.assertEqual(set(action.choices), {"verify", "summary", "replay", "preflight"})


if __name__ == "__main__":
    unittest.main()

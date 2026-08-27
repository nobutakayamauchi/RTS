from __future__ import annotations

import hashlib
import unittest

from model_transition_intelligence.core import validate_bundle
from official_docs_intake import build_intake_report
from semantic_claim_refinement import refine_intake_report, verify_refinement_report
from semantic_claim_refinement.core import RefinementError


URL = "https://developers.openai.com/api/docs/guides/semantic-refinement-test"


def make_intake(body: str):
    def fetcher(provider: str, url: str):
        payload = body if url == URL else "index"
        return {
            "requested_url": url,
            "final_url": url,
            "content_type": "text/plain; charset=utf-8",
            "body": payload,
            "raw_sha256": hashlib.sha256(payload.encode()).hexdigest(),
            "etag": None,
            "last_modified": None,
            "status": 200,
        }

    report = build_intake_report(
        {
            "provider": "openai",
            "product_surface": "api",
            "generation": "test-generation",
            "captured_at": "2026-08-27T11:00:00Z",
            "query_terms": ["test-generation"],
            "explicit_urls": [URL],
            "max_documents": 1,
        },
        fetcher=fetcher,
    )
    return report


class SemanticClaimRefinementTests(unittest.TestCase):
    def test_unique_semantic_alias_reduces_review(self):
        intake = make_intake("Requests may dispatch several functions concurrently.")
        self.assertEqual(intake["status"], "REVIEW_REQUIRED")
        self.assertEqual(intake["audit"]["ambiguous_block_count"], 1)

        refined = refine_intake_report(intake)
        verify_refinement_report(refined, intake_report=intake)
        self.assertEqual(refined["status"], "READY_FOR_H")
        self.assertEqual(refined["audit"]["resolved_count"], 1)
        self.assertEqual(refined["audit"]["remaining_ambiguous_count"], 0)
        self.assertEqual(refined["audit"]["added_claim_count"], 1)
        validate_bundle(refined["bundle"])

        claims = refined["bundle"]["sources"][0]["claims"]
        semantic = [c for c in claims if c.get("extraction_method") == "CONTROLLED_SEMANTIC_ALIAS_V1"]
        self.assertEqual(len(semantic), 1)
        self.assertEqual(semantic[0]["anchor"], "Requests may dispatch several functions concurrently.")
        self.assertEqual(semantic[0]["area"], "tools")
        self.assertEqual(semantic[0]["key"], "parallel_tool_calls")
        self.assertEqual(semantic[0]["behavior_status"], "UNVERIFIED")
        self.assertEqual(semantic[0]["value"]["mode"], "PARALLEL_TOOL_CALLS")

    def test_unmatched_contract_text_stays_review_required(self):
        intake = make_intake("Requests now use a new runtime policy for advanced workflows.")
        refined = refine_intake_report(intake)
        self.assertEqual(refined["status"], "REVIEW_REQUIRED")
        self.assertEqual(refined["audit"]["resolved_count"], 0)
        self.assertEqual(refined["audit"]["remaining_ambiguous_count"], 1)
        self.assertEqual(refined["audit"]["unresolved"][0]["reason"], "NO_ONTOLOGY_MATCH")

    def test_upstream_truncation_blocks_ready_even_when_listed_anchor_resolves(self):
        intake = make_intake("Requests may dispatch several functions concurrently.")
        intake["audit"]["documents"][0]["extraction"]["ambiguous_findings_truncated"] = True
        refined = refine_intake_report(intake)
        self.assertEqual(refined["status"], "REVIEW_REQUIRED")
        self.assertTrue(refined["audit"]["upstream_ambiguous_findings_truncated"])
        self.assertGreater(refined["audit"]["remaining_ambiguous_count"], 0)

    def test_refined_claims_never_gain_authority(self):
        intake = make_intake("Requests may dispatch several functions concurrently.")
        refined = refine_intake_report(intake)
        self.assertEqual(refined["execution_authority"], "NONE")
        self.assertEqual(refined["profile_application_authority"], "NONE")
        self.assertEqual(refined["promotion_authority"], "NONE")
        self.assertEqual(refined["hidden_architecture_claim"], "NONE")
        self.assertEqual(refined["docs_claim_status"], "UNVERIFIED")

    def test_input_fingerprint_prevents_stale_verification(self):
        intake = make_intake("Requests may dispatch several functions concurrently.")
        refined = refine_intake_report(intake)
        changed = make_intake("Requests now use a new runtime policy for advanced workflows.")
        with self.assertRaises(RefinementError):
            verify_refinement_report(refined, intake_report=changed)

    def test_failed_intake_stays_failed(self):
        intake = make_intake("Requests may dispatch several functions concurrently.")
        intake["bundle"] = None
        intake["status"] = "FAILED"
        refined = refine_intake_report(intake)
        self.assertEqual(refined["status"], "FAILED")
        self.assertIsNone(refined["bundle"])


if __name__ == "__main__":
    unittest.main()

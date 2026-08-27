from __future__ import annotations

import hashlib
import unittest

from official_docs_intake import (
    IntakeError,
    PROVIDER_POLICIES,
    build_intake_report,
    discover_document_urls,
    verify_intake_report,
)


def fetched(url: str, body: str) -> dict:
    return {
        "requested_url": url,
        "final_url": url,
        "content_type": "text/plain; charset=utf-8",
        "body": body,
        "raw_sha256": hashlib.sha256(body.encode()).hexdigest(),
        "etag": None,
        "last_modified": None,
        "status": 200,
    }


class OfficialDocsIntakeDATests(unittest.TestCase):
    def test_known_claim_cannot_hide_unknown_contract_change_in_same_line(self):
        url = "https://developers.openai.com/api/docs/models"
        body = (
            "Context window is 1,050,000 tokens. "
            "Requests now pass through a novel coordination plane before completion."
        )

        def mock_fetch(provider: str, requested: str) -> dict:
            if requested == url:
                return fetched(url, body)
            raise IntakeError("fixture index unavailable")

        report = build_intake_report({
            "provider": "openai",
            "product_surface": "api",
            "generation": "gpt-x",
            "captured_at": "2026-08-27T10:00:00Z",
            "explicit_urls": [url],
            "max_documents": 1,
        }, fetcher=mock_fetch)
        self.assertEqual(report["status"], "REVIEW_REQUIRED")
        self.assertEqual(report["audit"]["ambiguous_block_count"], 1)
        self.assertTrue(report["bundle"]["sources"][0]["claims"])

    def test_exact_generation_discovery_outranks_generic_seed(self):
        index = PROVIDER_POLICIES["openai"]["index_urls"][0]
        exact = "https://developers.openai.com/api/docs/guides/gpt-x-migration.md"
        body = f"- [GPT-X migration guide]({exact})\n"

        def mock_fetch(provider: str, requested: str) -> dict:
            if requested == index:
                return fetched(index, body)
            raise IntakeError("secondary index unavailable")

        result = discover_document_urls("openai", ["gpt-x"], max_documents=1, fetcher=mock_fetch)
        self.assertEqual(result["urls"], [exact])

    def test_ready_report_never_grants_authority(self):
        url = "https://developers.openai.com/api/docs/models"

        def mock_fetch(provider: str, requested: str) -> dict:
            if requested == url:
                return fetched(url, "Context window is 128,000 tokens.")
            raise IntakeError("fixture index unavailable")

        report = build_intake_report({
            "provider": "openai",
            "product_surface": "api",
            "generation": "gpt-x",
            "captured_at": "2026-08-27T10:00:00Z",
            "explicit_urls": [url],
            "max_documents": 1,
        }, fetcher=mock_fetch)
        verify_intake_report(report)
        self.assertEqual(report["execution_authority"], "NONE")
        self.assertEqual(report["profile_application_authority"], "NONE")
        self.assertEqual(report["promotion_authority"], "NONE")
        self.assertEqual(report["hidden_architecture_claim"], "NONE")
        self.assertEqual(report["docs_claim_status"], "UNVERIFIED")

    def test_all_selected_document_failures_produce_failed_not_empty_ready(self):
        url = "https://developers.openai.com/api/docs/models"

        def mock_fetch(provider: str, requested: str) -> dict:
            raise IntakeError("offline")

        report = build_intake_report({
            "provider": "openai",
            "product_surface": "api",
            "generation": "gpt-x",
            "captured_at": "2026-08-27T10:00:00Z",
            "explicit_urls": [url],
            "max_documents": 1,
        }, fetcher=mock_fetch)
        self.assertEqual(report["status"], "FAILED")
        self.assertIsNone(report["bundle"])


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import hashlib
import unittest
import urllib.request

import official_docs_intake.core as core
from model_transition_intelligence.core import validate_bundle
from official_docs_intake import (
    IntakeError,
    PROVIDER_POLICIES,
    build_intake_report,
    discover_document_urls,
    extract_claims,
    normalize_visible_text,
    validate_official_url,
    verify_intake_report,
)


def fetched(url: str, body: str, content_type: str = "text/plain; charset=utf-8") -> dict:
    return {
        "requested_url": url,
        "final_url": url,
        "content_type": content_type,
        "body": body,
        "raw_sha256": hashlib.sha256(body.encode()).hexdigest(),
        "etag": '"fixture"',
        "last_modified": "Thu, 27 Aug 2026 00:00:00 GMT",
        "status": 200,
    }


class OfficialDocsIntakeTests(unittest.TestCase):
    def test_builtin_provider_policies_are_bounded(self):
        self.assertEqual(set(PROVIDER_POLICIES), {"openai", "anthropic", "google"})
        self.assertIn("developers.openai.com", PROVIDER_POLICIES["openai"]["official_hosts"])
        self.assertIn("platform.claude.com", PROVIDER_POLICIES["anthropic"]["official_hosts"])
        self.assertIn("ai.google.dev", PROVIDER_POLICIES["google"]["official_hosts"])
        for policy in PROVIDER_POLICIES.values():
            self.assertLessEqual(len(policy["index_urls"]), 2)
            self.assertLessEqual(len(policy["seed_urls"]), 2)

    def test_non_https_and_non_allowlisted_hosts_fail_closed(self):
        with self.assertRaises(IntakeError):
            validate_official_url("openai", "http://developers.openai.com/api/docs/models")
        with self.assertRaises(IntakeError):
            validate_official_url("openai", "https://example.com/openai-docs")
        with self.assertRaises(IntakeError):
            validate_official_url("google", "https://127.0.0.1/docs")

    def test_redirect_handler_revalidates_before_following(self):
        handler = core._AllowlistedRedirectHandler("openai")
        request = urllib.request.Request("https://developers.openai.com/api/docs/models")
        with self.assertRaises(IntakeError):
            handler.redirect_request(request, None, 302, "Found", {}, "https://example.com/steal")

    def test_html_normalizer_drops_script_style_and_navigation(self):
        body = """
        <html><head><style>.x{}</style><script>danger()</script></head>
        <body><nav>Pricing Context Tool Cache</nav><main>
        <h1>Model guide</h1><p>Context window is 1,050,000 tokens.</p>
        </main><footer>fake limit 2 tokens</footer></body></html>
        """
        content = normalize_visible_text(body, "text/html")
        self.assertIn("Model guide", content)
        self.assertIn("Context window is 1,050,000 tokens.", content)
        self.assertNotIn("danger", content)
        self.assertNotIn("fake limit", content)
        self.assertNotIn("Pricing Context Tool Cache", content)

    def test_claims_are_exact_anchors_and_h_compatible(self):
        url = "https://developers.openai.com/api/docs/guides/latest-model.md"
        body = "\n".join([
            "GPT-X supports a 1,050,000 token context window.",
            "Reasoning effort supports low, medium, high, xhigh, and max.",
            "Programmatic Tool Calling runs eligible tool calls in a hosted runtime.",
            "Explicit prompt caching is supported.",
        ])

        def mock_fetch(provider: str, requested: str) -> dict:
            if requested == url:
                return fetched(url, body)
            raise IntakeError("fixture index unavailable")

        report = build_intake_report({
            "provider": "openai",
            "product_surface": "responses-api",
            "generation": "gpt-x",
            "captured_at": "2026-08-27T10:00:00Z",
            "explicit_urls": [url],
            "query_terms": ["gpt-x"],
            "max_documents": 1,
        }, fetcher=mock_fetch)
        verify_intake_report(report)
        self.assertEqual(report["status"], "READY_FOR_H")
        bundle = report["bundle"]
        validate_bundle(bundle)
        source = bundle["sources"][0]
        self.assertEqual(source["behavior_status"], "UNVERIFIED")
        self.assertEqual(source["execution_authority"], "NONE")
        self.assertGreaterEqual(len(source["claims"]), 4)
        for claim in source["claims"]:
            self.assertIn(claim["anchor"], source["content"])
            self.assertEqual(claim["behavior_status"], "UNVERIFIED")

    def test_ambiguous_contract_signal_requires_review(self):
        url = "https://developers.openai.com/api/docs/models"
        body = "Requests now pass through a novel coordination plane before completion."

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
        self.assertEqual(report["bundle"]["sources"][0]["claims"], [])

    def test_partial_fetch_failure_preserves_success_and_is_not_ready(self):
        good = "https://developers.openai.com/api/docs/models"
        bad = "https://developers.openai.com/api/docs/guides/latest-model.md"

        def mock_fetch(provider: str, requested: str) -> dict:
            if requested == good:
                return fetched(good, "Context window is 128,000 tokens.")
            raise IntakeError("network fixture failure")

        report = build_intake_report({
            "provider": "openai",
            "product_surface": "api",
            "generation": "gpt-x",
            "captured_at": "2026-08-27T10:00:00Z",
            "explicit_urls": [good, bad],
            "max_documents": 2,
        }, fetcher=mock_fetch)
        self.assertEqual(report["status"], "REVIEW_REQUIRED")
        self.assertEqual(len(report["bundle"]["sources"]), 1)
        self.assertEqual(len(report["audit"]["fetch_failures"]), 1)

    def test_discovery_is_deduplicated_allowlisted_and_capped(self):
        index = PROVIDER_POLICIES["openai"]["index_urls"][0]
        links = "\n".join(
            f"- [GPT-X model guide {i}](https://developers.openai.com/api/docs/models/gpt-x-{i}.md)"
            for i in range(20)
        )

        def mock_fetch(provider: str, requested: str) -> dict:
            if requested == index:
                return fetched(index, links)
            raise IntakeError("secondary index unavailable")

        result = discover_document_urls("openai", ["gpt-x"], max_documents=3, fetcher=mock_fetch)
        self.assertEqual(len(result["urls"]), 3)
        self.assertEqual(len(result["urls"]), len(set(result["urls"])))
        for url in result["urls"]:
            self.assertEqual(validate_official_url("openai", url), url)

    def test_extract_claims_separates_marketing_from_contract(self):
        claims, audit = extract_claims("State-of-the-art frontier-class intelligence for everyone.")
        self.assertEqual(audit["coverage_state"], "COVERED")
        self.assertTrue(any(claim["kind"] == "MARKETING" for claim in claims))


if __name__ == "__main__":
    unittest.main()

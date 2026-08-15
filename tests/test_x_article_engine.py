import pytest

from x_article_engine import XArticleEngineError, audit_draft, build_generation_packet



def bridgepatch_brief(article_type="HOW_TO"):
    return {
        "offer": "BridgePatch: one bounded manual workflow step is assessed first, then optionally specified and implemented.",
        "target": "A small business owner repeating manual transfer, aggregation, checking, or drafting work every week.",
        "pain": "AI seems useful, but they do not know how to describe the work safely or what to automate first.",
        "primary_info": [
            {
                "claim": "During Vlog-tool development, supporting test, debug, operation-recording, and repair mechanisms kept expanding around the original tool; I called this tendency シムシティ化.",
                "source_ref": "human_attestation:bridgepatch-origin",
                "attested": True,
            }
        ],
        "article_type": article_type,
        "topic_mode": "BUSINESS",
        "cta": "Use the free BridgePatch fit check.",
        "evidence": [
            {
                "claim": "The BridgePatch provisional implementation design document costs 10,000円 including tax and does not include tool implementation.",
                "source_ref": "bridgepatch-sales-page",
                "status": "VERIFIED",
                "kind": "COMMERCIAL",
            },
            {
                "claim": "A simple one-action tool is standard 50,000円 including tax, with scope, total price, and timing agreed before start.",
                "source_ref": "bridgepatch-sales-page",
                "status": "VERIFIED",
                "kind": "COMMERCIAL",
            },
            {
                "claim": "The design document is normally delivered within 5営業日 after required information is available.",
                "source_ref": "bridgepatch-sales-page",
                "status": "VERIFIED",
                "kind": "TIMING",
            },
        ],
    }



def test_build_packet_preserves_human_and_evidence_boundaries():
    packet = build_generation_packet(bridgepatch_brief())

    assert packet["article_type"] == "HOW_TO"
    assert packet["opening_mode"] == "RELATABLE"
    assert packet["human_gate"]["required"] is True
    assert packet["external_publication_performed"] is False
    assert len(packet["verified_primary_info"]) == 1
    assert len(packet["verified_evidence"]) == 3



def test_story_requires_human_attested_primary_information():
    source = bridgepatch_brief("STORY")
    source["primary_info"][0]["attested"] = False

    with pytest.raises(XArticleEngineError, match="STORY requires"):
        build_generation_packet(source)



def test_case_result_requires_verified_result_evidence():
    with pytest.raises(XArticleEngineError, match="CASE_RESULT requires"):
        build_generation_packet(bridgepatch_brief("CASE_RESULT"))



def test_case_result_accepts_bound_result_evidence():
    source = bridgepatch_brief("CASE_RESULT")
    source["evidence"].append(
        {
            "claim": "A verified customer case reduced the target step from 20分 to 5分.",
            "source_ref": "customer-case-001",
            "status": "VERIFIED",
            "kind": "CASE_RESULT",
        }
    )

    packet = build_generation_packet(source)
    assert packet["article_type"] == "CASE_RESULT"
    assert packet["opening_mode"] == "PROOF_FIRST"



def test_unverified_evidence_is_excluded_and_forces_review():
    source = bridgepatch_brief()
    source["evidence"].append(
        {
            "claim": "Customers save 90% of their time.",
            "source_ref": "unsupported",
            "status": "UNVERIFIED",
            "kind": "RESULT",
        }
    )

    packet = build_generation_packet(source)
    assert packet["review_state"] == "REVIEW_REQUIRED"
    assert all("90%" not in item["claim"] for item in packet["verified_evidence"])



def test_audit_blocks_invented_numeric_claims():
    packet = build_generation_packet(bridgepatch_brief())
    draft = (
        "毎週2時間かかる作業を見直します。"
        "設計書は10,000円、実装は50,000円が標準で、通常5営業日です。"
    )

    audit = audit_draft(draft, packet)
    assert audit["status"] == "BLOCKED"
    assert any(
        item["code"] == "UNBOUND_NUMERIC_CLAIM" and item["detail"] == "2時間"
        for item in audit["findings"]
    )



def test_audit_allows_bound_numeric_claims_but_still_requires_human_review():
    packet = build_generation_packet(bridgepatch_brief())
    draft = "設計書は10,000円、実装は50,000円が標準で、通常5営業日です。"

    audit = audit_draft(draft, packet)
    assert audit["status"] == "HUMAN_REVIEW_REQUIRED"
    assert audit["findings"] == []
    assert audit["human_review_required"] is True



def test_audit_blocks_strengthened_commercial_promise():
    packet = build_generation_packet(bridgepatch_brief())
    draft = "開始後は追加料金が発生しません。"

    audit = audit_draft(draft, packet)
    assert audit["status"] == "BLOCKED"
    assert any(item["code"] == "UNBOUND_STRONG_CLAIM" for item in audit["findings"])

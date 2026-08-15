import pytest

from x_article_engine import XArticleEngineError, audit_draft, build_generation_packet


def bridgepatch_brief(article_type="HOW_TO"):
    return {
        "offer": "BridgePatch。まず無料で適合確認し、必要なら一工程の設計と実装へ進む。",
        "target": "毎週、転記・集計・確認・下書きを手作業している小規模事業者。",
        "pain": "AIは使えそうだが、安全に何を自動化するか説明できない。",
        "primary_info": [
            {
                "claim": "Vlogツール開発では、本体の周囲にテスト、デバッグ、操作記録、修復の仕組みが増えていった。私はこの傾向をシムシティ化と呼んでいた。",
                "source_ref": "human_attestation:bridgepatch-origin",
                "attested": True,
                "kind": "EXPERIENCE",
            }
        ],
        "article_type": article_type,
        "topic_mode": "BUSINESS",
        "cta": "BridgePatchの無料適合確認を使う。",
        "source_refs": [
            {
                "id": "bridgepatch-sales-page",
                "status": "VERIFIED",
                "kind": "PUBLIC_PAGE",
            }
        ],
        "evidence": [
            {
                "claim": "暫定ツール実装設計書は10,000円（税込）で、ツール実装は含まない。",
                "source_ref": "bridgepatch-sales-page",
                "status": "VERIFIED",
                "kind": "COMMERCIAL",
            },
            {
                "claim": "1アクション簡易ツールは50,000円（税込）が標準で、対象範囲・総額・納期は開始前に確定する。",
                "source_ref": "bridgepatch-sales-page",
                "status": "VERIFIED",
                "kind": "COMMERCIAL",
            },
            {
                "claim": "必要情報が揃ってから通常5営業日以内を目安に設計書を納品する。",
                "source_ref": "bridgepatch-sales-page",
                "status": "VERIFIED",
                "kind": "TIMING",
            },
        ],
    }


def test_build_packet_preserves_human_and_evidence_boundaries():
    packet = build_generation_packet(bridgepatch_brief())
    assert packet["schema_version"] == "0.2"
    assert packet["article_type"] == "HOW_TO"
    assert packet["opening_mode"] == "RELATABLE"
    assert packet["human_gate"]["required"] is True
    assert packet["publication_state"] == "BLOCKED_PENDING_HUMAN"
    assert packet["publication_authority"] == "USER_ONLY"
    assert packet["external_publication_performed"] is False
    assert len(packet["verified_primary_info"]) == 1
    assert len(packet["verified_evidence"]) == 3
    assert len(packet["verified_source_refs"]) == 1


def test_story_requires_human_attested_primary_information():
    source = bridgepatch_brief("STORY")
    source["primary_info"][0]["attested"] = False
    with pytest.raises(XArticleEngineError, match="STORY requires"):
        build_generation_packet(source)


def test_primary_info_cannot_masquerade_as_result_evidence():
    source = bridgepatch_brief()
    source["primary_info"][0]["kind"] = "CASE_RESULT"
    with pytest.raises(XArticleEngineError, match="primary_info"):
        build_generation_packet(source)


def test_case_result_requires_verified_result_evidence():
    with pytest.raises(XArticleEngineError, match="CASE_RESULT requires"):
        build_generation_packet(bridgepatch_brief("CASE_RESULT"))


def test_case_result_accepts_bound_result_evidence():
    source = bridgepatch_brief("CASE_RESULT")
    source["source_refs"].append(
        {"id": "customer-case-001", "status": "VERIFIED", "kind": "CASE"}
    )
    source["evidence"].append(
        {
            "claim": "確認済みの顧客事例では対象工程が20分から5分になった。",
            "source_ref": "customer-case-001",
            "status": "VERIFIED",
            "kind": "CASE_RESULT",
        }
    )
    packet = build_generation_packet(source)
    assert packet["article_type"] == "CASE_RESULT"
    assert packet["opening_mode"] == "PROOF_FIRST"


def test_undeclared_verified_source_is_not_trusted():
    source = bridgepatch_brief()
    source["evidence"].append(
        {
            "claim": "顧客の作業時間が90%減った。",
            "source_ref": "made-up-source",
            "status": "VERIFIED",
            "kind": "RESULT",
        }
    )
    packet = build_generation_packet(source)
    assert packet["review_state"] == "REVIEW_REQUIRED"
    assert all("90%" not in item["claim"] for item in packet["verified_evidence"])


def test_unverified_declared_source_is_not_trusted():
    source = bridgepatch_brief()
    source["source_refs"].append(
        {"id": "rumor", "status": "UNVERIFIED", "kind": "NOTE"}
    )
    source["evidence"].append(
        {
            "claim": "顧客の作業時間が90%減った。",
            "source_ref": "rumor",
            "status": "VERIFIED",
            "kind": "RESULT",
        }
    )
    packet = build_generation_packet(source)
    assert packet["review_state"] == "REVIEW_REQUIRED"
    assert all("90%" not in item["claim"] for item in packet["verified_evidence"])


def test_audit_blocks_invented_numeric_claims():
    packet = build_generation_packet(bridgepatch_brief())
    draft = "毎週2時間かかる作業。設計書は10,000円、実装は50,000円が標準で、通常5営業日。"
    audit = audit_draft(draft, packet)
    assert audit["status"] == "BLOCKED"
    assert any(
        item["code"] == "UNBOUND_NUMERIC_CLAIM" and item["detail"] == "2時間"
        for item in audit["findings"]
    )


def test_audit_normalizes_full_width_digits_before_checking():
    packet = build_generation_packet(bridgepatch_brief())
    audit = audit_draft("毎週２時間かかります。", packet)
    assert audit["status"] == "BLOCKED"
    assert any(item["detail"] == "2時間" for item in audit["findings"])


def test_audit_allows_bound_numeric_claims_but_still_requires_human_review():
    packet = build_generation_packet(bridgepatch_brief())
    draft = "設計書は10,000円、実装は50,000円が標準で、通常5営業日です。"
    audit = audit_draft(draft, packet)
    assert audit["status"] == "HUMAN_REVIEW_REQUIRED"
    assert audit["findings"] == []
    assert audit["human_review_required"] is True
    assert audit["publication_state"] == "BLOCKED_PENDING_HUMAN"


def test_audit_blocks_strengthened_commercial_promise():
    packet = build_generation_packet(bridgepatch_brief())
    audit = audit_draft("開始後は追加料金が発生しません。", packet)
    assert audit["status"] == "BLOCKED"
    assert any(item["code"] == "UNBOUND_STRONG_CLAIM" for item in audit["findings"])

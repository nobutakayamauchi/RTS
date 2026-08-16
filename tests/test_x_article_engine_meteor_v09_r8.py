import pytest

from x_article_engine.core import XArticleEngineError
from x_article_engine.meteor_v09_r8 import audit_draft, build_generation_packet


def sources():
    return [
        {"id": "sales", "status": "VERIFIED", "kind": "PUBLIC_PAGE"},
        {"id": "timing", "status": "VERIFIED", "kind": "OFFICIAL"},
        {"id": "risk-a", "status": "VERIFIED", "kind": "OFFICIAL"},
        {"id": "risk-b", "status": "VERIFIED", "kind": "OFFICIAL"},
    ]


def brief(**overrides):
    data = {
        "offer": "BridgePatch。まず無料で適合確認し、必要なら一工程の設計へ進む。",
        "target": "毎週、転記・集計・確認・下書きを手作業している小規模事業者。",
        "pain": "AIは使えそうだが、安全に何を自動化するか説明できない。",
        "primary_info": [
            {
                "claim": "あー、めんどくさくてキレそう。",
                "source_ref": "human_attestation:pain",
                "attested": True,
                "kind": "PAIN",
            }
        ],
        "article_type": "STORY",
        "topic_mode": "BUSINESS",
        "cta": "BridgePatchの無料適合確認を使う。",
        "product_name": "BridgePatch",
        "product_reading": "ブリッジパッチ",
        "evidence": [
            {
                "claim": "暫定ツール実装設計書は10,000円（税込）で、ツール実装は含まない。",
                "source_ref": "sales",
                "status": "VERIFIED",
                "kind": "COMMERCIAL",
            }
        ],
    }
    data.update(overrides)
    return data


def current_with_timing(**overrides):
    data = brief(freshness_mode="CURRENT", as_of="2026-08-16")
    data["evidence"] = [
        *data["evidence"],
        {
            "claim": "この仕様は2026年8月16日時点の公開仕様に基づく。",
            "source_ref": "timing",
            "status": "VERIFIED",
            "kind": "TIMING",
        },
    ]
    data.update(overrides)
    return data


def high_risk(**overrides):
    data = brief(risk_level="HIGH", topic_mode="PROCEDURAL")
    data["evidence"] = [
        *data["evidence"],
        {
            "claim": "権限を広げる操作では、誤操作時の影響範囲が大きくなる。",
            "source_ref": "risk-a",
            "status": "VERIFIED",
            "kind": "RISK",
        },
    ]
    data.update(overrides)
    return data


def codes(result):
    return {item["code"] for item in result["findings"]}


def test_r8_schema_and_purpose_binding_policy_present():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    assert packet["schema_version"] == "0.9-meteor-r8"
    assert "evidence_purpose_binding_policy" in packet


def test_current_mode_requires_explicit_freshness_evidence_refs():
    data = current_with_timing()
    with pytest.raises(XArticleEngineError, match="freshness_evidence_refs requires"):
        build_generation_packet(data, trusted_source_refs=sources())


def test_unrelated_dated_commercial_fact_cannot_authorize_currentness():
    data = brief(freshness_mode="CURRENT", as_of="2026-08-16")
    data["evidence"] = [
        {
            "claim": "2026年8月16日時点で設計書は10,000円だった。",
            "source_ref": "sales",
            "status": "VERIFIED",
            "kind": "COMMERCIAL",
        }
    ]
    data["freshness_evidence_refs"] = ["sales"]
    with pytest.raises(XArticleEngineError, match="must resolve to verified evidence of kind TIMING"):
        build_generation_packet(data, trusted_source_refs=sources())


def test_bound_verified_timing_ref_authorizes_current_mode():
    data = current_with_timing(freshness_evidence_refs=["timing"])
    packet = build_generation_packet(data, trusted_source_refs=sources())
    assert packet["freshness"]["evidence_refs"] == ["timing"]
    assert packet["freshness"]["bound_evidence"][0]["kind"] == "TIMING"


def test_unknown_freshness_ref_fails_closed():
    data = current_with_timing(freshness_evidence_refs=["not-there"])
    with pytest.raises(XArticleEngineError, match="not-there"):
        build_generation_packet(data, trusted_source_refs=sources())


def test_evergreen_article_with_random_timing_evidence_still_reviews_latest_wording():
    data = brief()
    data["evidence"] = [
        *data["evidence"],
        {
            "claim": "別の出来事が2026年8月16日に起きた。",
            "source_ref": "timing",
            "status": "VERIFIED",
            "kind": "TIMING",
        },
    ]
    packet = build_generation_packet(data, trusted_source_refs=sources())
    result = audit_draft("BridgePatch（ブリッジパッチ）の最新版を説明します。", packet)
    assert "FRESHNESS_CLAIM_WITHOUT_BOUND_EVIDENCE" in codes(result)


def test_current_article_with_bound_timing_ref_does_not_get_bound_evidence_review():
    packet = build_generation_packet(
        current_with_timing(freshness_evidence_refs=["timing"]),
        trusted_source_refs=sources(),
    )
    result = audit_draft("BridgePatch（ブリッジパッチ）の現在の仕様を説明します。", packet)
    assert "FRESHNESS_CLAIM_WITHOUT_BOUND_EVIDENCE" not in codes(result)


def test_high_risk_mode_requires_explicit_risk_evidence_refs():
    with pytest.raises(XArticleEngineError, match="risk_evidence_refs requires"):
        build_generation_packet(high_risk(), trusted_source_refs=sources())


def test_commercial_ref_cannot_be_used_as_risk_binding():
    data = high_risk(risk_evidence_refs=["sales"])
    with pytest.raises(XArticleEngineError, match="must resolve to verified evidence of kind"):
        build_generation_packet(data, trusted_source_refs=sources())


def test_bound_verified_risk_ref_authorizes_high_risk_mode():
    packet = build_generation_packet(
        high_risk(risk_evidence_refs=["risk-a"]),
        trusted_source_refs=sources(),
    )
    assert packet["risk_policy"]["evidence_refs"] == ["risk-a"]
    assert packet["risk_policy"]["bound_evidence"][0]["kind"] == "RISK"


def test_unrelated_second_risk_ref_is_not_silently_substituted_for_requested_ref():
    data = high_risk(risk_evidence_refs=["risk-b"])
    data["evidence"] = [
        *data["evidence"],
        {
            "claim": "別の操作ではAPIキー漏洩の危険がある。",
            "source_ref": "risk-b",
            "status": "VERIFIED",
            "kind": "RISK",
        },
    ]
    packet = build_generation_packet(data, trusted_source_refs=sources())
    assert packet["risk_policy"]["evidence_refs"] == ["risk-b"]
    assert all(item["source_ref"] == "risk-b" for item in packet["risk_policy"]["bound_evidence"])
    # Semantic match between that bound evidence and the exact warning still remains a /human check.
    checks = "\n".join(packet["human_gate"]["checks"])
    assert "本文で警告している具体的な危険" in checks

import pytest

from x_article_engine.core import XArticleEngineError
from x_article_engine.meteor_v09_r4 import audit_draft, build_generation_packet


def sources():
    return [
        {"id": "sales", "status": "VERIFIED", "kind": "PUBLIC_PAGE"},
        {"id": "counter", "status": "VERIFIED", "kind": "REPORT"},
    ]


def base_primary():
    return [
        {
            "claim": "私はこの仕事を始めた。",
            "source_ref": "human_attestation:origin",
            "attested": True,
            "kind": "ORIGIN",
        }
    ]


def brief(**overrides):
    data = {
        "offer": "BridgePatch。まず無料で適合確認し、必要なら一工程の設計へ進む。",
        "target": "毎週、転記・集計・確認・下書きを手作業している小規模事業者。",
        "pain": "AIは使えそうだが、安全に何を自動化するか説明できない。",
        "primary_info": base_primary(),
        "article_type": "STORY",
        "topic_mode": "BUSINESS",
        "cta": "BridgePatchの無料適合確認を使う。",
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


def codes(result):
    return [item["code"] for item in result["findings"]]


def test_origin_alone_no_longer_auto_activates_lived_pain_in_latest_layer():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    assert packet["schema_version"] == "0.9-meteor-r4"
    assert packet["opening_mode"] == "RELATABLE"
    assert packet["lived_pain_anchors"] == []
    assert "manufacture pain" in packet["narrative"]["opening_doctrine"]


def test_explicit_lived_pain_with_origin_only_fails_closed():
    with pytest.raises(XArticleEngineError, match="PAIN or FAILURE"):
        build_generation_packet(
            brief(opening_mode="LIVED_PAIN"),
            trusted_source_refs=sources(),
        )


def test_attested_pain_still_activates_lived_pain():
    data = brief()
    data["primary_info"] = [
        {
            "claim": "あー、めんどくさくてキレそう。",
            "source_ref": "human_attestation:pain",
            "attested": True,
            "kind": "PAIN",
        },
        *base_primary(),
    ]
    packet = build_generation_packet(data, trusted_source_refs=sources())
    assert packet["opening_mode"] == "LIVED_PAIN"
    assert any(item["kind"] == "PAIN" for item in packet["lived_pain_anchors"])


def test_explicit_lived_pain_with_attested_failure_is_allowed():
    data = brief(opening_mode="LIVED_PAIN")
    data["primary_info"] = [
        {
            "claim": "試して失敗し、そこで手が止まった。",
            "source_ref": "human_attestation:failure",
            "attested": True,
            "kind": "FAILURE",
        }
    ]
    packet = build_generation_packet(data, trusted_source_refs=sources())
    assert packet["opening_mode"] == "LIVED_PAIN"


def test_contrarian_without_explicit_basis_fails_closed():
    with pytest.raises(XArticleEngineError, match="counterpoint_basis"):
        build_generation_packet(
            brief(opening_mode="CONTRARIAN"),
            trusted_source_refs=sources(),
        )


def test_contrarian_can_bind_human_opinion_basis():
    data = brief(opening_mode="CONTRARIAN")
    data["primary_info"] = [
        {
            "claim": "全部自動化するより、一工程だけ切る方がいいと私は考えている。",
            "source_ref": "human_attestation:counterpoint",
            "attested": True,
            "kind": "OPINION",
        }
    ]
    data["counterpoint_basis"] = {
        "kind": "HUMAN_OPINION",
        "source_ref": "human_attestation:counterpoint",
    }
    packet = build_generation_packet(data, trusted_source_refs=sources())
    assert packet["opening_mode"] == "CONTRARIAN"


def test_contrarian_can_bind_verified_evidence_basis():
    data = brief(opening_mode="CONTRARIAN")
    data["evidence"] = [
        *data["evidence"],
        {
            "claim": "比較資料では、対象工程だけを切り出した方式に別の運用上の利点が確認された。",
            "source_ref": "counter",
            "status": "VERIFIED",
            "kind": "FACT",
        },
    ]
    data["counterpoint_basis"] = {
        "kind": "EVIDENCE",
        "source_ref": "counter",
    }
    packet = build_generation_packet(data, trusted_source_refs=sources())
    assert packet["opening_mode"] == "CONTRARIAN"


def test_fake_human_counterpoint_ref_does_not_pass():
    data = brief(opening_mode="CONTRARIAN")
    data["counterpoint_basis"] = {
        "kind": "HUMAN_OPINION",
        "source_ref": "human_attestation:not-present",
    }
    with pytest.raises(XArticleEngineError, match="counterpoint_basis"):
        build_generation_packet(data, trusted_source_refs=sources())


def test_operational_platform_evasion_instruction_is_blocked():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    result = audit_draft("BAN回避のためにゼロ幅文字をメッセージへ挿入して配信します。", packet)
    assert "PLATFORM_EVASION_OPERATIONAL_INSTRUCTION" in codes(result)
    assert result["status"] == "BLOCKED"


def test_platform_evasion_discussion_without_howto_is_reviewed():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    result = audit_draft("BAN回避を目的にしたステルス配信という主張がありますが、この記事では推奨しません。", packet)
    assert "PLATFORM_EVASION_OPERATIONAL_INSTRUCTION" not in codes(result)
    assert "PLATFORM_EVASION_LANGUAGE" in codes(result)


def test_opening_integrity_human_checks_are_present():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    checks = "\n".join(packet["human_gate"]["checks"])
    assert "neutral origin into drama" in checks
    assert "contrarian" in checks
    assert "evade enforcement" in checks

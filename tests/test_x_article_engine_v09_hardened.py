import pytest

from x_article_engine import audit_draft as root_audit
from x_article_engine import build_generation_packet as root_build
from x_article_engine.core import XArticleEngineError
from x_article_engine import meteor_v09_r8 as attack
from x_article_engine import v09_hardened as hardened


def sources():
    return [
        {"id": "sales", "status": "VERIFIED", "kind": "PUBLIC_PAGE"},
        {"id": "timing", "status": "VERIFIED", "kind": "OFFICIAL"},
        {"id": "risk", "status": "VERIFIED", "kind": "OFFICIAL"},
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


def current_brief():
    data = brief(
        freshness_mode="CURRENT",
        as_of="2026-08-16",
        freshness_evidence_refs=["timing"],
    )
    data["evidence"] = [
        *data["evidence"],
        {
            "claim": "この仕様は2026年8月16日時点の公開仕様に基づく。",
            "source_ref": "timing",
            "status": "VERIFIED",
            "kind": "TIMING",
        },
    ]
    return data


def high_risk_brief():
    data = brief(
        risk_level="HIGH",
        topic_mode="PROCEDURAL",
        risk_evidence_refs=["risk"],
    )
    data["evidence"] = [
        *data["evidence"],
        {
            "claim": "権限を広げる操作では、誤操作時の影響範囲が大きくなる。",
            "source_ref": "risk",
            "status": "VERIFIED",
            "kind": "RISK",
        },
    ]
    return data


def codes(result):
    return {item["code"] for item in result["findings"]}


def test_package_root_is_hardened_v09_not_attack_stack():
    packet = root_build(brief(), trusted_source_refs=sources())
    assert packet["schema_version"] == "0.9"
    assert "negated_claim_policy" in packet
    assert "polarity_policy" in packet
    assert "evidence_purpose_binding_policy" in packet


def test_root_and_hardened_are_same_runtime_contract():
    direct = hardened.build_generation_packet(brief(), trusted_source_refs=sources())
    root = root_build(brief(), trusted_source_refs=sources())
    assert root["schema_version"] == direct["schema_version"] == "0.9"
    assert root["opening_mode"] == direct["opening_mode"]
    assert root["publication_authority"] == direct["publication_authority"] == "USER_ONLY"
    assert root["publication_state"] == direct["publication_state"] == "BLOCKED_PENDING_HUMAN"


@pytest.mark.parametrize(
    "draft,code",
    [
        (
            "BridgePatch（ブリッジパッチ）を使っても、必ず成功するとは限りません。",
            None,
        ),
        (
            "BridgePatch（ブリッジパッチ）の全工程が完全無料ではありません。",
            None,
        ),
        (
            "BridgePatch（ブリッジパッチ）の作業が30分で終わるとは言いません。",
            None,
        ),
        (
            "BridgePatch（ブリッジパッチ）の記事です。APIキーをClaudeに送ってはいけません。",
            None,
        ),
        (
            "BridgePatch（ブリッジパッチ）の記事です。APIキーをClaudeに送ってください。",
            "SECRET_TRANSFER_TO_MODEL_RISK",
        ),
    ],
)
def test_hardened_absorbs_negation_and_polarity_behavior(draft, code):
    packet = root_build(brief(), trusted_source_refs=sources())
    result = root_audit(draft, packet)
    if code is None:
        assert "SECRET_TRANSFER_TO_MODEL_RISK" not in codes(result)
        assert "UNBOUND_ABSOLUTE_FREE_CLAIM" not in codes(result)
        assert "UNBOUND_NUMERIC_CLAIM" not in codes(result)
        assert not any(
            item["code"] == "UNBOUND_STRONG_CLAIM" and item["detail"] in {"必ず", "絶対"}
            for item in result["findings"]
        )
    else:
        assert code in codes(result)
        assert result["status"] == "BLOCKED"


def test_hardened_high_risk_front_gate_rejects_negated_risk_spoof():
    packet = root_build(high_risk_brief(), trusted_source_refs=sources())
    result = root_audit(
        "リスクはありません。BridgePatch（ブリッジパッチ）の手順です。\n"
        "手順1 設定します。\n手順2 実行します。\n手順3 完了を確認します。",
        packet,
    )
    assert "HIGH_RISK_WITHOUT_FRONT_STOP_GATE" in codes(result)
    assert result["status"] == "BLOCKED"


def test_hardened_high_risk_real_warning_passes_front_gate():
    packet = root_build(high_risk_brief(), trusted_source_refs=sources())
    result = root_audit(
        "警告：この操作は権限を広げるため、誤操作時の影響範囲が大きくなります。対象外なら進めないでください。\n"
        "BridgePatch（ブリッジパッチ）の手順です。なぜ確認するか。失敗範囲を小さくするためです。\n"
        "手順1 設定します。完了を確認してください。\n"
        "手順2 実行します。エラーなら停止して戻ります。\n"
        "手順3 成功表示を確認します。",
        packet,
    )
    assert "HIGH_RISK_WITHOUT_FRONT_STOP_GATE" not in codes(result)


def test_hardened_requires_bound_freshness_refs_at_root():
    data = current_brief()
    data.pop("freshness_evidence_refs")
    with pytest.raises(XArticleEngineError, match="freshness_evidence_refs requires"):
        root_build(data, trusted_source_refs=sources())


def test_hardened_current_with_bound_timing_ref_is_clean_for_binding_gate():
    packet = root_build(current_brief(), trusted_source_refs=sources())
    result = root_audit(
        "BridgePatch（ブリッジパッチ）の現在の仕様を説明します。",
        packet,
    )
    assert "FRESHNESS_CLAIM_WITHOUT_BOUND_EVIDENCE" not in codes(result)


def test_hardened_requires_bound_risk_refs_at_root():
    data = high_risk_brief()
    data.pop("risk_evidence_refs")
    with pytest.raises(XArticleEngineError, match="risk_evidence_refs requires"):
        root_build(data, trusted_source_refs=sources())


def test_hardened_and_r8_agree_on_key_attack_statuses():
    data = brief()
    attack_packet = attack.build_generation_packet(data, trusted_source_refs=sources())
    hard_packet = hardened.build_generation_packet(data, trusted_source_refs=sources())
    drafts = [
        "BridgePatch（ブリッジパッチ）は完全無料で使えます。",
        "BridgePatch（ブリッジパッチ）の作業が30分で終わるとは言いません。",
        "BridgePatch（ブリッジパッチ）の話です。BAN回避のためにゼロ幅文字を挿入して配信します。",
        "BridgePatch（ブリッジパッチ）の話です。多くの人は仕事の本質を理解していません。",
    ]
    for draft in drafts:
        attack_result = attack.audit_draft(draft, attack_packet)
        hard_result = hardened.audit_draft(draft, hard_packet)
        assert attack_result["status"] == hard_result["status"]
        assert codes(attack_result) == codes(hard_result)

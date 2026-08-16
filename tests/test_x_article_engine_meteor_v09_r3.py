import pytest

from x_article_engine.core import XArticleEngineError
from x_article_engine.meteor_v09_gate import audit_draft, build_generation_packet


def sources():
    return [
        {"id": "sales", "status": "VERIFIED", "kind": "PUBLIC_PAGE"},
        {"id": "risk", "status": "VERIFIED", "kind": "OFFICIAL"},
        {"id": "dated", "status": "VERIFIED", "kind": "OFFICIAL"},
    ]


def brief(**overrides):
    data = {
        "offer": "BridgePatch。まず無料で適合確認し、必要なら一工程の設計へ進む。",
        "target": "毎週、転記・集計・確認・下書きを手作業している小規模事業者。",
        "pain": "AIは使えそうだが、安全に何を自動化するか説明できない。",
        "primary_info": [
            {
                "claim": "あー、めんどくさくてキレそう。自前のプログラムの無限修正に頭を抱えた。",
                "source_ref": "human_attestation:pain",
                "attested": True,
                "kind": "PAIN",
            }
        ],
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


def risk_brief(**overrides):
    data = brief(risk_level="HIGH", topic_mode="PROCEDURAL")
    data["evidence"] = [
        *data["evidence"],
        {
            "claim": "この操作は権限を広げるため、誤操作時の影響範囲が大きくなる。",
            "source_ref": "risk",
            "status": "VERIFIED",
            "kind": "RISK",
        },
    ]
    data.update(overrides)
    return data


def codes(result):
    return [item["code"] for item in result["findings"]]


def test_r3_schema_and_strong_language_policy_present():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    assert packet["schema_version"] == "0.9-meteor-r3"
    assert set(packet["strong_language_policy"]) == {
        "outcome_absolute",
        "general_absolute",
        "safety_imperative",
    }
    assert "hardcoded_secret_rule" in packet["security_content_policy"]


def test_high_risk_warning_tone_without_verified_risk_evidence_fails_closed():
    with pytest.raises(XArticleEngineError, match="HIGH-risk articles require"):
        build_generation_packet(
            brief(risk_level="HIGH", topic_mode="PROCEDURAL"),
            trusted_source_refs=sources(),
        )


def test_high_risk_with_verified_risk_evidence_builds():
    packet = build_generation_packet(risk_brief(), trusted_source_refs=sources())
    assert packet["risk_policy"]["risk_level"] == "HIGH"
    assert "verified RISK/SAFETY/POLICY" in packet["risk_policy"]["evidence_rule"]


def test_as_of_in_evergreen_mode_does_not_silence_latest_review():
    packet = build_generation_packet(
        brief(as_of="2026-08-16"),
        trusted_source_refs=sources(),
    )
    result = audit_draft("これは最新版の方法です。", packet)
    assert "FRESHNESS_CLAIM_WITHOUT_DATED_EVIDENCE" in codes(result)


def test_current_mode_with_verified_timing_evidence_allows_current_wording():
    data = brief(freshness_mode="CURRENT", as_of="2026-08-16")
    data["evidence"] = [
        *data["evidence"],
        {
            "claim": "この仕様は2026年8月16日時点の公式情報で確認した。",
            "source_ref": "dated",
            "status": "VERIFIED",
            "kind": "TIMING",
        },
    ]
    packet = build_generation_packet(data, trusted_source_refs=sources())
    result = audit_draft("これは現在の仕様です。", packet)
    assert "FRESHNESS_CLAIM_WITHOUT_DATED_EVIDENCE" not in codes(result)


def test_outcome_absolute_remains_blocked():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    result = audit_draft("この方法なら必ず自動化できます。", packet)
    assert "UNBOUND_STRONG_CLAIM" in codes(result)
    assert result["status"] == "BLOCKED"


def test_non_outcome_absolute_prediction_is_downgraded_to_review():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    result = audit_draft("ここで初心者は必ず次の壁にぶつかります。", packet)
    assert "UNBOUND_STRONG_CLAIM" not in codes(result)
    assert "ABSOLUTE_GENERALIZATION_LANGUAGE" in codes(result)
    assert result["status"] == "HUMAN_REVIEW_REQUIRED"


def test_safety_absolute_is_allowed_without_commercial_guarantee_block():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    result = audit_draft("APIキーは絶対に共有しないでください。権限は必ず確認してください。", packet)
    assert not any(
        item["code"] == "UNBOUND_STRONG_CLAIM" and item["detail"] in {"必ず", "絶対"}
        for item in result["findings"]
    )


def test_universal_capability_promise_is_reviewed():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    result = audit_draft("初心者でもこの記事だけでできます。", packet)
    assert "UNIVERSAL_CAPABILITY_PROMISE" in codes(result)


def test_hardcoded_default_secret_is_blocked():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    result = audit_draft("管理画面用APIキーは sk-line-harness-2026 をこのまま使って設定してください。", packet)
    assert "HARDCODED_SECRET_LITERAL_RISK" in codes(result)
    assert result["status"] == "BLOCKED"


def test_dummy_secret_example_is_not_blocked_as_real_default():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    result = audit_draft("例のダミーAPIキー sk-example-placeholder は実際には使わないでください。", packet)
    assert "HARDCODED_SECRET_LITERAL_RISK" not in codes(result)


def test_platform_evasion_language_is_reviewed_not_learned_as_growth_doctrine():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    result = audit_draft("BAN回避のためにステルス配信とゼロ幅文字を使います。", packet)
    assert "PLATFORM_EVASION_LANGUAGE" in codes(result)


def test_risk_article_still_requires_front_stop_gate_after_risk_evidence_exists():
    packet = build_generation_packet(risk_brief(), trusted_source_refs=sources())
    result = audit_draft("手順1 権限を開きます。\n手順2 設定します。\n手順3 実行します。", packet)
    assert "HIGH_RISK_WITHOUT_FRONT_STOP_GATE" in codes(result)
    assert result["status"] == "BLOCKED"


def test_risk_article_with_evidence_and_front_gate_can_reach_human_review():
    packet = build_generation_packet(risk_brief(), trusted_source_refs=sources())
    draft = (
        "警告：この操作は権限を広げるため、誤操作時の影響範囲が大きくなります。対象外なら進めないでください。\n"
        "なぜ最初にテストするのか。失敗時の影響を小さくするためです。\n"
        "手順1 テスト環境で設定します。完了表示を確認してください。\n"
        "手順2 権限を確認します。エラーなら停止して戻ります。\n"
        "手順3 実行し、成功表示を確認します。"
    )
    result = audit_draft(draft, packet)
    assert "HIGH_RISK_WITHOUT_FRONT_STOP_GATE" not in codes(result)
    assert result["status"] in {"HUMAN_REVIEW_REQUIRED", "BLOCKED"}


def test_human_gate_requires_classification_of_strong_language_and_risk_evidence():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    checks = "\n".join(packet["human_gate"]["checks"])
    assert "outcome guarantee" in checks
    assert "secret literal" in checks
    assert "platform-evasion" in checks
    assert "verified evidence" in checks

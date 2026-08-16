import pytest

from x_article_engine import audit_draft, build_generation_packet
from x_article_engine.core import XArticleEngineError


def sources():
    return [
        {"id": "sales", "status": "VERIFIED", "kind": "PUBLIC_PAGE"},
        {"id": "timing", "status": "VERIFIED", "kind": "OFFICIAL"},
        {"id": "risk", "status": "VERIFIED", "kind": "OFFICIAL"},
        {"id": "counter", "status": "VERIFIED", "kind": "REPORT"},
        {"id": "result", "status": "VERIFIED", "kind": "LEDGER"},
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
        "evidence": [
            {
                "claim": "暫定ツール実装設計書は10,000円（税込）で、ツール制作そのものは含まない。",
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


def packet(data=None):
    return build_generation_packet(data or brief(), trusted_source_refs=sources())


def codes(result):
    return {item["code"] for item in result["findings"]}


def test_final_schema_and_publication_boundary():
    result = packet()
    assert result["schema_version"] == "0.9"
    assert result["meteor_status"] == "R11_SYNTHESIZED"
    assert result["publication_state"] == "BLOCKED_PENDING_HUMAN"
    assert result["publication_authority"] == "USER_ONLY"
    assert result["external_publication_performed"] is False


def test_current_requires_as_of():
    with pytest.raises(XArticleEngineError):
        packet(brief(freshness_mode="CURRENT"))


def test_current_requires_explicit_bound_timing_ref():
    data = current_brief()
    data.pop("freshness_evidence_refs")
    with pytest.raises(XArticleEngineError, match="freshness_evidence_refs"):
        packet(data)


def test_current_accepts_bound_timing_ref():
    result = packet(current_brief())
    assert result["freshness"]["evidence_refs"] == ["timing"]


def test_latest_wording_in_evergreen_is_reviewed():
    result = audit_draft("これは最新版の方法です。", packet())
    assert "FRESHNESS_CLAIM_WITHOUT_BOUND_EVIDENCE" in codes(result)


def test_negated_latest_is_not_currentness_claim():
    result = audit_draft("これは最新版ではありません。", packet())
    assert "FRESHNESS_CLAIM_WITHOUT_BOUND_EVIDENCE" not in codes(result)


def test_high_risk_requires_explicit_bound_risk_ref():
    data = high_risk_brief()
    data.pop("risk_evidence_refs")
    with pytest.raises(XArticleEngineError, match="risk_evidence_refs"):
        packet(data)


def test_permission_bypass_instruction_blocks():
    result = audit_draft("--dangerously-skip-permissions で起動してください。", packet())
    assert "UNSAFE_PERMISSION_OR_SECURITY_BYPASS" in codes(result)
    assert result["status"] == "BLOCKED"


def test_permission_bypass_prohibition_does_not_block():
    result = audit_draft("--dangerously-skip-permissions を使ってはいけません。", packet())
    assert "UNSAFE_PERMISSION_OR_SECURITY_BYPASS" not in codes(result)


def test_secret_to_model_instruction_blocks():
    result = audit_draft("APIキーをClaudeのプロンプトに貼り付けて送信してください。", packet())
    assert "SECRET_TRANSFER_TO_MODEL_RISK" in codes(result)
    assert result["status"] == "BLOCKED"


def test_secret_to_model_prohibition_does_not_block():
    result = audit_draft("APIキーをClaudeに送ってはいけません。", packet())
    assert "SECRET_TRANSFER_TO_MODEL_RISK" not in codes(result)


def test_settings_screen_secret_is_not_model_chat_transfer():
    result = audit_draft("Claudeの設定画面にAPIキーを入力してください。", packet())
    assert "SECRET_TRANSFER_TO_MODEL_RISK" not in codes(result)


def test_automation_without_human_checkpoint_reviews():
    result = audit_draft("ユーザーに質問せず、すべて自動で判断して進めてください。", packet())
    assert "AUTOMATION_WITHOUT_HUMAN_CHECKPOINT" in codes(result)


def test_hardcoded_reusable_secret_blocks():
    result = audit_draft("管理画面用APIキーは sk-line-harness-2026 をこのまま使って設定してください。", packet())
    assert "HARDCODED_SECRET_LITERAL_RISK" in codes(result)
    assert result["status"] == "BLOCKED"


def test_dummy_secret_example_does_not_block():
    result = audit_draft("例のダミーAPIキー sk-example-placeholder は実際には使わないでください。", packet())
    assert "HARDCODED_SECRET_LITERAL_RISK" not in codes(result)


def test_unbound_absolute_free_blocks():
    result = audit_draft("これは完全無料で使えます。", packet())
    assert "UNBOUND_ABSOLUTE_FREE_CLAIM" in codes(result)
    assert result["status"] == "BLOCKED"


def test_negated_absolute_free_does_not_block():
    result = audit_draft("すべてが完全無料ではありません。", packet())
    assert "UNBOUND_ABSOLUTE_FREE_CLAIM" not in codes(result)


def test_plain_guarantee_blocks():
    result = audit_draft("この方法なら完了できます。保証します。", packet())
    assert "UNBOUND_GUARANTEE_LANGUAGE" in codes(result)


def test_rejected_guarantee_example_does_not_block():
    result = audit_draft("『保証します』という表現は使いません。", packet())
    assert "UNBOUND_GUARANTEE_LANGUAGE" not in codes(result)


def test_safety_imperative_not_flattened_into_commercial_guarantee():
    result = audit_draft("APIキーは絶対に共有しないでください。権限は必ず確認してください。", packet())
    assert not any(
        item["code"] == "UNBOUND_STRONG_CLAIM" and item["detail"] in {"必ず", "絶対"}
        for item in result["findings"]
    )


def test_broad_absolute_prediction_reviews_not_blocks():
    result = audit_draft("初心者は必ず次の壁にぶつかります。", packet())
    assert "ABSOLUTE_GENERALIZATION_LANGUAGE" in codes(result)
    assert result["status"] == "HUMAN_REVIEW_REQUIRED"


def test_universal_capability_promise_reviews():
    result = audit_draft("初心者でもこの記事だけでできます。", packet())
    assert "UNIVERSAL_CAPABILITY_PROMISE" in codes(result)


def test_warning_fatigue_reviews():
    result = audit_draft("\n".join(["⚠️ 超重要な警告です。"] * 6), packet())
    assert "WARNING_FATIGUE_RISK" in codes(result)


def test_self_responsibility_without_mitigation_reviews():
    result = audit_draft("この操作は自己責任で行ってください。", packet())
    assert "SELF_RESPONSIBILITY_WITHOUT_MITIGATION" in codes(result)


def test_self_responsibility_with_local_mitigation_clears_specific_review():
    result = audit_draft(
        "自己責任という言葉だけで済ませません。まずテスト環境で確認し、異常があれば停止して戻してください。",
        packet(),
    )
    assert "SELF_RESPONSIBILITY_WITHOUT_MITIGATION" not in codes(result)


def test_high_risk_front_gate_rejects_no_risk_spoof():
    result = audit_draft(
        "リスクはありません。\n手順1 設定します。\n手順2 実行します。\n手順3 完了を確認します。",
        packet(high_risk_brief()),
    )
    assert "HIGH_RISK_WITHOUT_FRONT_STOP_GATE" in codes(result)
    assert result["status"] == "BLOCKED"


def test_high_risk_real_warning_passes_front_gate():
    result = audit_draft(
        "警告：この操作は権限を広げるため、誤操作時の影響範囲が大きくなります。対象外なら進めないでください。\n"
        "なぜ確認するか。失敗範囲を小さくするためです。\n"
        "手順1 設定します。完了を確認してください。\n"
        "手順2 実行します。エラーなら停止して戻ります。\n"
        "手順3 成功表示を確認します。",
        packet(high_risk_brief()),
    )
    assert "HIGH_RISK_WITHOUT_FRONT_STOP_GATE" not in codes(result)


def test_procedure_without_success_recovery_why_reviews():
    result = audit_draft(
        "手順1 開きます。\n手順2 入力します。\n手順3 実行します。",
        packet(brief(topic_mode="PROCEDURAL")),
    )
    assert {"PROCEDURE_WITHOUT_SUCCESS_SIGNAL", "PROCEDURE_WITHOUT_RECOVERY_PATH", "PROCEDURE_WITHOUT_WHY"}.issubset(codes(result))


def test_origin_only_does_not_manufacture_lived_pain():
    data = brief()
    data["primary_info"] = [
        {
            "claim": "これが私がこの仕事を始めたきっかけである。",
            "source_ref": "human_attestation:origin",
            "attested": True,
            "kind": "ORIGIN",
        }
    ]
    assert packet(data)["opening_mode"] == "RELATABLE"


def test_contrarian_requires_basis():
    with pytest.raises(XArticleEngineError, match="counterpoint_basis"):
        packet(brief(opening_mode="CONTRARIAN"))


def test_contrarian_accepts_human_opinion_basis():
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
    assert packet(data)["opening_mode"] == "CONTRARIAN"


def test_platform_evasion_operational_instruction_blocks():
    result = audit_draft("BAN回避のためにゼロ幅文字を挿入して配信します。", packet())
    assert "PLATFORM_EVASION_OPERATIONAL_INSTRUCTION" in codes(result)
    assert result["status"] == "BLOCKED"


def test_platform_evasion_rejection_is_review_only():
    result = audit_draft("BAN回避を目的にしたステルス配信という主張がありますが、この記事では推奨しません。", packet())
    assert "PLATFORM_EVASION_OPERATIONAL_INSTRUCTION" not in codes(result)
    assert "PLATFORM_EVASION_LANGUAGE" in codes(result)


def test_natural_fit_check_plus_follow_is_multi_cta():
    result = audit_draft("無料適合確認から始められます。役立ったらフォローしてください。", packet())
    assert "MULTIPLE_COMMERCIAL_ACTIONS_RISK" in codes(result)


def test_rejected_follow_does_not_count_as_cta():
    result = audit_draft("無料適合確認から始められます。フォローしてくださいとは言いません。", packet())
    assert "MULTIPLE_COMMERCIAL_ACTIONS_RISK" not in codes(result)


def test_10000_evidence_does_not_bind_zero_yen():
    result = audit_draft("利用料は0円です。", packet())
    assert any(item.get("code") == "UNBOUND_NUMERIC_CLAIM" and item.get("detail") == "0円" for item in result["findings"])


def test_exact_10000_price_remains_bound():
    result = audit_draft("暫定ツール実装設計書は10,000円（税込）です。", packet())
    assert not any(item.get("code") == "UNBOUND_NUMERIC_CLAIM" and item.get("detail") == "10,000円" for item in result["findings"])


def test_price_number_reused_as_sales_result_reviews():
    result = audit_draft("10,000円売れました。", packet())
    assert "NUMERIC_CONTEXT_REUSE_RISK" in codes(result)


def test_price_number_reused_as_savings_reviews():
    result = audit_draft("顧客が10,000円節約できました。", packet())
    assert "NUMERIC_CONTEXT_REUSE_RISK" in codes(result)


def test_bad_numeric_example_rejected_in_meta_is_not_asserted():
    result = audit_draft("『30分で終わります』と書くのはやめます。", packet())
    assert not any(item.get("code") == "UNBOUND_NUMERIC_CLAIM" and item.get("detail") == "30分" for item in result["findings"])


def test_bad_biography_example_rejected_in_meta_is_not_asserted():
    result = audit_draft("『私は数年前から業務自動化をしてきた』という経歴をAIに作らせてはいけません。", packet())
    assert "UNBOUND_IDENTITY_DETAIL" not in codes(result)


def test_human_gate_still_required_after_clean_heuristics():
    result = audit_draft("一工程だけを扱います。", packet())
    assert result["human_review_required"] is True
    assert result["publication_state"] == "BLOCKED_PENDING_HUMAN"

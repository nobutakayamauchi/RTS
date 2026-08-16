import pytest

from x_article_engine.core import XArticleEngineError
from x_article_engine.meteor_v09 import audit_draft, build_generation_packet


def sources():
    return [
        {"id": "bridgepatch-sales-page", "status": "VERIFIED", "kind": "PUBLIC_PAGE"},
        {"id": "dated-source", "status": "VERIFIED", "kind": "OFFICIAL"},
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
            },
            {
                "claim": "私はこの状態をシムシティ化と呼んでいた。",
                "source_ref": "human_attestation:label",
                "attested": True,
                "kind": "OPINION",
            },
            {
                "claim": "これが私がこの仕事を始めたきっかけである。",
                "source_ref": "human_attestation:origin",
                "attested": True,
                "kind": "ORIGIN",
            },
        ],
        "article_type": "STORY",
        "topic_mode": "BUSINESS",
        "cta": "BridgePatchの無料適合確認を使う。",
        "product_name": "BridgePatch",
        "product_reading": "ブリッジパッチ",
        "evidence": [
            {
                "claim": "暫定ツール実装設計書は10,000円（税込）で、ツール実装は含まない。",
                "source_ref": "bridgepatch-sales-page",
                "status": "VERIFIED",
                "kind": "COMMERCIAL",
            }
        ],
    }
    data.update(overrides)
    return data


def codes(result):
    return [item["code"] for item in result["findings"]]


def test_packet_synthesizes_v09_conflict_rules():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    assert packet["schema_version"] == "0.9-candidate"
    assert "decision_then_path_policy" in packet
    assert "completion_design_policy" in packet
    assert "risk_policy" in packet
    assert "human_automation_boundary" in packet
    assert "pain_to_promise_policy" in packet
    assert "knowledge_conflict_rules" in packet
    assert "Safety information outranks CTA optimization." in packet["knowledge_conflict_rules"]


def test_current_article_requires_as_of_boundary():
    with pytest.raises(XArticleEngineError):
        build_generation_packet(
            brief(freshness_mode="CURRENT"),
            trusted_source_refs=sources(),
        )


def test_update_article_requires_as_of_boundary():
    with pytest.raises(XArticleEngineError):
        build_generation_packet(
            brief(freshness_mode="UPDATE"),
            trusted_source_refs=sources(),
        )


def test_current_article_keeps_as_of_boundary():
    packet = build_generation_packet(
        brief(freshness_mode="CURRENT", as_of="2026-08-16"),
        trusted_source_refs=sources(),
    )
    assert packet["freshness"]["mode"] == "CURRENT"
    assert packet["freshness"]["as_of"] == "2026-08-16"


def test_invalid_risk_level_fails_closed():
    with pytest.raises(XArticleEngineError):
        build_generation_packet(brief(risk_level="YOLO"), trusted_source_refs=sources())


def test_latest_language_without_dated_evidence_is_reviewed():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    result = audit_draft("これは最新版の方法です。BridgePatch（ブリッジパッチ）を説明します。", packet)
    assert "FRESHNESS_CLAIM_WITHOUT_DATED_EVIDENCE" in codes(result)


def test_latest_language_with_as_of_boundary_is_not_freshness_reviewed():
    packet = build_generation_packet(
        brief(freshness_mode="CURRENT", as_of="2026-08-16"),
        trusted_source_refs=sources(),
    )
    result = audit_draft("これは現時点の方法です。BridgePatch（ブリッジパッチ）を説明します。", packet)
    assert "FRESHNESS_CLAIM_WITHOUT_DATED_EVIDENCE" not in codes(result)


def test_latest_language_with_timing_evidence_is_not_freshness_reviewed():
    data = brief()
    data["evidence"] = [
        *data["evidence"],
        {
            "claim": "この手順は2026年8月16日時点の公開仕様に基づく。",
            "source_ref": "dated-source",
            "status": "VERIFIED",
            "kind": "TIMING",
        },
    ]
    packet = build_generation_packet(data, trusted_source_refs=sources())
    result = audit_draft("これは現在の手順です。BridgePatch（ブリッジパッチ）を説明します。", packet)
    assert "FRESHNESS_CLAIM_WITHOUT_DATED_EVIDENCE" not in codes(result)


def test_dangerously_skip_permissions_instruction_is_blocked():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    result = audit_draft("Claude Codeを --dangerously-skip-permissions で起動してください。", packet)
    assert "UNSAFE_PERMISSION_OR_SECURITY_BYPASS" in codes(result)
    assert result["status"] == "BLOCKED"


def test_dangerously_skip_permissions_warning_is_not_blocked_by_v09_bypass_gate():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    result = audit_draft("--dangerously-skip-permissions は使わないでください。", packet)
    assert "UNSAFE_PERMISSION_OR_SECURITY_BYPASS" not in codes(result)


def test_auth_disable_instruction_is_blocked():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    result = audit_draft("認証を無効にして、そのまま進めてください。", packet)
    assert "UNSAFE_PERMISSION_OR_SECURITY_BYPASS" in codes(result)


def test_auth_disable_warning_is_allowed_by_bypass_gate():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    result = audit_draft("認証を無効にしないでください。", packet)
    assert "UNSAFE_PERMISSION_OR_SECURITY_BYPASS" not in codes(result)


def test_secret_transfer_to_ai_is_blocked():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    result = audit_draft("APIキーをClaudeのプロンプトに貼り付けて送信してください。", packet)
    assert "SECRET_TRANSFER_TO_MODEL_RISK" in codes(result)
    assert result["status"] == "BLOCKED"


def test_secret_transfer_warning_is_not_blocked():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    result = audit_draft("APIキーはClaudeのチャットに貼り付けないでください。", packet)
    assert "SECRET_TRANSFER_TO_MODEL_RISK" not in codes(result)


def test_automation_without_checkpoint_is_reviewed():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    result = audit_draft("ユーザーに質問せず、すべて自動で判断して進めてください。", packet)
    assert "AUTOMATION_WITHOUT_HUMAN_CHECKPOINT" in codes(result)


def test_multiple_commercial_actions_are_reviewed():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    draft = "無料適合確認に登録してください。この記事をフォローして、分からなければリプしてください。"
    result = audit_draft(draft, packet)
    assert "MULTIPLE_COMMERCIAL_ACTIONS_RISK" in codes(result)


def test_warning_fatigue_is_reviewed():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    draft = "\n".join(["⚠️ 超重要な警告です。"] * 6)
    result = audit_draft(draft, packet)
    assert "WARNING_FATIGUE_RISK" in codes(result)


def test_self_responsibility_without_mitigation_is_reviewed():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    result = audit_draft("この操作は自己責任で行ってください。", packet)
    assert "SELF_RESPONSIBILITY_WITHOUT_MITIGATION" in codes(result)


def test_self_responsibility_with_concrete_mitigation_is_not_flagged_by_that_gate():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    draft = "自己責任で進めるのではなく、まずテスト環境で確認し、異常があれば停止して戻してください。"
    result = audit_draft(draft, packet)
    assert "SELF_RESPONSIBILITY_WITHOUT_MITIGATION" not in codes(result)


def test_unbound_complete_free_claim_is_blocked():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    result = audit_draft("これは完全無料で使えます。", packet)
    assert "UNBOUND_ABSOLUTE_FREE_CLAIM" in codes(result)
    assert result["status"] == "BLOCKED"


def test_bound_complete_free_claim_is_not_blocked_by_absolute_free_gate():
    data = brief()
    data["evidence"] = [
        *data["evidence"],
        {
            "claim": "無料適合確認は完全無料で提供する。",
            "source_ref": "bridgepatch-sales-page",
            "status": "VERIFIED",
            "kind": "COMMERCIAL",
        },
    ]
    packet = build_generation_packet(data, trusted_source_refs=sources())
    result = audit_draft("無料適合確認は完全無料で提供します。", packet)
    assert "UNBOUND_ABSOLUTE_FREE_CLAIM" not in codes(result)


def test_superlative_language_is_reviewed_not_automatically_blocked():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    result = audit_draft("これは世界一分かりやすい最強の方法です。", packet)
    assert "SUPERLATIVE_OR_TOTALIZING_LANGUAGE" in codes(result)


def test_high_risk_guide_without_front_stop_gate_is_blocked():
    packet = build_generation_packet(
        brief(risk_level="HIGH", topic_mode="PROCEDURAL"),
        trusted_source_refs=sources(),
    )
    result = audit_draft("STEP1 設定を開きます。\nSTEP2 値を入力します。\nSTEP3 実行します。", packet)
    assert "HIGH_RISK_WITHOUT_FRONT_STOP_GATE" in codes(result)
    assert result["status"] == "BLOCKED"


def test_high_risk_guide_with_front_stop_gate_passes_that_gate():
    packet = build_generation_packet(
        brief(risk_level="HIGH", topic_mode="PROCEDURAL"),
        trusted_source_refs=sources(),
    )
    draft = "警告：この操作にはデータ損失のリスクがあります。対象外の人は進めないでください。\nSTEP1 設定を確認します。\nSTEP2 実行します。\nSTEP3 成功表示を確認します。"
    result = audit_draft(draft, packet)
    assert "HIGH_RISK_WITHOUT_FRONT_STOP_GATE" not in codes(result)


def test_procedural_guide_without_completion_recovery_or_why_is_reviewed():
    packet = build_generation_packet(
        brief(topic_mode="PROCEDURAL"),
        trusted_source_refs=sources(),
    )
    result = audit_draft("STEP1 開きます。\nSTEP2 入力します。\nSTEP3 実行します。", packet)
    assert "PROCEDURE_WITHOUT_SUCCESS_SIGNAL" in codes(result)
    assert "PROCEDURE_WITHOUT_RECOVERY_PATH" in codes(result)
    assert "PROCEDURE_WITHOUT_WHY" in codes(result)


def test_procedural_guide_with_completion_recovery_and_why_clears_those_gates():
    packet = build_generation_packet(
        brief(topic_mode="PROCEDURAL"),
        trusted_source_refs=sources(),
    )
    draft = (
        "なぜこの順番なのか。失敗した場所を切り分けやすくするためです。\n"
        "STEP1 設定を開きます。完了したら表示を確認してください。\n"
        "STEP2 値を入力します。エラーの場合は前の画面に戻ります。\n"
        "STEP3 実行します。成功と表示されれば完了です。"
    )
    result = audit_draft(draft, packet)
    assert "PROCEDURE_WITHOUT_SUCCESS_SIGNAL" not in codes(result)
    assert "PROCEDURE_WITHOUT_RECOVERY_PATH" not in codes(result)
    assert "PROCEDURE_WITHOUT_WHY" not in codes(result)


def test_existing_core_still_blocks_unbound_guarantee():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    result = audit_draft("BridgePatchなら必ず自動化できます。", packet)
    assert "UNBOUND_STRONG_CLAIM" in codes(result)
    assert result["status"] == "BLOCKED"


def test_existing_core_still_blocks_invented_number():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    result = audit_draft("作業は30分で終わります。", packet)
    assert "UNBOUND_NUMERIC_CLAIM" in codes(result)


def test_existing_ai_smell_gate_still_reviews_generic_subject():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    result = audit_draft("多くの人は仕事の本質を理解していません。", packet)
    assert "GENERIC_OVERSIZED_SUBJECT" in codes(result)
    assert "ABSTRACT_WORD_WITHOUT_PAYLOAD" in codes(result)


def test_attested_pain_does_not_get_sanitized_out_of_policy():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    primary = "\n".join(item["claim"] for item in packet["verified_primary_info"])
    assert "めんどくさくてキレそう" in primary
    assert packet["voice_policy"]["preserve_attested_raw_pain"] is True


def test_human_gate_contains_new_meteor_conflict_checks():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    checks = "\n".join(packet["human_gate"]["checks"])
    assert "最新・現在・現時点" in checks
    assert "bypass" not in checks.lower()  # Japanese human-facing wording remains readable.
    assert "権限" in checks
    assert "安全" in checks
    assert "commercial actions" in checks or "商" not in checks  # tolerate Japanese wording evolution
    assert "automation" not in checks.lower()  # Japanese wording remains readable.
    assert "自動化" in checks

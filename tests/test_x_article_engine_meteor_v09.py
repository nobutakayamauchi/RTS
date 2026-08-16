import pytest

from x_article_engine.core import XArticleEngineError
from x_article_engine.meteor_v09_final import audit_draft, build_generation_packet


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


def current_brief(**overrides):
    data = brief(freshness_mode="CURRENT", as_of="2026-08-16")
    data["evidence"] = [
        *data["evidence"],
        {
            "claim": "この手順は2026年8月16日時点の公開仕様に基づく。",
            "source_ref": "dated-source",
            "status": "VERIFIED",
            "kind": "TIMING",
        },
    ]
    data.update(overrides)
    return data


def codes(result):
    return [item["code"] for item in result["findings"]]


def test_packet_synthesizes_v09_meteor_conflict_rules():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    assert packet["schema_version"] == "0.9-meteor"
    assert "decision_then_path_policy" in packet
    assert "completion_design_policy" in packet
    assert "risk_policy" in packet
    assert "human_automation_boundary" in packet
    assert "pain_to_promise_policy" in packet
    assert "knowledge_conflict_rules" in packet
    assert "Safety information outranks CTA optimization." in packet["knowledge_conflict_rules"]
    assert "as_of is only a scope label" in packet["freshness"]["evidence_rule"]


def test_current_article_requires_as_of_boundary():
    with pytest.raises(XArticleEngineError):
        build_generation_packet(brief(freshness_mode="CURRENT"), trusted_source_refs=sources())


def test_update_article_requires_as_of_boundary():
    with pytest.raises(XArticleEngineError):
        build_generation_packet(brief(freshness_mode="UPDATE"), trusted_source_refs=sources())


def test_as_of_alone_does_not_create_current_truth():
    with pytest.raises(XArticleEngineError):
        build_generation_packet(
            brief(freshness_mode="CURRENT", as_of="2026-08-16"),
            trusted_source_refs=sources(),
        )


def test_current_article_requires_and_keeps_verified_dated_evidence():
    packet = build_generation_packet(current_brief(), trusted_source_refs=sources())
    assert packet["freshness"]["mode"] == "CURRENT"
    assert packet["freshness"]["as_of"] == "2026-08-16"


def test_invalid_risk_level_fails_closed():
    with pytest.raises(XArticleEngineError):
        build_generation_packet(brief(risk_level="YOLO"), trusted_source_refs=sources())


def test_latest_language_without_dated_evidence_is_reviewed_in_evergreen_mode():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    result = audit_draft("これは最新版の方法です。BridgePatch（ブリッジパッチ）を説明します。", packet)
    assert "FRESHNESS_CLAIM_WITHOUT_DATED_EVIDENCE" in codes(result)


def test_latest_language_with_verified_timing_evidence_clears_freshness_review():
    packet = build_generation_packet(current_brief(), trusted_source_refs=sources())
    result = audit_draft("これは現時点の方法です。BridgePatch（ブリッジパッチ）を説明します。", packet)
    assert "FRESHNESS_CLAIM_WITHOUT_DATED_EVIDENCE" not in codes(result)


def test_dangerously_skip_permissions_instruction_is_blocked():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    result = audit_draft("Claude Codeを --dangerously-skip-permissions で起動してください。", packet)
    assert "UNSAFE_PERMISSION_OR_SECURITY_BYPASS" in codes(result)
    assert result["status"] == "BLOCKED"


def test_dangerous_command_inside_prohibition_is_not_blocked():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    result = audit_draft("--dangerously-skip-permissions は使わないでください。", packet)
    assert "UNSAFE_PERMISSION_OR_SECURITY_BYPASS" not in codes(result)


def test_auth_disable_instruction_is_blocked():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    result = audit_draft("認証を無効にして、そのまま進めてください。", packet)
    assert "UNSAFE_PERMISSION_OR_SECURITY_BYPASS" in codes(result)


def test_auth_none_description_is_not_mistaken_for_instruction():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    result = audit_draft("認証なしでは使えません。認証は有効のままにしてください。", packet)
    assert "UNSAFE_PERMISSION_OR_SECURITY_BYPASS" not in codes(result)


def test_auth_disable_warning_is_not_blocked():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    result = audit_draft("認証を無効にしないでください。", packet)
    assert "UNSAFE_PERMISSION_OR_SECURITY_BYPASS" not in codes(result)


def test_secret_transfer_to_model_prompt_is_blocked():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    result = audit_draft("APIキーをClaudeのプロンプトに貼り付けて送信してください。", packet)
    assert "SECRET_TRANSFER_TO_MODEL_RISK" in codes(result)
    assert result["status"] == "BLOCKED"


def test_secret_transfer_prohibition_is_not_blocked():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    result = audit_draft("APIキーはClaudeのチャットに貼り付けないでください。", packet)
    assert "SECRET_TRANSFER_TO_MODEL_RISK" not in codes(result)


def test_secret_entered_into_named_settings_screen_is_not_automatically_called_model_transfer():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    result = audit_draft("Claudeの設定画面にAPIキーを入力してください。", packet)
    assert "SECRET_TRANSFER_TO_MODEL_RISK" not in codes(result)


def test_automation_without_checkpoint_is_reviewed():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    result = audit_draft("ユーザーに質問せず、すべて自動で判断して進めてください。", packet)
    assert "AUTOMATION_WITHOUT_HUMAN_CHECKPOINT" in codes(result)


def test_two_competing_reader_actions_are_enough_for_cta_review():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    draft = "BridgePatchの無料適合確認を使ってください。この記事が役立ったらフォローしてください。"
    result = audit_draft(draft, packet)
    assert "MULTIPLE_COMMERCIAL_ACTIONS_RISK" in codes(result)


def test_narrative_mentions_of_registration_and_followers_are_not_ctas():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    draft = "登録前の教育と、フォロワー数の変化は別の指標として見ます。"
    result = audit_draft(draft, packet)
    assert "MULTIPLE_COMMERCIAL_ACTIONS_RISK" not in codes(result)


def test_warning_fatigue_is_reviewed():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    draft = "\n".join(["⚠️ 超重要な警告です。"] * 6)
    result = audit_draft(draft, packet)
    assert "WARNING_FATIGUE_RISK" in codes(result)


def test_self_responsibility_without_local_mitigation_is_reviewed():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    result = audit_draft("この操作は自己責任で行ってください。", packet)
    assert "SELF_RESPONSIBILITY_WITHOUT_MITIGATION" in codes(result)


def test_self_responsibility_with_local_mitigation_is_not_flagged():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    draft = "自己責任という言葉だけで済ませません。まずテスト環境で確認し、異常があれば停止して戻してください。"
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


def test_plain_guarantee_language_is_blocked_even_without_100_percent_wording():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    result = audit_draft("この手順なら完了できます。保証します。", packet)
    assert "UNBOUND_GUARANTEE_LANGUAGE" in codes(result)
    assert result["status"] == "BLOCKED"


def test_absolute_safety_language_is_reviewed():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    result = audit_draft("この方法は安全です。初心者でも安心です。", packet)
    assert "ABSOLUTE_SAFETY_LANGUAGE" in codes(result)


def test_outcome_promise_language_is_reviewed():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    result = audit_draft("この記事の通りにすれば売れます。", packet)
    assert "OUTCOME_PROMISE_LANGUAGE" in codes(result)


def test_superlative_language_is_reviewed_not_automatically_blocked():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    result = audit_draft("これは世界一分かりやすい最強の方法です。", packet)
    assert "SUPERLATIVE_OR_TOTALIZING_LANGUAGE" in codes(result)


def test_high_risk_guide_without_front_stop_gate_is_blocked():
    packet = build_generation_packet(
        brief(risk_level="HIGH", topic_mode="PROCEDURAL"),
        trusted_source_refs=sources(),
    )
    result = audit_draft("手順1 設定を開きます。\n手順2 値を入力します。\n手順3 実行します。", packet)
    assert "HIGH_RISK_WITHOUT_FRONT_STOP_GATE" in codes(result)
    assert result["status"] == "BLOCKED"


def test_high_risk_guide_with_front_stop_gate_passes_that_gate():
    packet = build_generation_packet(
        brief(risk_level="HIGH", topic_mode="PROCEDURAL"),
        trusted_source_refs=sources(),
    )
    draft = "警告：この操作にはデータ損失のリスクがあります。対象外の人は進めないでください。\n手順1 設定を確認します。\n手順2 実行します。\n手順3 成功表示を確認します。"
    result = audit_draft(draft, packet)
    assert "HIGH_RISK_WITHOUT_FRONT_STOP_GATE" not in codes(result)


def test_japanese_procedural_guide_without_completion_recovery_or_why_is_reviewed():
    packet = build_generation_packet(brief(topic_mode="PROCEDURAL"), trusted_source_refs=sources())
    result = audit_draft("手順1 開きます。\n手順2 入力します。\n手順3 実行します。", packet)
    assert "PROCEDURE_WITHOUT_SUCCESS_SIGNAL" in codes(result)
    assert "PROCEDURE_WITHOUT_RECOVERY_PATH" in codes(result)
    assert "PROCEDURE_WITHOUT_WHY" in codes(result)


def test_procedural_guide_with_completion_recovery_and_why_clears_those_gates():
    packet = build_generation_packet(brief(topic_mode="PROCEDURAL"), trusted_source_refs=sources())
    draft = (
        "なぜこの順番なのか。失敗した場所を切り分けやすくするためです。\n"
        "手順1 設定を開きます。完了したら表示を確認してください。\n"
        "手順2 値を入力します。エラーの場合は前の画面に戻ります。\n"
        "手順3 実行します。成功と表示されれば完了です。"
    )
    result = audit_draft(draft, packet)
    assert "PROCEDURE_WITHOUT_SUCCESS_SIGNAL" not in codes(result)
    assert "PROCEDURE_WITHOUT_RECOVERY_PATH" not in codes(result)
    assert "PROCEDURE_WITHOUT_WHY" not in codes(result)


def test_existing_core_still_blocks_unbound_outcome_absolute():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    result = audit_draft("BridgePatchなら必ず自動化できます。", packet)
    assert "UNBOUND_STRONG_CLAIM" in codes(result)
    assert result["status"] == "BLOCKED"


def test_safety_imperatives_with_must_and_never_are_not_misclassified_as_commercial_guarantees():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    draft = "APIキーは絶対に共有しないでください。権限は必ず確認してください。"
    result = audit_draft(draft, packet)
    assert not any(
        item["code"] == "UNBOUND_STRONG_CLAIM" and item["detail"] in {"必ず", "絶対"}
        for item in result["findings"]
    )


def test_existing_core_still_blocks_invented_number():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    result = audit_draft("作業は30分で終わります。", packet)
    assert "UNBOUND_NUMERIC_CLAIM" in codes(result)


def test_existing_ai_smell_gate_still_reviews_generic_subject_and_empty_abstraction():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    result = audit_draft("多くの人は仕事の本質を理解していません。", packet)
    assert "GENERIC_OVERSIZED_SUBJECT" in codes(result)
    assert "ABSTRACT_WORD_WITHOUT_PAYLOAD" in codes(result)


def test_attested_pain_is_preserved_in_packet():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    primary = "\n".join(item["claim"] for item in packet["verified_primary_info"])
    assert "めんどくさくてキレそう" in primary
    assert packet["voice_policy"]["preserve_attested_raw_pain"] is True


def test_reference_specific_three_examples_rule_is_not_made_mandatory():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    rendered = repr(packet)
    assert "always use exactly three examples" not in rendered.lower()
    assert "具体例は必ず3つ" not in rendered


def test_human_gate_contains_freshness_security_safety_cta_and_human_boundary_checks():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    checks = "\n".join(packet["human_gate"]["checks"])
    assert "最新・現在・現時点" in checks
    assert "権限" in checks
    assert "安全" in checks
    assert "commercial actions" in checks
    assert "自動化" in checks
    assert "as_of" in checks


def test_bridgepatch_safe_story_does_not_trigger_security_specific_blocks():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    draft = (
        "あー、めんどくさくてキレそう。\n"
        "修正して確認する。直したら別の場所をもう一度確認する。まさに無限修正だった。\n"
        "そこで全部を自動化するのではなく、一工程だけ切ることにした。\n"
        "間違えたときは人間に戻せるようにする。\n"
        "その考えを仕事に使える形にしたのがBridgePatch（ブリッジパッチ）です。"
    )
    result = audit_draft(draft, packet)
    security_codes = {
        "UNSAFE_PERMISSION_OR_SECURITY_BYPASS",
        "SECRET_TRANSFER_TO_MODEL_RISK",
        "HIGH_RISK_WITHOUT_FRONT_STOP_GATE",
        "UNBOUND_GUARANTEE_LANGUAGE",
    }
    assert not security_codes.intersection(codes(result))

import pytest

from x_article_engine.meteor_v09_r7 import audit_draft, build_generation_packet


def sources():
    return [
        {"id": "sales", "status": "VERIFIED", "kind": "PUBLIC_PAGE"},
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


def high_risk_brief():
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
    return data


def codes(result):
    return {item["code"] for item in result["findings"]}


def test_r7_schema_and_polarity_policy_present():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    assert packet["schema_version"] == "0.9-meteor-r7"
    assert "polarity_policy" in packet


def test_secret_transfer_do_not_instruction_is_not_blocked_as_transfer():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    result = audit_draft(
        "BridgePatch（ブリッジパッチ）の記事です。APIキーをClaudeに送ってはいけません。",
        packet,
    )
    assert "SECRET_TRANSFER_TO_MODEL_RISK" not in codes(result)


def test_secret_transfer_positive_instruction_still_blocks():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    result = audit_draft(
        "BridgePatch（ブリッジパッチ）の記事です。APIキーをClaudeに送ってください。",
        packet,
    )
    assert "SECRET_TRANSFER_TO_MODEL_RISK" in codes(result)
    assert result["status"] == "BLOCKED"


def test_dangerous_command_inside_do_not_use_form_is_not_blocked():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    result = audit_draft(
        "BridgePatch（ブリッジパッチ）の記事です。--dangerously-skip-permissions を使ってはいけません。",
        packet,
    )
    assert "UNSAFE_PERMISSION_OR_SECURITY_BYPASS" not in codes(result)


def test_high_risk_front_cannot_be_spoofed_by_no_risk_sentence():
    packet = build_generation_packet(high_risk_brief(), trusted_source_refs=sources())
    draft = (
        "リスクはありません。BridgePatch（ブリッジパッチ）の手順です。\n"
        "手順1 設定します。\n手順2 実行します。\n手順3 完了を確認します。"
    )
    result = audit_draft(draft, packet)
    assert "HIGH_RISK_WITHOUT_FRONT_STOP_GATE" in codes(result)
    assert result["status"] == "BLOCKED"


def test_high_risk_front_cannot_be_spoofed_by_do_not_stop_sentence():
    packet = build_generation_packet(high_risk_brief(), trusted_source_refs=sources())
    draft = (
        "停止しないでください。BridgePatch（ブリッジパッチ）の手順です。\n"
        "手順1 設定します。\n手順2 実行します。\n手順3 完了を確認します。"
    )
    result = audit_draft(draft, packet)
    assert "HIGH_RISK_WITHOUT_FRONT_STOP_GATE" in codes(result)


def test_real_high_risk_warning_satisfies_front_gate():
    packet = build_generation_packet(high_risk_brief(), trusted_source_refs=sources())
    draft = (
        "警告：この操作は権限を広げるため、誤操作時の影響範囲が大きくなります。対象外なら進めないでください。\n"
        "BridgePatch（ブリッジパッチ）の手順です。なぜ最初に確認するか。失敗範囲を小さくするためです。\n"
        "手順1 設定します。完了を確認してください。\n"
        "手順2 実行します。エラーなら停止して戻ります。\n"
        "手順3 成功表示を確認します。"
    )
    result = audit_draft(draft, packet)
    assert "HIGH_RISK_WITHOUT_FRONT_STOP_GATE" not in codes(result)


def test_two_rejected_actions_are_not_counted_as_multiple_ctas():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    draft = (
        "BridgePatch（ブリッジパッチ）の記事です。"
        "登録してくださいとは言いません。フォローしてくださいとも言いません。"
    )
    result = audit_draft(draft, packet)
    assert "MULTIPLE_COMMERCIAL_ACTIONS_RISK" not in codes(result)


def test_one_real_cta_plus_one_rejected_action_is_not_multi_cta():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    draft = (
        "BridgePatch（ブリッジパッチ）の無料適合確認を使ってください。"
        "フォローしてくださいとは言いません。"
    )
    result = audit_draft(draft, packet)
    assert "MULTIPLE_COMMERCIAL_ACTIONS_RISK" not in codes(result)


def test_two_real_ctas_still_review():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    draft = (
        "BridgePatch（ブリッジパッチ）の無料適合確認を使ってください。"
        "記事が役立ったらフォローしてください。"
    )
    result = audit_draft(draft, packet)
    assert "MULTIPLE_COMMERCIAL_ACTIONS_RISK" in codes(result)


def test_human_gate_includes_polarity_check():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    checks = "\n".join(packet["human_gate"]["checks"])
    assert "実行を勧めているのか" in checks
    assert "禁止・否定" in checks

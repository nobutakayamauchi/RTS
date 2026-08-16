from x_article_engine.meteor_v09_r5 import audit_draft, build_generation_packet


def sources():
    return [{"id": "sales", "status": "VERIFIED", "kind": "PUBLIC_PAGE"}]


def brief():
    return {
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
                "claim": "暫定ツール実装設計書は10,000円（税込）で、ツール実装は含まない。",
                "source_ref": "sales",
                "status": "VERIFIED",
                "kind": "COMMERCIAL",
            }
        ],
    }


def codes(result):
    return [item["code"] for item in result["findings"]]


def test_r5_schema_and_false_positive_policies_present():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    assert packet["schema_version"] == "0.9-meteor-r5"
    assert "generic_abstract_collision_rule" in packet["anti_ai_smell_policy"]
    assert "evasion_negation_rule" in packet["security_content_policy"]


def test_generic_human_word_does_not_hide_empty_abstract_noun():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    result = audit_draft("多くの人は仕事の本質を理解していません。", packet)
    assert "GENERIC_OVERSIZED_SUBJECT" in codes(result)
    assert "ABSTRACT_WORD_WITHOUT_PAYLOAD" in codes(result)


def test_polite_evasion_rejection_is_review_not_operational_block():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    result = audit_draft(
        "BAN回避を目的にしたステルス配信という主張がありますが、この記事では推奨しません。",
        packet,
    )
    assert "PLATFORM_EVASION_OPERATIONAL_INSTRUCTION" not in codes(result)
    assert "PLATFORM_EVASION_LANGUAGE" in codes(result)


def test_polite_evasion_non_teaching_statement_is_review_not_operational_block():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    result = audit_draft(
        "ゼロ幅文字を使う回避策はここでは教えません。規約に沿う方法だけ扱います。",
        packet,
    )
    assert "PLATFORM_EVASION_OPERATIONAL_INSTRUCTION" not in codes(result)
    assert "PLATFORM_EVASION_LANGUAGE" in codes(result)


def test_true_operational_evasion_still_blocks():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    result = audit_draft("BAN回避のためにゼロ幅文字を挿入して配信します。", packet)
    assert "PLATFORM_EVASION_OPERATIONAL_INSTRUCTION" in codes(result)
    assert result["status"] == "BLOCKED"


def test_japanese_human_gate_explicitly_mentions_permission_safety_automation():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    checks = "\n".join(packet["human_gate"]["checks"])
    assert "権限" in checks
    assert "安全" in checks
    assert "自動化" in checks

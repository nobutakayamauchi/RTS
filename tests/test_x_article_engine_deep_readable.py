from x_article_engine.deep_readable import build_generation_packet


def sources():
    return [
        {"id": "bridgepatch-sales-page", "status": "VERIFIED", "kind": "PUBLIC_PAGE"}
    ]


def brief():
    return {
        "offer": "BridgePatch。まず無料で適合確認し、必要なら一工程の設計と実装へ進む。",
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


def test_packet_uses_deep_readable_layer():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    assert packet["schema_version"] == "0.5"
    assert packet["opening_mode"] == "LIVED_PAIN"
    assert packet["terminology_policy"]["explain_on_first_use"] is True
    assert packet["product_naming_policy"]["first_mention_format"] == "BridgePatch（ブリッジパッチ）"
    assert "entry_rule" in packet["comprehension_doctrine"]
    assert "transition_rule" in packet["claim_layer_policy"]
    assert "promise_payoff_rule" in packet["reader_progression_policy"]
    assert "anti_metric_trap" in packet["commercial_article_policy"]


def test_reference_article_platform_claims_are_not_imported_as_truth():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    rendered = repr(packet["reference_learning_boundary"])
    # Writing lessons are imported; specific platform claims are explicitly not.
    assert "platform algorithm weights" in rendered
    assert "ranking constants" in rendered
    assert "time windows" in rendered
    assert "20.0" not in rendered
    assert "48時間" not in rendered
    assert "PageRank" not in rendered
    assert "Agatha" not in rendered


def test_commercial_priority_puts_reader_and_offer_before_distribution():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    priorities = packet["commercial_article_policy"]["priority_order"]
    assert priorities == [
        "WHO_TO_REACH",
        "WHAT_TO_HELP_THEM_UNDERSTAND",
        "WHAT_STATE_TO_LEAVE_THEM_IN",
        "HOW_TO_MAXIMIZE_DISTRIBUTION",
    ]


def test_human_gate_checks_fact_interpretation_boundary_and_payoff():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    checks = "\n".join(packet["human_gate"]["checks"])
    assert "source-backed fact" in checks
    assert "forward promise" in checks
    assert "first-time reader" in checks

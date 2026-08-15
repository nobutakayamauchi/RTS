from x_article_engine import build_generation_packet


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


def test_packet_uses_v08_depth_market_layer():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    assert packet["schema_version"] == "0.8"
    assert "beginner_layer" in packet["audience_depth_policy"]
    assert "intermediate_layer" in packet["audience_depth_policy"]
    assert "advanced_layer" in packet["audience_depth_policy"]
    assert "primary_source_preference" in packet["source_depth_policy"]
    assert "commercial_cta_rule" in packet["desire_timing_policy"]
    assert "candidate_patterns" in packet["market_gap_policy"]
    assert "speed_rule" in packet["speed_quality_policy"]
    assert packet["reach_conversion_policy"]["axes"] == [
        "READ_OR_REACH",
        "QUALIFIED_COMMERCIAL_PROGRESS",
    ]


def test_reference_metrics_and_speed_story_are_not_imported_as_truth():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    boundary = "\n".join(packet["reference_learning_boundary"]["not_imported_as_truth"])
    assert "impression" in boundary
    assert "follower" in boundary
    assert "creation time" in boundary
    assert "being first" in boundary
    assert "260万" not in boundary
    assert "700" not in boundary
    assert "154" not in boundary
    assert "5時間" not in boundary


def test_counterpoint_policy_rejects_manufactured_conflict_as_doctrine():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    policy = packet["market_gap_policy"]
    assert "evidence or a genuine human-attested belief" in policy["counterpoint_rule"]
    assert "Do not manufacture faction conflict" in policy["conflict_rule"]


def test_asset_timing_does_not_expand_commercial_cta_count():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    timing = packet["desire_timing_policy"]
    assert "utility asset" in timing["utility_asset_rule"].lower()
    assert "multiple competing commercial CTAs" in timing["utility_asset_rule"]
    assert "singular" in timing["commercial_cta_rule"]


def test_human_gate_checks_depth_source_market_and_reach_conversion():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    checks = "\n".join(packet["human_gate"]["checks"])
    assert "first-time reader" in checks
    assert "comparison numbers" in checks
    assert "strongest available source" in checks
    assert "controversy" in checks
    assert "reach/read metrics" in checks

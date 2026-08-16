from x_article_engine import audit_draft, build_generation_packet


def sources():
    return [
        {"id": "sales", "status": "VERIFIED", "kind": "PUBLIC_PAGE"},
    ]


def brief():
    return {
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


def test_root_points_to_consolidated_v09():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    assert packet["schema_version"] == "0.9"
    assert "strong_language_policy" in packet
    assert "security_content_policy" in packet
    assert "opening_integrity_policy" in packet
    assert "generic_abstract_collision_rule" in packet["anti_ai_smell_policy"]
    assert packet["publication_state"] == "BLOCKED_PENDING_HUMAN"
    assert packet["publication_authority"] == "USER_ONLY"
    assert packet["external_publication_performed"] is False


def test_root_keeps_human_gate_mandatory():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    result = audit_draft(
        "あー、めんどくさくてキレそう。BridgePatch（ブリッジパッチ）は一工程だけを扱います。",
        packet,
    )
    assert result["human_review_required"] is True
    assert result["publication_state"] == "BLOCKED_PENDING_HUMAN"
    assert result["publication_authority"] == "USER_ONLY"

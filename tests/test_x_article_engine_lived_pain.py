import pytest

from x_article_engine.core import XArticleEngineError, build_generation_packet


def sources():
    return [
        {"id": "bridgepatch-sales-page", "status": "VERIFIED", "kind": "PUBLIC_PAGE"}
    ]


def brief():
    return {
        "offer": "BridgePatch。まず無料で適合確認し、必要なら一工程の設計と実装へ進む。",
        "target": "毎週、転記・集計・確認・下書きを手作業している小規模事業者。",
        "pain": "小さいが放置できない手作業が残り続ける。",
        "primary_info": [
            {
                "claim": "あーめんどくさくてキレそう、と自前のプログラムを前に頭を抱えた。",
                "source_ref": "human_attestation:bridgepatch-pain",
                "attested": True,
                "kind": "PAIN",
            },
            {
                "claim": "CapCutで動画編集に挑戦して挫折し、自分が迷わないよう機能を削ったツールを作った。",
                "source_ref": "human_attestation:bridgepatch-failure",
                "attested": True,
                "kind": "FAILURE",
            },
            {
                "claim": "人にも使ってもらおうとすると予期しない操作や動作不良のチェックが増え、直す、チェックする、また直すという無限修正の感覚になった。",
                "source_ref": "human_attestation:bridgepatch-friction",
                "attested": True,
                "kind": "EXPERIENCE",
            },
            {
                "claim": "直接1円にもならないが、放置するとクレームの元になり得るので手を抜けない仕事だと感じた。",
                "source_ref": "human_attestation:bridgepatch-stakes",
                "attested": True,
                "kind": "OPINION",
            },
            {
                "claim": "これが私がこの仕事を始めたきっかけである。",
                "source_ref": "human_attestation:bridgepatch-origin",
                "attested": True,
                "kind": "ORIGIN",
            },
        ],
        "article_type": "HOW_TO",
        "topic_mode": "BUSINESS",
        "cta": "BridgePatchの無料適合確認を使う。",
        "evidence": [
            {
                "claim": "暫定ツール実装設計書は10,000円（税込）で、ツール実装は含まない。",
                "source_ref": "bridgepatch-sales-page",
                "status": "VERIFIED",
                "kind": "COMMERCIAL",
            }
        ],
    }


def build(source=None):
    return build_generation_packet(source or brief(), trusted_source_refs=sources())


def test_lived_pain_is_selected_when_attested_pain_exists():
    packet = build()
    assert packet["schema_version"] == "0.3"
    assert packet["opening_mode"] == "LIVED_PAIN"
    assert packet["article_type"] == "HOW_TO"
    assert len(packet["lived_pain_anchors"]) == 3


def test_lived_pain_sequence_shows_pain_before_explanation():
    packet = build()
    sequence = packet["narrative"]["sequence"]
    assert sequence[:6] == [
        "raw_pain_line",
        "concrete_scene",
        "failed_attempt_or_trigger",
        "friction_loop",
        "cost_or_stakes",
        "origin_statement_if_attested",
    ]
    assert sequence.index("mechanism") < sequence.index("solution")
    assert sequence.index("solution") < sequence.index("reader_bridge")


def test_lived_pain_preserves_raw_voice_in_policy():
    packet = build()
    assert packet["voice_policy"]["preserve_attested_raw_pain"] is True
    assert packet["voice_policy"]["preserve_colloquial_force"] is True
    assert "sanitize" in packet["voice_policy"]["lived_pain_rule"]


def test_explicit_lived_pain_requires_attested_anchor():
    source = brief()
    source["primary_info"] = [
        {
            "claim": "一工程だけ切る方がいいと考えている。",
            "source_ref": "human_attestation:belief",
            "attested": True,
            "kind": "BELIEF",
        }
    ]
    source["opening_mode"] = "LIVED_PAIN"

    with pytest.raises(XArticleEngineError, match="LIVED_PAIN requires"):
        build(source)


def test_relational_mode_remains_available_without_lived_pain_anchor():
    source = brief()
    source["primary_info"] = [
        {
            "claim": "一工程だけ切る方がいいと考えている。",
            "source_ref": "human_attestation:belief",
            "attested": True,
            "kind": "BELIEF",
        }
    ]
    packet = build(source)
    assert packet["opening_mode"] == "RELATABLE"


def test_human_gate_checks_felt_pain_and_scene_truth():
    packet = build()
    checks = packet["human_gate"]["checks"]
    assert any("make the pain felt" in item for item in checks)
    assert any("scene detail" in item for item in checks)

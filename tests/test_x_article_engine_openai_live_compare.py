import json

import pytest

from x_article_engine.core import XArticleEngineError
from x_article_engine.openai_live_compare import (
    TUNED_SYSTEM_INSTRUCTIONS,
    build_tuned_openai_request,
    extract_response_text,
    run_openai_live_comparison,
    unexpected_author_markers,
)
from x_article_engine import v09_final


def sources():
    return [
        {"id": "official-service-page", "status": "VERIFIED", "kind": "PUBLIC_PAGE"}
    ]


def brief():
    return {
        "offer": "小規模事業者向けの週次レポート整理サービス。",
        "target": "毎週レポートを手作業でまとめている小規模事業者。",
        "pain": "転記と確認に手間がかかる。",
        "primary_info": [
            {
                "claim": "私は一工程ずつ確認する方が安全だと考えている。",
                "source_ref": "human_attestation:opinion",
                "attested": True,
                "kind": "OPINION",
            }
        ],
        "article_type": "HOW_TO",
        "topic_mode": "BUSINESS",
        "cta": "サービスの説明ページを見る。",
        "evidence": [
            {
                "claim": "公式ページでは導入前に対象範囲を確認すると説明している。",
                "source_ref": "official-service-page",
                "status": "VERIFIED",
                "kind": "POLICY",
            }
        ],
    }


def test_live_01_tuned_request_uses_same_security_shape_without_plain_rewrite():
    packet = v09_final.build_generation_packet(brief(), trusted_source_refs=sources())
    request = build_tuned_openai_request(packet, model="gpt-example")
    payload = json.loads(request["input"][0]["content"][0]["text"])

    assert request["instructions"] == TUNED_SYSTEM_INSTRUCTIONS
    assert request["store"] is False
    assert payload["profile"]["profile_id"] == "X_ARTICLE_TUNED_V09"
    assert "BridgePatch" in json.dumps(payload["rules"], ensure_ascii=False)
    assert payload["publication_boundary"]["publication_state"] == "BLOCKED_PENDING_HUMAN"


def test_live_02_tuned_request_blocks_secret_literal_before_transport():
    source = brief()
    source["pain"] = "誤って sk-abcdefghijklmnopqrstuvwxyz1234567890 をメモに残した。"
    packet = v09_final.build_generation_packet(source, trusted_source_refs=sources())
    with pytest.raises(XArticleEngineError, match="credential-like literal"):
        build_tuned_openai_request(packet, model="gpt-example")


def test_live_03_extract_response_text_supports_current_responses_shape():
    response = {
        "id": "resp_test",
        "status": "completed",
        "output": [
            {
                "type": "message",
                "content": [
                    {"type": "output_text", "text": "本文です。", "annotations": []}
                ],
            }
        ],
    }
    assert extract_response_text(response) == "本文です。"


def test_live_04_extract_response_text_rejects_empty_response():
    with pytest.raises(XArticleEngineError, match="output_text"):
        extract_response_text({"output": []})


def test_live_05_marker_check_only_flags_unbound_engine_author_terms():
    packet = v09_final.build_generation_packet(brief(), trusted_source_refs=sources())
    assert unexpected_author_markers("BridgePatchを使います。", packet) == ["BridgePatch"]

    source = brief()
    source["offer"] = "BridgePatchを使った支援。"
    bound_packet = v09_final.build_generation_packet(source, trusted_source_refs=sources())
    assert unexpected_author_markers("BridgePatchを使います。", bound_packet) == []


def test_live_06_comparison_calls_same_model_twice_and_never_returns_api_key():
    calls = []

    def fake_transport(request, api_key, endpoint, timeout):
        calls.append(
            {
                "request": request,
                "api_key": api_key,
                "endpoint": endpoint,
                "timeout": timeout,
            }
        )
        if len(calls) == 1:
            text = "毎週の転記を一工程ずつ整理します。サービスの説明ページを見る。"
            response_id = "resp_tuned"
        else:
            text = "毎週の転記と確認を、一つの工程から整理します。サービスの説明ページを見る。"
            response_id = "resp_plain"
        return {
            "id": response_id,
            "model": "gpt-same",
            "status": "completed",
            "output": [
                {
                    "type": "message",
                    "content": [{"type": "output_text", "text": text}],
                }
            ],
            "usage": {"input_tokens": 10, "output_tokens": 10, "total_tokens": 20},
        }

    result = run_openai_live_comparison(
        brief(),
        trusted_source_refs=sources(),
        api_key="secret-key-used-only-by-transport",
        model="gpt-same",
        transport=fake_transport,
    )

    assert len(calls) == 2
    assert calls[0]["request"]["model"] == calls[1]["request"]["model"] == "gpt-same"
    assert calls[0]["request"]["instructions"] != calls[1]["request"]["instructions"]
    assert result["same_model_same_brief"] is True
    assert result["publication_state"] == "BLOCKED_PENDING_HUMAN"
    assert result["tuned"]["response"]["response_id"] == "resp_tuned"
    assert result["plain"]["response"]["response_id"] == "resp_plain"
    assert "secret-key-used-only-by-transport" not in json.dumps(result, ensure_ascii=False)
    assert result["tuned"]["audit"]["human_review_required"] is True
    assert result["plain"]["audit"]["human_review_required"] is True

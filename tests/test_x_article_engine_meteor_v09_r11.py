from x_article_engine.meteor_v09_r11 import audit_draft, build_generation_packet


def sources():
    return [
        {"id": "sales", "status": "VERIFIED", "kind": "PUBLIC_PAGE"},
        {"id": "result", "status": "VERIFIED", "kind": "LEDGER"},
        {"id": "timing", "status": "VERIFIED", "kind": "OFFICIAL"},
    ]


def brief(extra=None):
    evidence = [
        {
            "claim": "暫定ツール実装設計書は10,000円（税込）で、ツール制作そのものは含まない。",
            "source_ref": "sales",
            "status": "VERIFIED",
            "kind": "COMMERCIAL",
        },
        {
            "claim": "必要情報が揃ってから通常5営業日以内を目安に設計書を納品する。",
            "source_ref": "timing",
            "status": "VERIFIED",
            "kind": "TIMING",
        },
    ]
    if extra:
        evidence.extend(extra)
    return {
        "offer": "BridgePatch。まず無料で適合確認し、必要なら一工程の設計へ進む。",
        "target": "毎週、転記・集計・確認・下書きを手作業している小規模事業者。",
        "pain": "AIは使えそうだが、安全に何を自動化するか説明できない。",
        "primary_info": [
            {
                "claim": "直接1円にもならないが、放置すると手を抜けない仕事だと感じた。",
                "source_ref": "human_attestation:one-yen",
                "attested": True,
                "kind": "OPINION",
            }
        ],
        "article_type": "STORY",
        "topic_mode": "BUSINESS",
        "cta": "BridgePatchの無料適合確認を使う。",
        "product_name": "BridgePatch",
        "product_reading": "ブリッジパッチ",
        "evidence": evidence,
    }


def packet(extra=None):
    return build_generation_packet(brief(extra), trusted_source_refs=sources())


def codes(result):
    return {item["code"] for item in result["findings"]}


def test_r11_schema_and_numeric_context_policy_present():
    result = packet()
    assert result["schema_version"] == "0.9-meteor-r11"
    assert "numeric_context_policy" in result


def test_verified_price_reused_as_sales_result_is_reviewed():
    result = audit_draft(
        "BridgePatch（ブリッジパッチ）で10,000円売れました。",
        packet(),
    )
    assert "UNBOUND_NUMERIC_CLAIM" not in codes(result)
    assert "NUMERIC_CONTEXT_REUSE_RISK" in codes(result)
    assert result["status"] == "HUMAN_REVIEW_REQUIRED"


def test_verified_price_reused_as_customer_savings_is_reviewed():
    result = audit_draft(
        "BridgePatch（ブリッジパッチ）で顧客が10,000円節約できました。",
        packet(),
    )
    assert "NUMERIC_CONTEXT_REUSE_RISK" in codes(result)


def test_verified_price_used_as_price_is_not_context_mismatch():
    result = audit_draft(
        "BridgePatch（ブリッジパッチ）の暫定ツール実装設計書は10,000円（税込）です。",
        packet(),
    )
    assert "NUMERIC_CONTEXT_REUSE_RISK" not in codes(result)


def test_verified_timing_used_as_timing_is_not_context_mismatch():
    result = audit_draft(
        "BridgePatch（ブリッジパッチ）の設計書は通常5営業日以内を目安に納品します。",
        packet(),
    )
    assert "NUMERIC_CONTEXT_REUSE_RISK" not in codes(result)


def test_verified_timing_reused_as_result_count_is_reviewed_when_same_token_shape_matches():
    # The unit remains part of the numeric token, so unrelated-unit reuse cannot borrow authority.
    # This test instead confirms the exact token remains bound to timing context only.
    result = audit_draft(
        "BridgePatch（ブリッジパッチ）は5営業日以内に売上が増えます。",
        packet(),
    )
    assert "NUMERIC_CONTEXT_REUSE_RISK" in codes(result)


def test_verified_result_reused_as_price_is_reviewed():
    extra = [
        {
            "claim": "確認済みの売上結果は20,000円だった。",
            "source_ref": "result",
            "status": "VERIFIED",
            "kind": "RESULT",
        }
    ]
    result = audit_draft(
        "BridgePatch（ブリッジパッチ）の料金は20,000円です。",
        packet(extra),
    )
    assert "NUMERIC_CONTEXT_REUSE_RISK" in codes(result)


def test_primary_attested_one_yen_phrase_is_not_forced_into_commercial_bucket():
    result = audit_draft(
        "BridgePatch（ブリッジパッチ）を作る前、直接1円にもならない仕事だと感じました。",
        packet(),
    )
    assert "UNBOUND_NUMERIC_CLAIM" not in codes(result)
    assert "NUMERIC_CONTEXT_REUSE_RISK" not in codes(result)


def test_meta_rejected_bad_result_example_does_not_trigger_context_review():
    result = audit_draft(
        "BridgePatch（ブリッジパッチ）の記事で『10,000円売れました』という表現は使いません。",
        packet(),
    )
    assert "NUMERIC_CONTEXT_REUSE_RISK" not in codes(result)

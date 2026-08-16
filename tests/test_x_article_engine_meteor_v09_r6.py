from x_article_engine.meteor_v09_r6 import audit_draft, build_generation_packet


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


def codes(result):
    return {item["code"] for item in result["findings"]}


def packet():
    return build_generation_packet(brief(), trusted_source_refs=sources())


def test_r6_schema_and_negated_claim_policy_present():
    result = packet()
    assert result["schema_version"] == "0.9-meteor-r6"
    assert "negated_claim_policy" in result


def test_negated_absolute_success_is_not_blocked_as_guarantee():
    result = audit_draft(
        "BridgePatch（ブリッジパッチ）を使っても、必ず成功するとは限りません。",
        packet(),
    )
    assert "UNBOUND_STRONG_CLAIM" not in codes(result)
    assert "ABSOLUTE_GENERALIZATION_LANGUAGE" not in codes(result)


def test_positive_absolute_success_still_blocks():
    result = audit_draft(
        "BridgePatch（ブリッジパッチ）なら必ず成功します。",
        packet(),
    )
    assert "UNBOUND_STRONG_CLAIM" in codes(result)
    assert result["status"] == "BLOCKED"


def test_negated_complete_free_is_not_blocked_as_free_promise():
    result = audit_draft(
        "BridgePatch（ブリッジパッチ）の全工程が完全無料ではありません。",
        packet(),
    )
    assert "UNBOUND_ABSOLUTE_FREE_CLAIM" not in codes(result)


def test_positive_complete_free_still_blocks():
    result = audit_draft(
        "BridgePatch（ブリッジパッチ）は完全無料で使えます。",
        packet(),
    )
    assert "UNBOUND_ABSOLUTE_FREE_CLAIM" in codes(result)
    assert result["status"] == "BLOCKED"


def test_refused_guarantee_phrase_is_not_blocked():
    result = audit_draft(
        "BridgePatch（ブリッジパッチ）について『保証します』とは書けません。",
        packet(),
    )
    assert "UNBOUND_GUARANTEE_LANGUAGE" not in codes(result)


def test_positive_guarantee_phrase_still_blocks():
    result = audit_draft(
        "BridgePatch（ブリッジパッチ）なら完了できます。保証します。",
        packet(),
    )
    assert "UNBOUND_GUARANTEE_LANGUAGE" in codes(result)
    assert result["status"] == "BLOCKED"


def test_negated_unbound_duration_is_not_blocked():
    result = audit_draft(
        "BridgePatch（ブリッジパッチ）の作業が30分で終わるとは言いません。",
        packet(),
    )
    assert "UNBOUND_NUMERIC_CLAIM" not in codes(result)


def test_positive_unbound_duration_still_blocks():
    result = audit_draft(
        "BridgePatch（ブリッジパッチ）の作業は30分で終わります。",
        packet(),
    )
    assert "UNBOUND_NUMERIC_CLAIM" in codes(result)
    assert result["status"] == "BLOCKED"


def test_negated_latest_is_not_reviewed_as_current_claim():
    result = audit_draft(
        "BridgePatch（ブリッジパッチ）のこの説明は最新版ではありません。",
        packet(),
    )
    assert "FRESHNESS_CLAIM_WITHOUT_DATED_EVIDENCE" not in codes(result)


def test_positive_latest_without_timing_evidence_is_still_reviewed():
    result = audit_draft(
        "BridgePatch（ブリッジパッチ）の最新版を説明します。",
        packet(),
    )
    assert "FRESHNESS_CLAIM_WITHOUT_DATED_EVIDENCE" in codes(result)


def test_negated_superlative_is_not_reviewed_as_claim():
    result = audit_draft(
        "BridgePatch（ブリッジパッチ）が世界一だとは言いません。",
        packet(),
    )
    assert "SUPERLATIVE_OR_TOTALIZING_LANGUAGE" not in codes(result)


def test_positive_superlative_is_still_reviewed():
    result = audit_draft(
        "BridgePatch（ブリッジパッチ）は世界一分かりやすい方法です。",
        packet(),
    )
    assert "SUPERLATIVE_OR_TOTALIZING_LANGUAGE" in codes(result)


def test_negated_first_person_biography_is_not_blocked_as_asserted_history():
    result = audit_draft(
        "BridgePatch（ブリッジパッチ）の記事で『私は数年前から業務自動化をしてきた』とは書けません。",
        packet(),
    )
    assert "UNBOUND_IDENTITY_DETAIL" not in codes(result)


def test_positive_unbound_biography_still_blocks():
    result = audit_draft(
        "私は数年前から業務自動化の仕事をしてきました。BridgePatch（ブリッジパッチ）の話をします。",
        packet(),
    )
    assert "UNBOUND_IDENTITY_DETAIL" in codes(result)
    assert result["status"] == "BLOCKED"


def test_negation_does_not_hide_a_separate_positive_claim():
    result = audit_draft(
        "BridgePatch（ブリッジパッチ）の作業は30分で終わります。必ず成功するとは限りません。",
        packet(),
    )
    assert "UNBOUND_NUMERIC_CLAIM" in codes(result)
    assert result["status"] == "BLOCKED"

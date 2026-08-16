from x_article_engine.meteor_v09_r10 import audit_draft, build_generation_packet


def sources():
    return [
        {"id": "sales", "status": "VERIFIED", "kind": "PUBLIC_PAGE"},
        {"id": "timing", "status": "VERIFIED", "kind": "MEASURED"},
        {"id": "count", "status": "VERIFIED", "kind": "LEDGER"},
    ]


def brief(extra_evidence=None):
    evidence = [
        {
            "claim": "暫定ツール実装設計書は10,000円（税込）で、ツール制作そのものは含まない。",
            "source_ref": "sales",
            "status": "VERIFIED",
            "kind": "COMMERCIAL",
        }
    ]
    if extra_evidence:
        evidence.extend(extra_evidence)
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
        "evidence": evidence,
    }


def packet(extra_evidence=None):
    return build_generation_packet(
        brief(extra_evidence=extra_evidence),
        trusted_source_refs=sources(),
    )


def codes(result):
    return {item["code"] for item in result["findings"]}


def test_r10_schema_and_numeric_boundary_policy_present():
    result = packet()
    assert result["schema_version"] == "0.9-meteor-r10"
    assert "numeric_binding_policy" in result
    assert "meta_rejection_policy" in result


def test_verified_10000_yen_does_not_bind_invented_zero_yen():
    result = audit_draft(
        "BridgePatch（ブリッジパッチ）の利用料は0円です。",
        packet(),
    )
    assert "UNBOUND_NUMERIC_CLAIM" in codes(result)
    assert any(item.get("detail") == "0円" for item in result["findings"])
    assert result["status"] == "BLOCKED"


def test_verified_10000_yen_still_binds_exact_10000_yen():
    result = audit_draft(
        "BridgePatch（ブリッジパッチ）の暫定ツール実装設計書は10,000円（税込）です。",
        packet(),
    )
    assert not any(
        item.get("code") == "UNBOUND_NUMERIC_CLAIM" and item.get("detail") == "10,000円"
        for item in result["findings"]
    )


def test_verified_15_minutes_does_not_bind_5_minutes():
    extra = [
        {
            "claim": "確認済みの作業時間は15分だった。",
            "source_ref": "timing",
            "status": "VERIFIED",
            "kind": "RESULT",
        }
    ]
    result = audit_draft(
        "BridgePatch（ブリッジパッチ）の確認済み作業時間は5分でした。",
        packet(extra),
    )
    assert any(
        item.get("code") == "UNBOUND_NUMERIC_CLAIM" and item.get("detail") == "5分"
        for item in result["findings"]
    )


def test_verified_100_people_does_not_bind_zero_people():
    extra = [
        {
            "claim": "確認済みの参加者は100人だった。",
            "source_ref": "count",
            "status": "VERIFIED",
            "kind": "RESULT",
        }
    ]
    result = audit_draft(
        "BridgePatch（ブリッジパッチ）の確認済み参加者は0人でした。",
        packet(extra),
    )
    assert any(
        item.get("code") == "UNBOUND_NUMERIC_CLAIM" and item.get("detail") == "0人"
        for item in result["findings"]
    )


def test_bad_duration_example_shown_only_to_reject_wording_is_not_blocked():
    result = audit_draft(
        "BridgePatch（ブリッジパッチ）の記事で『30分で終わります』と書くのはやめます。",
        packet(),
    )
    assert not any(
        item.get("code") == "UNBOUND_NUMERIC_CLAIM" and item.get("detail") == "30分"
        for item in result["findings"]
    )


def test_bad_100_percent_example_shown_only_to_reject_wording_is_not_asserted():
    result = audit_draft(
        "BridgePatch（ブリッジパッチ）の記事では『100%できます』という表現は使いません。",
        packet(),
    )
    assert not any(item.get("detail") == "100%" and item.get("severity") == "BLOCK" for item in result["findings"])


def test_invented_biography_shown_only_as_forbidden_ai_copy_is_not_asserted_biography():
    result = audit_draft(
        "BridgePatch（ブリッジパッチ）の記事で『私は数年前から業務自動化をしてきた』という経歴をAIに作らせてはいけません。",
        packet(),
    )
    assert "UNBOUND_IDENTITY_DETAIL" not in codes(result)


def test_positive_unbound_biography_still_blocks():
    result = audit_draft(
        "私は数年前から業務自動化をしてきました。BridgePatch（ブリッジパッチ）の話をします。",
        packet(),
    )
    assert "UNBOUND_IDENTITY_DETAIL" in codes(result)
    assert result["status"] == "BLOCKED"


def test_rejected_bad_example_does_not_hide_separate_positive_numeric_claim():
    result = audit_draft(
        "BridgePatch（ブリッジパッチ）は5分で終わります。『30分で終わります』と書くのはやめます。",
        packet(),
    )
    assert any(
        item.get("code") == "UNBOUND_NUMERIC_CLAIM" and item.get("detail") == "5分"
        for item in result["findings"]
    )
    assert result["status"] == "BLOCKED"

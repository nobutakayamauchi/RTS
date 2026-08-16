from x_article_engine.meteor_v09_r9 import audit_draft, build_generation_packet


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
                "claim": "まず無料で制作可否を確認できる。",
                "source_ref": "sales",
                "status": "VERIFIED",
                "kind": "COMMERCIAL",
            },
            {
                "claim": "暫定ツール実装設計書は10,000円（税込）で、ツール制作そのものは含まない。",
                "source_ref": "sales",
                "status": "VERIFIED",
                "kind": "COMMERCIAL",
            },
        ],
    }


def packet():
    return build_generation_packet(brief(), trusted_source_refs=sources())


def codes(result):
    return {item["code"] for item in result["findings"]}


def test_r9_schema_and_cta_semantics_policy_present():
    result = packet()
    assert result["schema_version"] == "0.9-meteor-r9"
    assert "cta_semantics_policy" in result


def test_natural_fit_check_continuation_counts_as_one_cta():
    result = audit_draft(
        "BridgePatch（ブリッジパッチ）の話です。これ、自動化できる？くらいなら無料適合確認から始められます。",
        packet(),
    )
    assert "MULTIPLE_COMMERCIAL_ACTIONS_RISK" not in codes(result)


def test_natural_fit_check_plus_follow_counts_as_two_actions():
    result = audit_draft(
        "BridgePatch（ブリッジパッチ）の話です。無料適合確認から始められます。役立ったらフォローしてください。",
        packet(),
    )
    assert "MULTIPLE_COMMERCIAL_ACTIONS_RISK" in codes(result)


def test_describing_fit_check_concept_is_not_itself_a_cta():
    result = audit_draft(
        "BridgePatch（ブリッジパッチ）の記事で、無料適合確認という考え方を説明します。",
        packet(),
    )
    assert "MULTIPLE_COMMERCIAL_ACTIONS_RISK" not in codes(result)


def test_fit_check_plus_rejected_follow_is_still_single_cta():
    result = audit_draft(
        "BridgePatch（ブリッジパッチ）は無料適合確認から始められます。フォローしてくださいとは言いません。",
        packet(),
    )
    assert "MULTIPLE_COMMERCIAL_ACTIONS_RISK" not in codes(result)


def test_log_term_does_not_fire_inside_program_word():
    result = audit_draft(
        "BridgePatch（ブリッジパッチ）の話です。プログラムの不具合を直しました。",
        packet(),
    )
    assert not any(
        item.get("code") == "UNEXPLAINED_TERM_ON_FIRST_USE" and item.get("detail") == "ログ"
        for item in result["findings"]
    )


def test_real_log_term_still_requires_explanation():
    result = audit_draft(
        "BridgePatch（ブリッジパッチ）の話です。ログを確認しました。",
        packet(),
    )
    assert any(
        item.get("code") == "UNEXPLAINED_TERM_ON_FIRST_USE" and item.get("detail") == "ログ"
        for item in result["findings"]
    )


def test_explained_log_term_passes_terminology_gate():
    result = audit_draft(
        "BridgePatch（ブリッジパッチ）の話です。ログという、プログラムがいつ何をしたか残す記録を確認しました。",
        packet(),
    )
    assert not any(
        item.get("code") == "UNEXPLAINED_TERM_ON_FIRST_USE" and item.get("detail") == "ログ"
        for item in result["findings"]
    )

from x_article_engine.terminology import audit_draft, build_generation_packet


def source():
    return {
        "offer": "BridgePatchで一工程の手作業を小さく改善する。",
        "target": "毎週、転記や確認を手作業している小規模事業者。",
        "pain": "AIを使えそうでも、何をどう渡せばいいか分からない。",
        "primary_info": [
            {
                "claim": "動画編集でCapCutに挑戦したが挫折し、自分が迷わないよう機能を削ったツールを作った。",
                "source_ref": "human_attestation:origin",
                "attested": True,
                "kind": "ORIGIN",
            }
        ],
        "article_type": "HOW_TO",
        "topic_mode": "BUSINESS",
        "cta": "BridgePatchの無料適合確認を使う。",
        "product_name": "BridgePatch",
        "product_reading": "ブリッジパッチ",
        "terms_to_explain": [
            {
                "term": "CapCut",
                "explanation": "スマホなどで使える動画編集アプリ",
                "anchors": ["動画編集", "アプリ"],
                "min_anchor_matches": 2,
            }
        ],
        "evidence": [
            {
                "claim": "暫定ツール実装設計書は10,000円（税込）で、ツール実装は含まない。",
                "source_ref": "bridgepatch-sales-page",
                "status": "VERIFIED",
                "kind": "COMMERCIAL",
            }
        ],
    }


def trusted():
    return [
        {"id": "bridgepatch-sales-page", "status": "VERIFIED", "kind": "PUBLIC_PAGE"}
    ]


def packet():
    return build_generation_packet(source(), trusted_source_refs=trusted())


def test_packet_defaults_to_general_non_technical_reader():
    result = packet()
    assert result["schema_version"] == "0.4"
    assert result["reader_model"]["knowledge_level"] == "GENERAL_NON_TECH"
    assert result["terminology_policy"]["explain_on_first_use"] is True


def test_first_product_mention_requires_katakana_reading_once():
    result = packet()
    audit = audit_draft(
        "BridgePatchでは、まず作業を一工程だけ切ります。",
        result,
    )
    assert audit["status"] == "BLOCKED"
    assert any(
        item["code"] == "MISSING_PRODUCT_READING_ON_FIRST_USE"
        for item in audit["findings"]
    )


def test_product_reading_once_then_plain_name_passes_product_gate():
    result = packet()
    audit = audit_draft(
        "BridgePatch（ブリッジパッチ）は一工程だけを扱います。後でBridgePatchの無料確認を使えます。",
        result,
    )
    assert not any(
        item["code"].startswith("MISSING_PRODUCT") or item["code"] == "REPEATED_PRODUCT_READING"
        for item in audit["findings"]
    )


def test_repeated_product_reading_is_blocked():
    result = packet()
    audit = audit_draft(
        "BridgePatch（ブリッジパッチ）を紹介します。後でもBridgePatch（ブリッジパッチ）を使います。",
        result,
    )
    assert any(item["code"] == "REPEATED_PRODUCT_READING" for item in audit["findings"])


def test_csv_without_first_use_explanation_is_blocked():
    result = packet()
    audit = audit_draft(
        "BridgePatch（ブリッジパッチ）ではCSVを受け取って処理します。",
        result,
    )
    assert any(
        item["code"] == "UNEXPLAINED_TERM_ON_FIRST_USE" and item["detail"] == "CSV"
        for item in audit["findings"]
    )


def test_csv_with_plain_language_explanation_passes_term_gate():
    result = packet()
    audit = audit_draft(
        "BridgePatch（ブリッジパッチ）では、CSVというExcelなどで開ける表形式のデータファイルを扱えます。",
        result,
    )
    assert not any(
        item["code"] == "UNEXPLAINED_TERM_ON_FIRST_USE" and item["detail"] == "CSV"
        for item in audit["findings"]
    )


def test_debug_without_explanation_is_blocked():
    result = packet()
    audit = audit_draft(
        "BridgePatch（ブリッジパッチ）の話です。次にデバッグをしました。",
        result,
    )
    assert any(
        item["code"] == "UNEXPLAINED_TERM_ON_FIRST_USE" and item["detail"] == "デバッグ"
        for item in audit["findings"]
    )


def test_debug_with_plain_language_explanation_passes_term_gate():
    result = packet()
    audit = audit_draft(
        "BridgePatch（ブリッジパッチ）の話です。デバッグ、つまりプログラムの不具合の原因を探して直す作業も必要になりました。",
        result,
    )
    assert not any(
        item["code"] == "UNEXPLAINED_TERM_ON_FIRST_USE" and item["detail"] == "デバッグ"
        for item in audit["findings"]
    )


def test_custom_capcut_term_is_explained_on_first_use():
    result = packet()
    audit = audit_draft(
        "BridgePatch（ブリッジパッチ）を作る前、CapCutという動画編集アプリに挑戦しました。",
        result,
    )
    assert not any(
        item["code"] == "UNEXPLAINED_TERM_ON_FIRST_USE" and item["detail"] == "CapCut"
        for item in audit["findings"]
    )

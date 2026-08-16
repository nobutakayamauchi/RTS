from x_article_engine.ai_humanity import audit_draft, build_generation_packet


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
                "claim": "私はこの状態をシムシティ化と呼んでいる。",
                "source_ref": "human_attestation:label",
                "attested": True,
                "kind": "OPINION",
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


def packet():
    return build_generation_packet(brief(), trusted_source_refs=sources())


def test_packet_adds_material_first_and_ai_smell_policy():
    result = packet()
    assert result["schema_version"] == "0.6"
    assert "recipe_vs_ingredients" in result["material_first_policy"]
    assert "abstract_word_rule" in result["anti_ai_smell_policy"]
    assert "specificity_without_hallucination" in result["specificity_policy"]


def test_empty_abstract_words_are_reviewed_not_automatically_blocked():
    result = audit_draft(
        "全体の構造を理解することが重要です。\n"
        "BridgePatch（ブリッジパッチ）は無料適合確認から始めます。",
        packet(),
    )
    codes = [item["code"] for item in result["findings"]]
    assert "ABSTRACT_WORD_WITHOUT_PAYLOAD" in codes
    assert result["ai_smell_gate"] == "REVIEW"


def test_concrete_use_of_design_word_is_not_flagged_as_empty_abstraction():
    result = audit_draft(
        "BridgePatch（ブリッジパッチ）の設計では、入力→処理→出力を先に書きます。",
        packet(),
    )
    empty_abstract = [
        item for item in result["findings"] if item["code"] == "ABSTRACT_WORD_WITHOUT_PAYLOAD"
    ]
    assert not empty_abstract


def test_model_coined_label_is_blocked():
    result = audit_draft(
        "BridgePatch（ブリッジパッチ）を作っています。\n"
        "この現象を『自動化迷子現象』と呼んでいます。",
        packet(),
    )
    assert any(item["code"] == "MODEL_COINED_LABEL_RISK" for item in result["findings"])
    assert result["status"] == "BLOCKED"


def test_attested_source_originated_label_is_allowed():
    result = audit_draft(
        "BridgePatch（ブリッジパッチ）を作っています。\n"
        "この状態を『シムシティ化』と呼んでいます。",
        packet(),
    )
    assert not any(item["code"] == "MODEL_COINED_LABEL_RISK" for item in result["findings"])


def test_boilerplate_and_giant_subject_are_review_findings():
    result = audit_draft(
        "BridgePatch（ブリッジパッチ）を使うことが可能です。\n"
        "多くの人は自動化で困っているのではないでしょうか。",
        packet(),
    )
    codes = {item["code"] for item in result["findings"]}
    assert "AI_BOILERPLATE_PHRASE" in codes
    assert "GENERIC_OVERSIZED_SUBJECT" in codes


def test_human_gate_contains_material_quality_checks():
    checks = "\n".join(packet()["human_gate"]["checks"])
    assert "構造・設計・本質" in checks
    assert "three concrete things" in checks
    assert "could only have come from" in checks

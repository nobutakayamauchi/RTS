from x_article_engine.longform_filter import audit_draft, build_generation_packet


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
                "claim": "これが私がこの仕事を始めたきっかけである。",
                "source_ref": "human_attestation:origin",
                "attested": True,
                "kind": "ORIGIN",
            },
        ],
        "article_type": "STORY",
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


def test_packet_adds_value_driven_longform_layer():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    assert packet["schema_version"] == "0.7"
    assert "length_rule" in packet["longform_policy"]
    assert "section_utility_rule" in packet["longform_policy"]
    assert "heading_rule" in packet["longform_policy"]
    assert "why_rule" in packet["longform_policy"]
    assert "cta_continuity_rule" in packet["longform_policy"]
    assert "selective_attrition" in packet["longform_reader_journey"]


def test_reference_metrics_and_fixed_length_are_not_imported_as_truth():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    rendered = repr(packet)
    assert "8,645" not in rendered
    assert "1.8万" not in rendered
    assert "868万円" not in rendered
    assert "6,000字" not in rendered
    assert "a fixed character count required for filtering" in rendered


def test_dense_mobile_paragraph_is_reviewed_not_blocked_by_longform_layer():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    draft = "これは読みやすさを確認するための文章です。" * 20
    result = audit_draft(draft, packet)
    codes = [item["code"] for item in result["findings"]]
    assert "DENSE_MOBILE_PARAGRAPH" in codes
    assert result["status"] in {"HUMAN_REVIEW_REQUIRED", "BLOCKED"}


def test_long_draft_without_scan_path_is_reviewed():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    paragraph = "手作業が増える理由を一つずつ説明します。ここでは範囲を小さく切る考え方を扱います。"
    draft = "\n\n".join([paragraph] * 80)
    result = audit_draft(draft, packet)
    codes = [item["code"] for item in result["findings"]]
    assert "LONGFORM_WEAK_SCAN_PATH" in codes


def test_long_draft_with_informative_headings_has_scan_path():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    paragraph = "手作業が増える理由を一つずつ説明します。範囲を小さく切ると、どこで止めるかを決めやすくなります。"
    sections = []
    for heading in [
        "■ なぜ仕事が増え続けるのか",
        "■ 全部ではなく一工程だけ切る",
        "■ 失敗したら人に戻せるようにする",
        "■ その考えを仕事に使う",
    ]:
        sections.append(heading + "\n\n" + "\n\n".join([paragraph] * 18))
    draft = "\n\n".join(sections)
    result = audit_draft(draft, packet)
    codes = [item["code"] for item in result["findings"]]
    assert "LONGFORM_WEAK_SCAN_PATH" not in codes


def test_human_gate_checks_section_utility_and_cta_continuity():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    checks = "\n".join(packet["human_gate"]["checks"])
    assert "Could I delete a section" in checks
    assert "scan only the headings" in checks
    assert "why it matters" in checks
    assert "commercial break" in checks

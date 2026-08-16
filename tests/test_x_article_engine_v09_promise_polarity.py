from x_article_engine import audit_draft, build_generation_packet


def sources():
    return [{"id": "terms", "status": "VERIFIED", "kind": "PUBLIC_PAGE"}]


def packet(claim):
    brief = {
        "offer": "テスト用のサービス。",
        "target": "一般読者。",
        "pain": "条件を誤解したくない。",
        "primary_info": [],
        "article_type": "HOW_TO",
        "topic_mode": "BUSINESS",
        "cta": "条件を確認する。",
        "evidence": [
            {
                "claim": claim,
                "source_ref": "terms",
                "status": "VERIFIED",
                "kind": "COMMERCIAL",
            }
        ],
    }
    return build_generation_packet(brief, trusted_source_refs=sources())


def codes(result):
    return {item["code"] for item in result["findings"]}


def test_negative_refund_evidence_does_not_authorize_positive_refund_promise():
    result = audit_draft("合わなければ全額返金します。", packet("返金は行いません。"))
    assert result["status"] == "BLOCKED"
    assert "CONTRADICTS_VERIFIED_COMMERCIAL_TERM" in codes(result) or "UNBOUND_STRONG_CLAIM" in codes(result)


def test_possible_extra_fee_evidence_does_not_authorize_no_extra_fee_promise():
    result = audit_draft(
        "開始後の追加料金はありません。",
        packet("内容によっては追加料金が発生する場合があります。"),
    )
    assert result["status"] == "BLOCKED"
    assert "CONTRADICTS_VERIFIED_COMMERCIAL_TERM" in codes(result) or "UNBOUND_STRONG_CLAIM" in codes(result)


def test_no_guarantee_evidence_does_not_authorize_guarantee():
    result = audit_draft("成果を保証します。", packet("成果は保証しません。"))
    assert result["status"] == "BLOCKED"
    assert "CONTRADICTS_VERIFIED_COMMERCIAL_TERM" in codes(result) or "UNBOUND_STRONG_CLAIM" in codes(result)


def test_limited_evidence_does_not_authorize_unlimited_promise():
    result = audit_draft("利用回数は無制限です。", packet("利用回数には上限があります。"))
    assert result["status"] == "BLOCKED"
    assert "CONTRADICTS_VERIFIED_COMMERCIAL_TERM" in codes(result) or "UNBOUND_STRONG_CLAIM" in codes(result)


def test_negative_refund_term_can_be_stated_as_negative():
    result = audit_draft("返金は行いません。", packet("返金は行いません。"))
    assert "CONTRADICTS_VERIFIED_COMMERCIAL_TERM" not in codes(result)


def test_possible_extra_fee_term_can_be_stated_without_strengthening():
    result = audit_draft(
        "内容によっては追加料金が発生する場合があります。",
        packet("内容によっては追加料金が発生する場合があります。"),
    )
    assert "CONTRADICTS_VERIFIED_COMMERCIAL_TERM" not in codes(result)


def test_no_guarantee_term_can_be_stated_as_no_guarantee():
    result = audit_draft("成果は保証しません。", packet("成果は保証しません。"))
    assert "CONTRADICTS_VERIFIED_COMMERCIAL_TERM" not in codes(result)


def test_unrelated_verified_word_does_not_silence_strong_promise_gate():
    result = audit_draft(
        "永続的に利用できます。",
        packet("このページは永続的な提供を保証するものではありません。"),
    )
    assert result["status"] == "BLOCKED"

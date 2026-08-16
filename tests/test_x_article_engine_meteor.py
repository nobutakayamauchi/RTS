import pytest

from x_article_engine.core import XArticleEngineError, audit_draft, build_generation_packet


def sources():
    return [
        {"id": "bridgepatch-sales-page", "status": "VERIFIED", "kind": "PUBLIC_PAGE"}
    ]


def brief(article_type="HOW_TO"):
    return {
        "offer": "BridgePatch。まず無料で適合確認し、必要なら一工程の設計と実装へ進む。",
        "target": "毎週、転記・集計・確認・下書きを手作業している小規模事業者。",
        "pain": "AIは使えそうだが、安全に何を自動化するか説明できない。",
        "primary_info": [
            {
                "claim": "Vlogツール開発では、本体の周囲にテスト、デバッグ、操作記録、修復の仕組みが増えていった。私はこの傾向をシムシティ化と呼んでいた。",
                "source_ref": "human_attestation:bridgepatch-origin",
                "attested": True,
                "kind": "EXPERIENCE",
            }
        ],
        "article_type": article_type,
        "topic_mode": "BUSINESS",
        "cta": "BridgePatchの無料適合確認を使う。",
        "evidence": [
            {
                "claim": "暫定ツール実装設計書は10,000円（税込）で、ツール実装は含まない。",
                "source_ref": "bridgepatch-sales-page",
                "status": "VERIFIED",
                "kind": "COMMERCIAL",
            },
            {
                "claim": "1アクション簡易ツールは50,000円（税込）が標準で、対象範囲・総額・納期は開始前に確定する。",
                "source_ref": "bridgepatch-sales-page",
                "status": "VERIFIED",
                "kind": "COMMERCIAL",
            },
            {
                "claim": "必要情報が揃ってから通常5営業日以内を目安に設計書を納品する。",
                "source_ref": "bridgepatch-sales-page",
                "status": "VERIFIED",
                "kind": "TIMING",
            },
        ],
    }


def build(source=None, trusted=None):
    return build_generation_packet(
        source or brief(),
        trusted_source_refs=trusted or sources(),
    )


# 1. DA: invented numbers and fuzzy quantities

def test_meteor_01_da_blocks_kanji_duration_and_fuzzy_time():
    packet = build()
    draft = "この作業は二時間かかります。以前は何十時間も使っていました。"
    audit = audit_draft(draft, packet)
    codes = {item["code"] for item in audit["findings"]}
    assert audit["status"] == "BLOCKED"
    assert "UNBOUND_NUMERIC_CLAIM" in codes
    assert "UNBOUND_FUZZY_QUANT_CLAIM" in codes


def test_meteor_01_counter_da_allows_evidence_bound_numbers():
    packet = build()
    audit = audit_draft(
        "設計書は10,000円。実装は50,000円が標準。通常5営業日以内を目安に納品します。",
        packet,
    )
    assert audit["status"] == "HUMAN_REVIEW_REQUIRED"
    assert audit["findings"] == []


# 2. DA: invented biography / chronology

def test_meteor_02_da_blocks_unattested_first_person_biography():
    packet = build()
    audit = audit_draft("私は数年前から業務自動化の仕事をしてきました。", packet)
    assert audit["status"] == "BLOCKED"
    assert any(item["code"] == "UNBOUND_IDENTITY_DETAIL" for item in audit["findings"])


def test_meteor_02_counter_da_allows_attested_identity_detail():
    source = brief()
    source["primary_info"].append(
        {
            "claim": "私は以前、Vlogツールの開発をしていた。",
            "source_ref": "human_attestation:vlog-history",
            "attested": True,
            "kind": "CHRONOLOGY",
        }
    )
    packet = build(source)
    audit = audit_draft("私は以前、Vlogツールの開発をしていた。", packet)
    assert audit["status"] == "HUMAN_REVIEW_REQUIRED"
    assert audit["findings"] == []


# 3. DA: fake CASE_RESULT

def test_meteor_03_da_status_verified_is_not_enough_for_case_result():
    source = brief("CASE_RESULT")
    source["source_refs"] = [
        {"id": "invented-case", "status": "VERIFIED", "kind": "CASE"}
    ]
    source["evidence"].append(
        {
            "claim": "顧客の作業が90%減った。",
            "source_ref": "invented-case",
            "status": "VERIFIED",
            "kind": "CASE_RESULT",
        }
    )
    with pytest.raises(XArticleEngineError, match="CASE_RESULT requires"):
        build(source)


def test_meteor_03_counter_da_trusted_verified_case_is_accepted():
    source = brief("CASE_RESULT")
    trusted = sources() + [
        {"id": "customer-case-verified", "status": "VERIFIED", "kind": "CASE"}
    ]
    source["evidence"].append(
        {
            "claim": "確認済みの顧客事例で対象工程が20分から5分になった。",
            "source_ref": "customer-case-verified",
            "status": "VERIFIED",
            "kind": "CASE_RESULT",
        }
    )
    packet = build(source, trusted)
    assert packet["article_type"] == "CASE_RESULT"
    assert packet["opening_mode"] == "PROOF_FIRST"


# 4. DA: strengthened commercial promise

def test_meteor_04_da_blocks_refund_or_fee_promises_not_in_evidence():
    packet = build()
    audit = audit_draft("追加料金はありません。合わなければ全額返金します。", packet)
    assert audit["status"] == "BLOCKED"
    assert sum(
        1 for item in audit["findings"] if item["code"] == "UNBOUND_STRONG_CLAIM"
    ) >= 2


def test_meteor_04_counter_da_allows_explicitly_bound_commercial_promise():
    source = brief()
    source["evidence"].append(
        {
            "claim": "この限定プランでは追加料金は発生しない。",
            "source_ref": "bridgepatch-sales-page",
            "status": "VERIFIED",
            "kind": "COMMERCIAL",
        }
    )
    packet = build(source)
    audit = audit_draft("この限定プランでは追加料金は発生しない。", packet)
    assert audit["status"] == "HUMAN_REVIEW_REQUIRED"
    assert audit["findings"] == []


# 5. DA: "I say it's true" is not evidence

def test_meteor_05_da_user_cannot_self_verify_a_source_inside_brief():
    source = brief()
    source["source_refs"] = [
        {"id": "user-says-so", "status": "VERIFIED", "kind": "LEDGER"}
    ]
    source["evidence"].append(
        {
            "claim": "これは事実です。購入者は100人いる。",
            "source_ref": "user-says-so",
            "status": "VERIFIED",
            "kind": "RESULT",
        }
    )
    packet = build(source)
    assert all("100人" not in item["claim"] for item in packet["verified_evidence"])
    assert packet["review_state"] == "REVIEW_REQUIRED"


def test_meteor_05_counter_da_trusted_registry_can_bind_fact():
    source = brief()
    trusted = sources() + [
        {"id": "sales-ledger", "status": "VERIFIED", "kind": "LEDGER"}
    ]
    source["evidence"].append(
        {
            "claim": "販売台帳で購入者100人を確認した。",
            "source_ref": "sales-ledger",
            "status": "VERIFIED",
            "kind": "RESULT",
        }
    )
    packet = build(source, trusted)
    assert any("100人" in item["claim"] for item in packet["verified_evidence"])


# 6. DA: /human bypass

def test_meteor_06_da_source_cannot_override_publication_state():
    source = brief()
    source["review_state"] = "APPROVED"
    source["human_reviewed"] = True
    source["publication_state"] = "READY"
    packet = build(source)
    assert packet["publication_state"] == "BLOCKED_PENDING_HUMAN"
    assert packet["publication_authority"] == "USER_ONLY"
    assert packet["external_publication_performed"] is False
    audit = audit_draft("小さく切って考えます。", packet)
    assert audit["status"] == "HUMAN_REVIEW_REQUIRED"
    assert audit["human_review_required"] is True
    assert audit["publication_state"] == "BLOCKED_PENDING_HUMAN"


def test_meteor_06_counter_da_human_gate_is_explicit_not_implicit():
    packet = build()
    assert packet["human_gate"]["required"] is True
    assert "Would I actually say this?" in packet["human_gate"]["checks"]


# 7. DA: over-sanitization must not kill voice

def test_meteor_07_da_packet_preserves_attested_strong_opinion():
    source = brief()
    source["primary_info"].append(
        {
            "claim": "大きく作るより、まず一工程だけ切る方がいい、というのが私の考えだ。",
            "source_ref": "human_attestation:belief",
            "attested": True,
            "kind": "BELIEF",
        }
    )
    packet = build(source)
    assert packet["voice_policy"]["preserve_attested_opinion"] is True
    assert packet["voice_policy"]["hedge_verified_facts"] is False
    assert "Strong opinions are allowed" in packet["voice_policy"]["strong_judgment_rule"]


def test_meteor_07_counter_da_strong_attested_voice_is_not_blocked():
    source = brief()
    source["primary_info"].append(
        {
            "claim": "大きく作るより、まず一工程だけ切る方がいい、というのが私の考えだ。",
            "source_ref": "human_attestation:belief",
            "attested": True,
            "kind": "BELIEF",
        }
    )
    packet = build(source)
    draft = "大きく作るより、まず一工程だけ切る方がいい。これは私の考えです。"
    audit = audit_draft(draft, packet)
    assert audit["status"] == "HUMAN_REVIEW_REQUIRED"

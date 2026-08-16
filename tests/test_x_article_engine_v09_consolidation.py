import pytest

from x_article_engine.core import XArticleEngineError
from x_article_engine import meteor_v09_r5 as stacked
from x_article_engine import v09 as flat


def sources():
    return [
        {"id": "sales", "status": "VERIFIED", "kind": "PUBLIC_PAGE"},
        {"id": "dated", "status": "VERIFIED", "kind": "OFFICIAL"},
        {"id": "risk", "status": "VERIFIED", "kind": "OFFICIAL"},
        {"id": "counter", "status": "VERIFIED", "kind": "REPORT"},
    ]


def brief(**overrides):
    data = {
        "offer": "BridgePatch。まず無料で適合確認し、必要なら一工程の設計へ進む。",
        "target": "毎週、転記・集計・確認・下書きを手作業している小規模事業者。",
        "pain": "AIは使えそうだが、安全に何を自動化するか説明できない。",
        "primary_info": [
            {
                "claim": "あー、めんどくさくてキレそう。",
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
    data.update(overrides)
    return data


def codes(result):
    return {item["code"] for item in result["findings"]}


def build_pair(data=None):
    src = data or brief()
    return (
        stacked.build_generation_packet(src, trusted_source_refs=sources()),
        flat.build_generation_packet(src, trusted_source_refs=sources()),
    )


def test_flat_keeps_key_generation_contract_from_stacked_candidate():
    old, new = build_pair()
    for key in [
        "article_type",
        "opening_mode",
        "publication_state",
        "publication_authority",
        "external_publication_performed",
        "review_state",
    ]:
        assert new[key] == old[key]
    assert len(new["verified_primary_info"]) == len(old["verified_primary_info"])
    assert len(new["verified_evidence"]) == len(old["verified_evidence"])
    assert new["schema_version"] == "0.9"
    assert old["schema_version"] == "0.9-meteor-r5"


@pytest.mark.parametrize(
    "draft,required_code,expected_status",
    [
        (
            "BridgePatch（ブリッジパッチ）の記事です。Claude Codeを --dangerously-skip-permissions で起動してください。",
            "UNSAFE_PERMISSION_OR_SECURITY_BYPASS",
            "BLOCKED",
        ),
        (
            "BridgePatch（ブリッジパッチ）の記事です。APIキーをClaudeのプロンプトに貼り付けて送信してください。",
            "SECRET_TRANSFER_TO_MODEL_RISK",
            "BLOCKED",
        ),
        (
            "BridgePatch（ブリッジパッチ）は完全無料で使えます。",
            "UNBOUND_ABSOLUTE_FREE_CLAIM",
            "BLOCKED",
        ),
        (
            "BridgePatch（ブリッジパッチ）の手順なら完了できます。保証します。",
            "UNBOUND_GUARANTEE_LANGUAGE",
            "BLOCKED",
        ),
        (
            "BridgePatch（ブリッジパッチ）の話です。多くの人は仕事の本質を理解していません。",
            "ABSTRACT_WORD_WITHOUT_PAYLOAD",
            "HUMAN_REVIEW_REQUIRED",
        ),
        (
            "BridgePatch（ブリッジパッチ）の話です。BAN回避を目的にしたステルス配信という主張がありますが、この記事では推奨しません。",
            "PLATFORM_EVASION_LANGUAGE",
            "HUMAN_REVIEW_REQUIRED",
        ),
        (
            "BridgePatch（ブリッジパッチ）の話です。BAN回避のためにゼロ幅文字を挿入して配信します。",
            "PLATFORM_EVASION_OPERATIONAL_INSTRUCTION",
            "BLOCKED",
        ),
    ],
)
def test_flat_preserves_meteor_attack_outcomes(draft, required_code, expected_status):
    old_packet, new_packet = build_pair()
    old = stacked.audit_draft(draft, old_packet)
    new = flat.audit_draft(draft, new_packet)
    assert required_code in codes(old)
    assert required_code in codes(new)
    assert old["status"] == expected_status
    assert new["status"] == expected_status


def test_flat_and_stacked_both_keep_safe_bridgepatch_story_out_of_security_blocks():
    old_packet, new_packet = build_pair()
    draft = (
        "あー、めんどくさくてキレそう。\n"
        "修正して確認する。直したら別の場所をもう一度確認する。まさに無限修正だった。\n"
        "そこで全部を自動化するのではなく、一工程だけ切ることにした。\n"
        "間違えたときは人間に戻せるようにする。\n"
        "その考えを仕事に使える形にしたのがBridgePatch（ブリッジパッチ）です。"
    )
    security_codes = {
        "UNSAFE_PERMISSION_OR_SECURITY_BYPASS",
        "SECRET_TRANSFER_TO_MODEL_RISK",
        "HIGH_RISK_WITHOUT_FRONT_STOP_GATE",
        "UNBOUND_GUARANTEE_LANGUAGE",
        "PLATFORM_EVASION_OPERATIONAL_INSTRUCTION",
    }
    assert not security_codes.intersection(codes(stacked.audit_draft(draft, old_packet)))
    assert not security_codes.intersection(codes(flat.audit_draft(draft, new_packet)))


def test_flat_origin_only_falls_back_to_relatable_like_stacked_r5():
    data = brief()
    data["primary_info"] = [
        {
            "claim": "これが私がこの仕事を始めたきっかけである。",
            "source_ref": "human_attestation:origin",
            "attested": True,
            "kind": "ORIGIN",
        }
    ]
    old, new = build_pair(data)
    assert old["opening_mode"] == "RELATABLE"
    assert new["opening_mode"] == "RELATABLE"


def test_flat_contrarian_requires_basis_and_accepts_bound_human_opinion():
    data = brief(opening_mode="CONTRARIAN")
    data["primary_info"] = [
        {
            "claim": "全部自動化するより、一工程だけ切る方がいいと私は考えている。",
            "source_ref": "human_attestation:counterpoint",
            "attested": True,
            "kind": "OPINION",
        }
    ]
    with pytest.raises(XArticleEngineError, match="counterpoint_basis"):
        flat.build_generation_packet(data, trusted_source_refs=sources())

    data["counterpoint_basis"] = {
        "kind": "HUMAN_OPINION",
        "source_ref": "human_attestation:counterpoint",
    }
    packet = flat.build_generation_packet(data, trusted_source_refs=sources())
    assert packet["opening_mode"] == "CONTRARIAN"


def test_flat_current_mode_requires_dated_verified_evidence():
    with pytest.raises(XArticleEngineError, match="verified dated/TIMING evidence"):
        flat.build_generation_packet(
            brief(freshness_mode="CURRENT", as_of="2026-08-16"),
            trusted_source_refs=sources(),
        )

    data = brief(freshness_mode="CURRENT", as_of="2026-08-16")
    data["evidence"] = [
        *data["evidence"],
        {
            "claim": "この仕様は2026年8月16日時点の公式情報で確認した。",
            "source_ref": "dated",
            "status": "VERIFIED",
            "kind": "TIMING",
        },
    ]
    packet = flat.build_generation_packet(data, trusted_source_refs=sources())
    assert packet["freshness"]["mode"] == "CURRENT"


def test_flat_high_risk_mode_requires_verified_risk_evidence():
    with pytest.raises(XArticleEngineError, match="HIGH-risk articles require"):
        flat.build_generation_packet(
            brief(risk_level="HIGH", topic_mode="PROCEDURAL"),
            trusted_source_refs=sources(),
        )

    data = brief(risk_level="HIGH", topic_mode="PROCEDURAL")
    data["evidence"] = [
        *data["evidence"],
        {
            "claim": "この操作は権限を広げるため、誤操作時の影響範囲が大きくなる。",
            "source_ref": "risk",
            "status": "VERIFIED",
            "kind": "RISK",
        },
    ]
    packet = flat.build_generation_packet(data, trusted_source_refs=sources())
    assert packet["risk_policy"]["risk_level"] == "HIGH"

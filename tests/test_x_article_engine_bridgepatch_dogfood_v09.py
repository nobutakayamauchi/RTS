from x_article_engine import audit_draft, build_generation_packet


def sources():
    return [
        {"id": "bridgepatch-sales-page", "status": "VERIFIED", "kind": "PUBLIC_PAGE"},
    ]


def brief():
    return {
        "offer": "BridgePatch。まず無料で制作可否を確認し、適合すれば一工程の暫定ツール実装設計書へ進む。",
        "target": "毎週、転記・集計・確認・下書きのような小さい手作業が残っている小規模事業者。",
        "pain": "大きなシステムを入れるほどではない手作業ほど残り、AIを使えそうでもどこまで任せるか説明しづらい。",
        "primary_info": [
            {
                "claim": "あー、めんどくさくてキレそう。自前のプログラムを前にそう感じた。",
                "source_ref": "human_attestation:pain",
                "attested": True,
                "kind": "PAIN",
            },
            {
                "claim": "CapCutが楽ですよと言われて試したが、私は使い続けられなかった。",
                "source_ref": "human_attestation:capcut",
                "attested": True,
                "kind": "FAILURE",
            },
            {
                "claim": "自分が迷わないよう機能や操作、ボタンを減らしたツールを作った。人にも使ってもらおうとすると、自分では想定していなかった操作まで考える必要が出てきた。",
                "source_ref": "human_attestation:tool",
                "attested": True,
                "kind": "EXPERIENCE",
            },
            {
                "claim": "直す、チェックする、また直す。全体を確認すると別の不具合が出て、そこを直すと別の場所が壊れる。まさに無限修正である、と感じた。",
                "source_ref": "human_attestation:loop",
                "attested": True,
                "kind": "EXPERIENCE",
            },
            {
                "claim": "ダメだ。マジで終わる気がしない。",
                "source_ref": "human_attestation:feeling",
                "attested": True,
                "kind": "PAIN",
            },
            {
                "claim": "直接1円にもならないが、放置すると不具合やクレームの元になり得るので手を抜けない仕事だと感じた。",
                "source_ref": "human_attestation:stakes",
                "attested": True,
                "kind": "OPINION",
            },
            {
                "claim": "本体を成立させるための周辺仕事が増えていく状態を、私はシムシティ化と呼んでいた。",
                "source_ref": "human_attestation:simcity",
                "attested": True,
                "kind": "OPINION",
            },
            {
                "claim": "全部を自動化するより、今いちばん邪魔をしている一工程だけ切る方がいい、というのが私の考えだ。",
                "source_ref": "human_attestation:belief",
                "attested": True,
                "kind": "BELIEF",
            },
            {
                "claim": "何をするかだけでなく、どこで止めるか、失敗したらどこで人間に戻すかを先に決めた方がいいと考えている。",
                "source_ref": "human_attestation:boundary",
                "attested": True,
                "kind": "BELIEF",
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
        "terms_to_explain": [
            {
                "term": "CapCut",
                "explanation": "スマホなどで使える動画編集アプリ",
                "anchors": ["動画編集", "アプリ"],
                "min_anchor_matches": 2,
            },
            {
                "term": "シムシティ",
                "explanation": "街を少しずつ作り広げていくゲーム",
                "anchors": ["街づくり", "ゲーム"],
                "min_anchor_matches": 2,
            },
        ],
        "evidence": [
            {
                "claim": "まず無料で制作可否を確認できる。",
                "source_ref": "bridgepatch-sales-page",
                "status": "VERIFIED",
                "kind": "COMMERCIAL",
            },
            {
                "claim": "暫定ツール実装設計書は10,000円（税込）で、ツール制作そのものは含まない。",
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
            {
                "claim": "実装を希望する場合は別途合意し、1アクション簡易ツールは50,000円（税込）を標準とする。対象範囲・総額・納期は開始前に確定する。",
                "source_ref": "bridgepatch-sales-page",
                "status": "VERIFIED",
                "kind": "COMMERCIAL",
            },
            {
                "claim": "人命、医療・介護判断、給与・決済の最終確定など高リスク業務は原則対象外または個別審査とする。",
                "source_ref": "bridgepatch-sales-page",
                "status": "VERIFIED",
                "kind": "SCOPE",
            },
        ],
    }


def article():
    return """# 「1円にもならないのに手を抜けない」無限修正が、この仕事を始めたきっかけだった

「あー、めんどくさくてキレそう。」

自分で作っていたプログラムを前に、そう思った。

きっかけは動画編集だった。
「CapCutが楽ですよ」と言われて、動画編集アプリのCapCutを試してみた。でも私は使い続けられなかった。

だったら、自分が迷いにくいものを作ろう。
機能を減らして、操作を減らして、ボタンも減らした。

ところが、人にも使ってもらおうと考えたところから仕事が増えた。
自分では想定していなかった操作まで考える必要が出てきたからだ。

■ ボタンを減らしたのに、仕事が減らない

直す。
チェックする。
また直す。

全体を確認すると、別の不具合が出る。
そこを直すと、別の場所が壊れる。

まさに無限修正である。

「ダメだ。マジで終わる気がしない。」

直接1円にもならない。
でも放置すると、不具合やクレームの元になり得る。
だから手を抜けない。

これが、私がこの仕事を始めたきっかけです。

■ 本体より、本体を成立させる仕事が増えていく

私はこの状態を「シムシティ化」と呼んでいた。
シムシティという街づくりゲームでは、建物だけ置けば終わりではない。街を動かすために、周りのものまで少しずつ増えていく。

プログラムでも似たことが起きた。
本体を作る。
テストがいる。
デバッグ、つまりプログラムの不具合の原因を探して直す作業がいる。
操作を確認する仕事も増える。

ここで私が考えたのは、全部を消すことではなかった。

今いちばん邪魔をしている一工程だけ切る。

■ 全部ではなく、一工程だけ切る

たとえばCSVという、Excelなどで開ける表形式のデータファイルを見る仕事があるとする。

その中から必要な数字を拾う。
別の表へ入れる。
最後の判断だけ人間がする。

ここまでなら、仕事全部をAIへ渡さなくてもいい。

私が先に決めたいのは、何をするかだけではない。
どこで止めるか。
失敗したら、どこで人間に戻すか。

転記はする。でも最終判断はしない。
下書きは作る。でも勝手に送信しない。
集計はする。でも最終確認は人間がする。

この境界を先に決める。

■ AIに仕事を説明できないのも、私は普通だと思う

正式な仕様書を作れなくてもいい。

「毎週これを開く」
「ここを見る」
「これをこっちへ入れる」

まずはそれでいい。

そこから、何が入ってくるのか、何をするのか、何を返すのか、何はやらないのかを整理する。

その整理まで依頼する側に全部やらせたら、意味がないだろ、と私は思う。

■ そこからBridgePatch（ブリッジパッチ）を作った

BridgePatchで最初にやるのは、大きなシステムを売ることではない。
まず無料で、今ある手作業を一工程として切り出せるか確認する。

切り出しに向かない、危険が大きい、範囲が広すぎる。
そう判断したら、そこで止める。

一工程として扱えそうなら、入力、処理、出力、やらないこと、失敗したときの戻し先を整理する。

暫定ツール実装設計書は10,000円（税込）。ここにツール制作そのものは含まない。
必要情報が揃ってから、通常5営業日以内を目安に設計書を納品する。

その内容を見て、実装まで必要なら別途合意する。
一つの処理だけをする簡易ツールは50,000円（税込）を標準とし、対象範囲・総額・納期は開始前に確定する。

何でも自動化するつもりもない。
人命、医療・介護判断、給与・決済の最終確定など、高リスクの業務は原則対象外か個別に確認する。

間違えたとき、人間が止めて戻せるか。
私はそこをかなり重く見る。

■ 今日やることは一個だけ

新しいツールを探す前に、毎週いちばんうっとうしい手作業を一個だけ書いてみてほしい。

何を見て
→ 何をして
→ どこへ残しているか

全部の仕事を説明しなくていい。
一番うっとうしい一工程だけ切る。

「これ、自動化できる？」くらいの状態なら、BridgePatchの無料適合確認から始められます。
https://nobutakayamauchi.github.io/RTS/bridgepatch/
"""


def test_realistic_bridgepatch_article_reaches_human_review_without_deterministic_block():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    result = audit_draft(article(), packet)
    blocks = [item for item in result["findings"] if item.get("severity") == "BLOCK"]
    assert blocks == []
    assert result["status"] == "HUMAN_REVIEW_REQUIRED"
    assert result["human_review_required"] is True
    assert result["publication_state"] == "BLOCKED_PENDING_HUMAN"
    assert result["publication_authority"] == "USER_ONLY"


def test_dogfood_article_preserves_lived_pain_mode_and_single_product_reading():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    assert packet["opening_mode"] == "LIVED_PAIN"
    assert article().count("BridgePatch（ブリッジパッチ）") == 1


def test_dogfood_article_does_not_require_reader_to_decode_seed_terms():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    result = audit_draft(article(), packet)
    unexplained = [
        item["detail"]
        for item in result["findings"]
        if item.get("code") == "UNEXPLAINED_TERM_ON_FIRST_USE"
    ]
    assert "CSV" not in unexplained
    assert "デバッグ" not in unexplained
    assert "CapCut" not in unexplained
    assert "シムシティ" not in unexplained


def test_dogfood_bad_numeric_invention_still_blocks():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    bad = article().replace(
        "直接1円にもならない。",
        "毎週2時間かかっていた。直接1円にもならない。",
        1,
    )
    result = audit_draft(bad, packet)
    assert any(
        item.get("code") == "UNBOUND_NUMERIC_CLAIM" and item.get("detail") == "2時間"
        for item in result["findings"]
    )
    assert result["status"] == "BLOCKED"


def test_dogfood_missing_product_reading_still_blocks():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    bad = article().replace("BridgePatch（ブリッジパッチ）", "BridgePatch", 1)
    result = audit_draft(bad, packet)
    assert any(item.get("code") == "MISSING_PRODUCT_READING_ON_FIRST_USE" for item in result["findings"])
    assert result["status"] == "BLOCKED"


def test_dogfood_second_commercial_action_is_reviewed():
    packet = build_generation_packet(brief(), trusted_source_refs=sources())
    bad = article() + "\n記事が役立ったらフォローしてください。"
    result = audit_draft(bad, packet)
    assert any(item.get("code") == "MULTIPLE_COMMERCIAL_ACTIONS_RISK" for item in result["findings"])

# AIと人間の仕事を「分けて見る」ための超かんたんガイド

## これ、何をやってるの？

AIを使って開発すると、GitHubにはcommitやPRが大量に残ります。

でも、commitが100個あるからといって、人間が100回頑張ったとは限りません。
AIがまとめて作ったのかもしれないし、人間は最初に1回だけ重要な判断をしただけかもしれません。

そこでこの仕組みでは、

**人間が何を決めたか**
→ **AIが何段の仕事を動かしたか**
→ **その仕事がどれくらいの成果を出したか**
→ **いつ人間が戻る必要があったか**

を分けて記録します。

---

## 何を数えるの？

最低限、4つだけ見れば使えます。

### 1. J = 人間の判断

人間がAIに出した「意味のある判断」です。

目安：

- 1点: 小さい修正、続行、承認
- 2点: 設計、方針、構造を決める
- 3点: 中止、凍結、最終承認など大きい判断

### 2. S = AIが動かした仕事の段数

例：

- 実装
- テスト
- 修正
- 再テスト
- デプロイ確認

このような「まとまり」を1段として数えます。

### 3. Y = AI側の見える成果

例：

- commit数
- 変更ファイル数
- テスト件数
- 生成物数
- 処理ジョブ数

重要なのは、**Yは人間の努力ではなく、AI側の出力量**だということです。

### 4. T_return = 人間が戻るまでの時間

AIに仕事を投げてから、

**次に人間の判断が必要になった時刻まで何分か**

を記録します。

---

## どういう計算なの？

### 人間の1判断で、AIを何段動かした？

`Gamma_J = S / J`

例：

人間の判断が2点で、AIが4段動いた場合：

`Gamma_J = 4 / 2 = 2`

→ 人間の判断1点あたり、AIを2段動かした。

### AIの1段で、どれだけ成果が増えた？

`Gamma_M = Y / S`

例：

4段のAI作業から20個の成果が出た場合：

`Gamma_M = 20 / 4 = 5`

→ AIの1段あたり、5個分の成果が出た。

### 人間の1判断が、最終的にどれだけ増幅された？

`Lambda = Y / J`

または

`Lambda = Gamma_J × Gamma_M`

上の例なら：

`Lambda = 20 / 2 = 10`

→ 人間の判断1点が、最終的に10個分の機械出力につながった。

---

## これで何がわかるの？

### 1. 「最近commitが少ない = 働いてない」が間違いか見える

昔は人間が細かく実装していた。
今は人間が設計だけして、AIが巨大な実装をまとめて処理している。

この2つはcommit数だけだと比較できません。

### 2. 自分が今どんな役割をしているか見える

たとえば：

- 実装する人
- 設計する人
- AIを回す人
- AIの結果を壊してチェックする人

へ役割が変わっているかを追えます。

### 3. AIを投げたあと、いつ戻ればいいか予測できる

同じ種類の仕事について `T_return` を貯めると、

「この仕事なら20分後くらいに戻ると良い」

のようなHuman Return ETAを作れます。

### 4. AIの使い方が本当に効率化しているか見える

効率化とは、単にcommitが増えることではありません。

- 人間の判断回数が減った
- AIの1段が大きくなった
- 人間が戻る回数が減った
- テストや検証をAIへ移せた

などを分けて確認できます。

---

## 自分も使うなら、何を記録すればいい？

まずはこれだけでOKです。

| 項目 | 内容 |
|---|---|
| timestamp | いつ起きたか |
| project | どのプロジェクトか |
| human_decision | 人間が何を決めたか |
| J | 判断の重さ 1〜3 |
| stage | AIが何をしたか |
| stage_id | 何段目か |
| output_count | 見える成果の数 |
| human_required_at | 次に人間が必要になった時刻 |
| evidence | 何を根拠にしたか |

GitHub、Chat、CI、エージェントログなどから取れれば十分です。

---

## AIで実装するならどうする？

最小構成なら、次の4つだけ作れば動きます。

### 1. Human Decision Logger

人間の指示を保存します。

保存するもの：

- 時刻
- 指示本文
- Jの点数
- プロジェクト名

### 2. Machine Stage Logger

AI側の作業を「段」に分けて保存します。

例：

- plan
- implement
- test
- repair
- verify

### 3. Binder

人間の判断とAIの仕事を結びます。

ただし、

**時間が近いだけでは結びつけない**

ことが重要です。

最低でも、

- 人間判断より後に起きた
- 内容が一致する
- 対象ファイルや目的が一致する

を確認します。

### 4. Calculator

定期的に以下を計算します。

- `Gamma_J = S / J`
- `Gamma_M = Y / S`
- `Lambda = Y / J`
- `T_return`

これだけで最初のバージョンは作れます。

---

## AIに実装を頼むなら、この指示をそのまま使える

```text
Build a small local-first operator/machine measurement system.

Record human decisions separately from AI output.

For each human decision, store:
- timestamp
- project
- decision text
- decision load J (1, 2, or 3)

For each machine stage, store:
- stage_id
- timestamp
- stage type
- linked human decision id
- visible output count Y

Only bind a machine stage to a human decision when:
1. the stage happened after the human decision,
2. the meaning/scope matches,
3. there is supporting evidence such as files, patch, logs, or task identity.

Calculate:
- Gamma_J = S / J
- Gamma_M = Y / S
- Lambda = Y / J
- human return time

Keep UNKNOWN as UNKNOWN. Do not turn missing data into zero.
Do not treat commit count as human effort.
Export results as JSONL and CSV.
```

---

## これをやると何が狙えるの？

最終的に狙えるのは、

**「AIをどれだけ使ったか」ではなく、「人間とAIがどう仕事を分担しているか」を測ること**です。

さらにデータが貯まれば、

- AIへ投げる最適な仕事サイズ
- 人間が戻るべき時間
- 人間がボトルネックになっている場所
- AIが細かすぎる仕事をしている場所
- 逆に1ステージが巨大化しすぎて危険な場所
- 追加レビューが必要な判断

なども見えるようになります。

---

## 何には使えない？

これは、

- 疲労度
- IQ
- 健康状態
- 頑張り度
- 生産性ランキング

を直接測るものではありません。

**仕事の構造を測るためのもの**です。

---

## 一言でいうと

> 人間がいつ判断し、その判断が何段のAI仕事を起動し、各段がどれだけ成果を出し、いつ人間へ制御が戻ったかを測る。

これがこの仕組みです。

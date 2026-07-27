# Round 0008 — 公開GitHub候補の内部探索・採点

## 現在地

```text
RTS全体                              79%
内部ハードニング                      100%
商品レディネス                        93/100

INTERNAL_PUBLIC_CANDIDATE_SHORTLIST_COMPLETE
HUMAN_RECOMMENDED_CANDIDATE_SELECTION_AND_CONTACT_AUTHORIZATION_REQUIRED
```

この工程は、前工程で許可された内部候補探索・採点だけを実施した。実在人物への連絡、顧客受付、分析、レポート共有、価格提示、契約、納品、公開、リポジトリ書込みは行っていない。

## 観測した候補

| 順位 | 候補 | 公開スコア | 内部判断 |
|---:|---|---:|---|
| 1 | `jbexta/AgentPilot` | 86/100 | 人間選定審査への推奨。未選定・未連絡 |
| 2 | `tmseidel/ai-git-bot` | 83/100 | 予備候補。未選定・未連絡 |
| 3 | `DahnM20/ai-flow` | 72/100 | 80点未満かつ観測マージPR標本が小さいため保留 |

スコアは公開GitHub情報だけを使った接触前評価である。現在のRepo権限、個人開発者としての立場、参加意思、時間、書面同意は証明していない。

## 推奨理由

`jbexta/AgentPilot` は、固定可能な公開コミット、詳細なREADME、12件の観測マージPR標本、コード主体のワークフロー構造、公開プロジェクトチャンネルを持つ。`tmseidel/ai-git-bot` より規模と認証・Webhook面が限定しやすく、最初の1回を公開証拠だけで小さく完結させやすいと判断した。

ただし、これは **推奨** であり **選定** ではない。候補者本人または正当な管理者であることと、任意の書面同意は次の人間ゲートまで保留する。

## 固定した公開証拠

### `jbexta/AgentPilot`

- 固定コミット: `333eb6ce4f193852f4d9fe5412e8636929b6bb4e`
- README blob: `ecf562df63252d4376446cc882d3d5598f668f06`
- 観測マージPR標本: #34, #32, #28, #27, #26, #24, #21, #20, #19, #15, #14, #13

### `tmseidel/ai-git-bot`

- 固定コミット: `498d50b365407e117390bbc79fe41af0fbc2300f`
- README blob: `8f45af916b4f105a39fcd094521b8909e64a90dc`
- 観測マージPR標本: #302, #300, #298, #301, #297, #295, #292, #290, #291, #282, #281, #279

### `DahnM20/ai-flow`

- 固定コミット: `98ebab6ff3f83cc82aeac59c012824b54141ae99`
- README blob: `37a35d6353b057be698c9e9016647910584da8a1`
- 観測マージPR標本: #12, #11

これは各Repoの総PR数を主張するものではなく、この工程で固定した有限の標本である。

## 次の人間ゲート

次の工程では、以下を一組として審査する。

```text
推奨候補を本当に選定するか
↓
Repo権限をどう確認するか
↓
使う連絡経路
↓
最終的に送る個別文面
↓
1回だけの接触許可
```

承認されるまで、宛先、連絡経路、個別文面は空欄のままとする。

## 商品レディネス

商品レディネスは **93/100で据え置く**。候補探索と採点は内部運用能力を強化したが、外部人間の理解、顧客価値、納品受入、価格、商用効果の証拠を作っていない。

## 主な指紋

```text
contract    64ec361b4ea0b866a9d0009c863988bf1e0ba12c455e89b8ea1183a4b4c8c221
universe    db9b5b003b28961a2a720ca856a8fd1793741cb9b8673c155e8c72c7c3baeb13
evidence    00e80125a48912404978afc42403d9a5c2b0137c1cf2ac3217a92fef74bcdd6c
scores      487ab0f2c34d8321c228e0b9f80b8a3001f382180ef08f52de26686c3ab23f81
decision    3a9080bd457a3b795584b70baa94e18a1b6cc71b336b1db2bf1de50a493f52b5
risk        8e8db09c3e5a89a63d126524d00d20f5819bbd21396356f7253230149934b179
score hold  e35ba651d43ec7823cba5bc736915594f230255f18fb577e6acaf5c870637ad0
completion  4bc4c3cb4bcf121e21887c150363035074680ebdd356d4640d412ab01790a853
position    963cdcbff1c70c3c432135021fd67f0386e417571a2aaff7c9ec74d04a09042d
checkpoint  42212a185a492ebc92c15a9fd90abc4e22fea0c90cae794560ef275365400861
```

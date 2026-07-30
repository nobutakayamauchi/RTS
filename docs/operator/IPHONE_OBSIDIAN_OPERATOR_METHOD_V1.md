# iPhone-Only Obsidian Operator Method v1

## 1. 目的

この方法は、RTSを高性能化するための新しい実行エンジンではない。

目的は、iPhoneだけで次の5つを継続できるようにすることにある。

1. 雑な思考を失わず捕捉する。
2. 公開可能な要約へ縮める。
3. 人間確認後にGitHub Issueへ提出する。
4. RTS / FREEZER側でガバナンス判断を行う。
5. 長大なチャットに依存せず、現在地から再開する。

RTSの正本はGitHubに置く。Obsidianは人間側の頭・資材庫・作業台として使う。

```text
Obsidian = private working memory / capture / staging
GitHub    = governed system of record
RTS       = governance / evidence / bounded execution
```

## 2. v1の非対称ブリッジ

### 入力方向

```text
Obsidianの私的メモ
→ 公開可能要約へ変換
→ iOSショートカット
→ GitHub Issue作成画面
→ 人間が内容を確認
→ 人間が送信
→ RTS側でFREEZER候補として審査
```

### 出力方向

```text
GitHub上の小型ステータスJSON
→ iOSショートカットが読取
→ 人間向けMarkdownへ整形
→ Obsidianの読取専用ダッシュボードへ保存
```

v1は完全同期を目指さない。入力は人間確認付き、出力は読取専用とする。

## 3. v1で使わないもの

以下は別のHuman Gateが開くまで導入しない。

- Obsidian Git
- Working Copy
- GitHub Personal Access Token
- GitHub APIによる自動Issue作成
- VPS
- Headless実行
- バックグラウンド監視
- GitHub ActionsによるObsidian同期
- private noteの自動送信
- IssueからFREEZERへの自動承認
- 外部送信、公開、契約、決済、provider実行

## 4. Vault最小構成

```text
System/
└── RTS_Bridge/
    ├── 00_Inbox/
    ├── 10_Staging/
    ├── 20_Submitted/
    ├── 80_Generated_ReadOnly/
    ├── 90_Templates/
    └── 99_Quarantine/
```

### 00_Inbox

思いつき、音声入力、会話断片、未整理メモを置く。秘密情報や個人情報を含む可能性があるため、このフォルダから直接GitHubへ出さない。

### 10_Staging

GitHubへ提出できるように、公開可能な要約へ変換したメモを置く。

### 20_Submitted

人間がGitHub Issueを送信した後、Issue URL、提出日、対象Repo、要約を記録する。

### 80_Generated_ReadOnly

`RTS_MOBILE_STATUS.json`から生成した現在地ダッシュボードを置く。人間が手で追記しない。追記したい内容は`00_Inbox`へ戻す。

### 90_Templates

Capture、Staging、Submitted用のローカルテンプレートを置く。

### 99_Quarantine

公開可否、権利、秘密、個人情報、契約情報、医療・労務・法務情報の扱いに迷う素材を隔離する。このフォルダの内容はGitHubへ提出しない。

## 5. 運用メソッド

```text
CAPTURE → DISTILL → SUBMIT → GOVERN → RESUME
```

### CAPTURE

判断せず、まず`00_Inbox`へ残す。

最低限の形式:

```markdown
# 仮タイトル

- captured_at: YYYY-MM-DD HH:MM JST
- source: voice / chat / idea / observation

## Raw note

自由記述
```

### DISTILL

`10_Staging`へ複製し、GitHubへ出してよい情報だけで次の形に縮める。

```markdown
# 公開可能タイトル

## 種別
idea / bug / specification / decision / resume

## 対象
repository / module / workflow

## 要約
3〜7行で説明する。

## 欲しい結果
何ができれば完了かを書く。

## 根拠
公開URL、PR、Issue、公開ファイルだけを書く。

## 制約
やってはいけないこと、Human Gate、WIP、権限境界を書く。

## 今回は許可しないこと
外部送信、公開、契約、決済、provider実行、秘密情報利用など。
```

DISTILL時に次を削除または抽象化する。

- API key、token、password、cookie、秘密URL
- 私信本文、メール本文、DM本文、スクリーンショット
- 氏名、住所、電話番号、個人メール、医療・労務・法務の生データ
- 顧客データ、社内資料、未公開コード
- 「全部やって」「適当に公開して」など権限が不明な表現

### SUBMIT

iOSショートカットはGitHubの新規Issue作成画面を開くところまで行う。送信はしない。

基本URL:

```text
https://github.com/nobutakayamauchi/RTS/issues/new?template=obsidian-intake.md
```

ショートカットの推奨手順:

1. 共有シートまたはクリップボードからStaging本文を受け取る。
2. タイトル、種別、対象Repoを人間に確認する。
3. 本文をURLエンコードする。
4. `template`、`title`、`body`のクエリを付けた新規Issue URLを作る。
5. SafariまたはGitHubアプリでURLを開く。
6. 人間がテンプレート、公開範囲、権限境界を再確認する。
7. 人間が`Submit new issue`を押す。

Issue作成はFREEZER承認ではない。実装開始、公開、外部実行、契約、決済、provider利用の許可にもならない。

### GOVERN

RTS側はIssueをそのまま実行指示として扱わない。

最低限、次を確認する。

1. 公開情報だけで構成されているか。
2. 対象Repoと対象範囲が明確か。
3. 完了条件が明確か。
4. 禁止事項とHuman Gateが明確か。
5. 既存FREEZER、WIP、Assessment、Preflightと衝突しないか。
6. 重複Issueや既存タスクがないか。
7. FREEZER候補、保留、却下、単純メモのどれにするか。

FREEZERへの登録、Assessment、Preflight、Build、Completionは既存のRTSガバナンスに従う。

### RESUME

Obsidian側では`docs/status/RTS_MOBILE_STATUS.json`だけを小さな再開点として読む。

ダッシュボードには最低限、次を表示する。

- RTS計画上の現在地
- 現在の正式状態
- 次のHuman Gate
- 次の人間行動
- 期限
- 現在許可されていること
- 現在閉じている権限
- 元状態ファイルとfingerprint

状態JSONが読めない、fingerprintが欠ける、期限を過ぎている、元状態と一致しない場合はfail closedとし、実行や提出を続けない。

## 6. 出力ショートカット

読取元:

```text
https://raw.githubusercontent.com/nobutakayamauchi/RTS/main/docs/status/RTS_MOBILE_STATUS.json
```

推奨手順:

1. `URLの内容を取得`でJSONを読む。
2. JSONを辞書として取得する。
3. `display`、`next_human_action`、`authority`をMarkdownへ整形する。
4. Obsidian URIを使い、次のノートを作成または置換する。

```text
System/RTS_Bridge/80_Generated_ReadOnly/RTS_Status.md
```

Obsidian URI例:

```text
obsidian://new?vault=<VAULT_NAME>&file=System%2FRTS_Bridge%2F80_Generated_ReadOnly%2FRTS_Status&content=<URL_ENCODED_MARKDOWN>&overwrite=true
```

`VAULT_NAME`とMarkdown本文はショートカット側でURLエンコードする。

## 7. 毎日の使い方

### 朝または作業開始時

1. `RTS_Status.md`を更新する。
2. `next_human_action`だけを読む。
3. `blocked`にある操作は行わない。
4. 新しい考えは`00_Inbox`へ入れる。

### 作業中

1. 1メモ1テーマにする。
2. 公開できる内容だけ`10_Staging`へ送る。
3. Issue化する前に、対象・結果・制約を埋める。
4. Issue送信後は`20_Submitted`へURLを残す。

### 作業終了時

1. 送信済みIssueを確認する。
2. 未送信Stagingを残す。
3. 秘密や判断不能素材を`99_Quarantine`へ移す。
4. 次回はチャット履歴ではなく`RTS_Status.md`とIssueから再開する。

## 8. 失敗時の扱い

| 状況 | 動作 |
|---|---|
| GitHubを開けない | Stagingを保持し、後で人間が再送する |
| Issue本文が長すぎる | 要約をIssueに置き、公開ファイルまたは既存PRを参照する |
| 公開可否が不明 | `99_Quarantine`へ移し、送らない |
| Status JSONが古い | 実行せず、GitHubの現在地ファイルを確認する |
| FREEZERと衝突 | Issueを保留し、WIPを増やさない |
| 誤送信 | Issueを閉じても履歴は消えない前提で、秘密を追記せず人間へ上げる |

## 9. v1の完成条件

- iPhoneだけでCaptureからIssue作成画面まで進める。
- 人間が送信前に内容を確認できる。
- private noteが自動送信されない。
- GitHub tokenをiPhoneへ保存しない。
- RTSの現在地を小型JSONから再構成できる。
- Obsidianを失ってもGitHub正本から再開できる。
- 長大チャットを失っても、Status、Issue、PR、FREEZERから再開できる。

## 10. 次のHuman Gate

v1の運用実績を確認するまで、次は実装しない。

- IssueのAPI自動作成
- GitHubからObsidianへの定期同期
- 複数Repoの自動集約
- FREEZER候補の自動生成
- 自動ラベル付与
- private repository対応
- GitHub token利用
- 外部provider接続

次工程へ進む条件は、少なくとも数件の手動運用で、秘密情報流出、重複、誤権限、再開不能が発生しないことを人間が確認することである。

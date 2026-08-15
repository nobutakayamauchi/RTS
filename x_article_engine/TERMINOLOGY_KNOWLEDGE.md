# X Article Engine — General-reader terminology knowledge

## Principle

If the intended reader may not know a word, do not force them to leave the article to understand it.

The first occurrence of an unfamiliar term should contain a short plain-language explanation in the same sentence or immediately after it. The explanation should make the article easier to read, not feel like a dictionary entry.

Default assumption for sales / educational X Articles: the reader is a general non-technical reader unless the brief explicitly says otherwise.

## First-occurrence rule

Good:

- `CSVという、Excelなどで開ける表形式のデータファイル`
- `デバッグ、つまりプログラムの不具合の原因を探して直す作業`
- `CapCutという動画編集アプリ`

Bad:

- `CSVを読み込む`
- `デバッグする`
- `APIで連携する`

when the article has not yet explained those terms.

After the first explanation, the short term may be used normally.

## Do not label the reader

Do not write things such as:

- `非エンジニアには分からないと思いますが`
- `IT音痴でも分かるように`
- `初心者向けに説明すると`

Those labels can make the reader feel ranked or talked down to. Explain the term naturally without classifying the reader.

## Product-name reading

When a product or service name is visually unfamiliar, the first natural introduction should include a katakana reading exactly once.

Example:

`BridgePatch（ブリッジパッチ）`

Later mentions use only:

`BridgePatch`

Do not repeat the reading every time.

## General-reader glossary seed

This is a starting set, not an exhaustive dictionary. Add terms when dogfooding shows that a general reader may stumble.

- `CSV`: a table-shaped data file that can be opened in spreadsheet software such as Excel.
- `デバッグ`: finding the cause of a program problem and fixing it.
- `ログ`: a record of what a program did and when.
- `API`: a mechanism that lets one service or program exchange information with another.
- `リポジトリ`: a place where program files and their change history are stored together.
- `プロンプト`: the instruction or request given to an AI.
- `自動化`: making a repeated manual step run by a program or AI under defined conditions.

## Writing rule

Prefer a tiny appositive explanation over a footnote or glossary section. The reader should learn the word exactly where they encounter it.

The goal is not to eliminate technical words. The goal is to make every necessary word understandable without breaking reading flow.

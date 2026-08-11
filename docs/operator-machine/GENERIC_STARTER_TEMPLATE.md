# Generic Starter Template / 汎用スターターテンプレート

This template is intentionally generic. It does not depend on any specific person's history.

このテンプレートは誰でも使える汎用品です。特定の人の過去データは前提にしません。

---

# 1. Start with one CSV / CSV 1枚から始める

Create a file called `operator_machine_events.csv`.

`operator_machine_events.csv` を1つ作れば始められます。

```csv
timestamp,project,event_type,text,J,stage_id,stage_type,output_count,human_required_at,evidence
2026-01-01T10:00:00+09:00,demo,human_decision,"Add login flow",2,,,,,chat
2026-01-01T10:01:00+09:00,demo,machine_stage,"Implement login UI",,S1,implement,4,,git_patch
2026-01-01T10:05:00+09:00,demo,machine_stage,"Run tests",,S2,test,8,,ci
2026-01-01T10:12:00+09:00,demo,machine_stage,"Fix failed tests",,S3,repair,3,2026-01-01T10:15:00+09:00,ci
```

---

# 2. Meaning of each field / 各項目の意味

| Field | 日本語 | Meaning |
|---|---|---|
| timestamp | 時刻 | when the event happened |
| project | プロジェクト | project or task name |
| event_type | 種類 | `human_decision` or `machine_stage` |
| text | 内容 | what was decided or done |
| J | 判断負荷 | 1, 2, or 3 for human decisions |
| stage_id | AI段ID | unique machine-stage id |
| stage_type | AI作業種別 | plan / implement / test / repair / verify etc. |
| output_count | 出力量 | visible output proxy for that stage |
| human_required_at | 人間が必要になった時刻 | first defensible point where human input was needed |
| evidence | 証拠 | chat / git patch / CI / task id / log etc. |

---

# 3. Simple decision score / 判断の点数

Use only three levels at first.

最初は3段階だけで十分です。

- `J=1`: small local choice / 小さい修正・続行・承認
- `J=2`: architecture, policy, scope / 設計・方針・構造
- `J=3`: freeze, stop, final authority / 凍結・中止・最終判断

Do not over-optimize the scoring system before collecting data.

最初から点数設計を細かくしすぎないでください。

---

# 4. Binding rule / 人間判断とAI作業の結び方

A machine stage can be linked to a human decision only when all of these are true:

AI作業を人間判断に結びつけるのは、最低でも次を満たすときだけです。

1. The machine stage happened **after** the human decision.  
   AI作業が人間判断より**後**に起きている。

2. The meaning and scope match.  
   内容と対象範囲が一致している。

3. There is supporting evidence.  
   ファイル、patch、CI、task id、logなどの裏付けがある。

If any of these are unclear, use `UNKNOWN` instead of guessing.

怪しい場合は推測せず `UNKNOWN` にします。

---

# 5. Minimum calculations / 最小計算

For one analysis window `W`:

ある期間 `W` について：

```text
J = total human decision load
S = number of trusted linked machine stages
Y = visible machine output proxy
```

Then calculate:

```text
Gamma_J = S / J
Gamma_M = Y / S
Lambda  = Y / J
```

Because:

```text
Lambda = Gamma_J × Gamma_M
```

Interpretation:

- `Gamma_J`: how many machine stages were activated per unit of human decision load
- `Gamma_M`: how much visible output came from one machine stage
- `Lambda`: total visible machine output per unit of human decision load

日本語：

- `Gamma_J`: 人間の判断1単位でAIを何段動かしたか
- `Gamma_M`: AIの1段からどれだけ出力が出たか
- `Lambda`: 人間の判断1単位が最終的にどれだけ機械出力へつながったか

---

# 6. Human Return ETA / 人間が戻る時間

For every launched task, record two timestamps separately:

AIに投げた仕事ごとに、次の2つを分けて記録します。

```text
human_required_at       = when human input first became necessary
observed_human_return_at = when the human actually returned
```

Do not train on the second one if the goal is to predict when the human **should** return.

「いつ戻るべきか」を予測したいなら、実際に戻った時刻ではなく `human_required_at` を教師データにします。

A simple first estimator is:

```text
Return ETA = P80(previous required-return times for the same task class)
```

Example:

```text
previous required-return times = 8, 10, 12, 15, 20 minutes
P80 ≈ around the upper end of the normal range
```

This intentionally favors coming back slightly late rather than checking constantly.

---

# 7. Suggested output / 出力例

For each week or project, print something like:

```text
Project: demo
Window: 2026-W01
Human decisions J: 7
Machine stages S: 10
Visible output Y: 48
Gamma_J: 1.43
Gamma_M: 4.80
Lambda: 6.86
Median required return: 12 min
P80 required return: 18 min
Evidence quality: MEDIUM
```

---

# 8. Optional human-load shape / 任意：人間側の負荷形状

If you want more detail later, add:

```text
E = direct human execution
J = decisions
O = orchestration / supervision
R = repair / redesign
X = context switches
```

Keep the vector:

```text
L = (E, J, O, R, X)
```

Do not force everything into one score unless you only need a display number.

詳しく見る場合でも、基本は1点に潰さず `L=(E,J,O,R,X)` の形で保持します。

---

# 9. Things you should NOT infer / 推測してはいけないこと

Do not infer these directly from GitHub activity:

GitHubの活動量から次を直接推測しないでください。

- fatigue / 疲労
- intelligence / 知能
- health / 健康状態
- motivation / やる気
- human effort from commit count / commit数＝人間の努力量

A long gap may mean sleep, waiting for CI, another project, API limits, a conversation, or nothing observable.

長い空白時間には様々な理由があります。空白だけで人間状態を断定しません。

---

# 10. Copy-paste implementation prompt / そのまま使える実装指示

```text
Create a local-first human/AI work measurement tool.

Input:
- CSV or JSONL event log
- optional Git timestamps
- optional chat timestamps
- optional CI/task-runner logs

Required behavior:
1. Separate HUMAN events from MACHINE events.
2. Score human decisions J as 1/2/3.
3. Group machine work into meaningful stages S.
4. Keep machine-visible output Y separate from human effort.
5. Bind a machine stage to a human decision only when temporal order, semantic scope, and evidence all support the link.
6. Otherwise label the binding UNKNOWN.
7. Calculate Gamma_J=S/J, Gamma_M=Y/S, Lambda=Y/J.
8. Record human_required_at separately from observed_human_return_at.
9. Estimate return ETA from previous human_required_at samples by task class, starting with P80.
10. Never convert missing evidence into semantic zero.
11. Export weekly/project summaries as CSV and Markdown.
12. Include a validation report listing rejected bindings and why they were rejected.

Keep the first implementation small. No daemon, database, or ML model is required.
```

---

# /goal

A useful first implementation is complete when it can answer these four questions:

最初の完成条件は、この4問に答えられることです。

1. **What did the human decide? / 人間は何を決めた？**
2. **What machine work did that decision actually trigger? / その判断でAIは何を動かした？**
3. **How much output did those stages produce? / そのAI作業はどれだけ出力した？**
4. **When did the human need to return? / いつ人間が戻る必要があった？**

If your system can answer those with evidence and can say `UNKNOWN` when it cannot, you have a valid starter version.

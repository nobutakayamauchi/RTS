# A Very Simple Guide to Measuring Human + AI Work

## What is this actually doing?

When you build with AI, GitHub may show lots of commits and pull requests.

But 100 commits do **not** mean a human did 100 units of work.
The AI may have created most of them after one important human decision.

This system separates the flow into four simple questions:

**What did the human decide?**
→ **How many machine stages did that decision trigger?**
→ **How much visible output did those stages produce?**
→ **When did the human need to come back?**

---

## What do we measure?

You only need four things to get started.

### 1. J = human decision load

This is the weight of a meaningful human decision.

Simple scoring:

- 1 = small local choice, approval, continue
- 2 = architecture, policy, scope, structural choice
- 3 = freeze, stop, final authority, irreversible choice

### 2. S = machine stages

A stage is one meaningful chunk of AI work.

Examples:

- implement
- test
- repair
- retest
- verify

### 3. Y = visible machine output

Examples:

- commits
- changed files
- completed tests
- generated artifacts
- processed jobs

Important: **Y is machine-visible output, not human effort.**

### 4. T_return = human return time

This is the time between launching AI work and the next moment when a human decision is actually needed.

---

## What are the calculations?

### How many machine stages did one unit of human decision start?

`Gamma_J = S / J`

Example:

Human decision load = 2
Machine stages = 4

`Gamma_J = 4 / 2 = 2`

So one unit of human decision load started two machine stages.

### How much output came from one machine stage?

`Gamma_M = Y / S`

Example:

4 machine stages produce 20 visible outputs.

`Gamma_M = 20 / 4 = 5`

So one machine stage produced five units of visible output.

### How much total machine output came from one unit of human decision?

`Lambda = Y / J`

or

`Lambda = Gamma_J × Gamma_M`

Using the same example:

`Lambda = 20 / 2 = 10`

So one unit of human decision load was associated with ten units of visible machine output.

---

## What can this tell me?

### 1. It shows why “fewer commits = less work” can be misleading

Earlier, the human may have done many small implementation steps.
Later, the human may make one architectural decision and let AI execute a much larger bundle.

Commit count alone cannot distinguish those situations.

### 2. It shows how your role is changing

You may move from:

- implementing
- to designing
- to orchestrating agents
- to reviewing and attacking AI output

The system helps make that shift visible.

### 3. It can estimate when you should return

If you collect enough `T_return` samples for the same class of work, you can estimate:

“Come back in about 20 minutes.”

That becomes a Human Return ETA.

### 4. It shows whether AI is actually changing the work structure

Useful signs include:

- fewer human decisions for the same result
- larger machine stages
- fewer unnecessary human returns
- more testing or verification moved to AI

---

## What should I log if I want to use it myself?

Start with this:

| Field | Meaning |
|---|---|
| timestamp | when it happened |
| project | project name |
| human_decision | what the human decided |
| J | decision load, 1 to 3 |
| stage | what the AI did |
| stage_id | machine stage identifier |
| output_count | visible output count |
| human_required_at | when a human was next required |
| evidence | why the link is trusted |

You can collect these from GitHub, chat logs, CI, agent logs, or your own task runner.

---

## How do I implement this with AI?

A minimal version only needs four pieces.

### 1. Human Decision Logger

Store:

- timestamp
- decision text
- decision load J
- project

### 2. Machine Stage Logger

Store machine work as stages such as:

- plan
- implement
- test
- repair
- verify

### 3. Binder

Link a machine stage to a human decision.

Do **not** link them just because the timestamps are close.

At minimum check:

- the machine stage happened after the human decision
- the meaning and scope match
- supporting evidence exists, such as files, patch content, logs, or task identity

### 4. Calculator

Calculate:

- `Gamma_J = S / J`
- `Gamma_M = Y / S`
- `Lambda = Y / J`
- `T_return`

That is enough for a first version.

---

## Prompt you can give directly to an AI coding agent

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

## What can I eventually aim for?

The goal is not to measure “how much AI you used.”

The goal is to measure **how work is divided between the human and the machine**.

With enough data, you can start to see:

- the best task size to delegate to AI
- when a human should return
- where the human is the bottleneck
- where machine stages are too small
- where one machine stage has become dangerously large
- which decisions deserve an extra review

---

## What should this NOT be used for?

It does not directly measure:

- fatigue
- intelligence
- health
- “how hard someone worked”
- worker rankings

It measures the **structure of human-machine work**.

---

## One-sentence version

> Measure when the human decides, how many machine stages that decision starts, how much output each stage produces, and when control needs to return to the human.

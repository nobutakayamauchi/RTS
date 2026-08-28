# Codex Reasoning Density Benchmark v1

Purpose: measure whether RTS externalized knowledge and selective restart context reduce Codex re-reading/reasoning cost without reducing correctness.

This is an **experiment**, not a production authority change. It does not mutate FREEZER, Canon, runtime policy, or completed K0/K1/K2/FRZ-000024 state.

## Phase 0 — Historical baseline first

Before running any new Codex benchmark, inventory the existing SSH-side Codex history:

```bash
bash experiments/codex_reasoning_density_v1/collect_history.sh
```

The collector is read-only. By default it:

- scans `~/.codex/sessions/**/*.jsonl`;
- inventories non-secret files under `~/.codex`;
- looks for benchmark surfaces such as `.benchmark-results`, `EXP-*`, and `WISH-KILL` under known repo roots;
- extracts session/model/cwd/provider and usage counters when present;
- hashes the first task text instead of copying prompt/response text;
- excludes `auth.json`, config/credential/secret files;
- labels `turn.completed` usage aggregation `HIGH` confidence;
- treats generic usage snapshots as potentially cumulative and keeps only the final snapshot with `LOW` confidence rather than blindly summing them.

Outputs:

```text
results/history-<UTC timestamp>/historical_baseline.json
results/history-<UTC timestamp>/historical_baseline.csv
results/history-<UTC timestamp>/summary.json
```

Do not merge `LOW` or `NONE` confidence usage into a headline token-reduction claim until its meter semantics are resolved.

## Three fresh runs

All three runs use fresh `codex exec --ephemeral --json` invocations. We deliberately do **not** use `codex exec resume`, because this benchmark is intended to measure RTS external reuse rather than session-history replay cost.

1. `cold` — Codex receives no restart packet and must discover the smallest relevant repo surface itself.
2. `reuse` — Codex receives `reuse_packet.md` as a routing aid, verifies only freshness-critical pointers, and answers the same question.
3. `next` — Codex receives the same bounded reuse packet and performs the next related read-only reasoning task without re-deriving completed K0-K2 history.

## What is measured

From the `turn.completed.usage` event emitted by `codex exec --json`:

- `input_tokens`
- `cached_input_tokens`
- `cache_write_input_tokens` when present
- `output_tokens`
- `reasoning_output_tokens`

The harness also records wall time and counts command/file-change/tool-call events visible in the JSONL.

Derived metrics:

- uncached input = `input_tokens - cached_input_tokens`
- cached input ratio = `cached_input_tokens / input_tokens`
- cold -> reuse input reduction
- cold -> reuse uncached-input reduction
- next-run cost relative to cold

`REFERENCE_TOKENS` defaults to `5000000` only because that is the current external reference supplied for this experiment. It is reported as a **reference ratio only**. It must not be mixed with provider-reported `codex exec` usage or treated as the same meter unless provenance is later established.

## Run

Prerequisites:

- run from a checkout of this branch (or a descendant containing this harness);
- `codex` CLI installed;
- Codex already authenticated in the local environment;
- Python 3.

First collect history, inspect the baseline, then run the new benchmark:

```bash
bash experiments/codex_reasoning_density_v1/collect_history.sh
bash experiments/codex_reasoning_density_v1/run.sh
```

Optional fixed model:

```bash
CODEX_BENCH_MODEL='<model-id>' bash experiments/codex_reasoning_density_v1/run.sh
```

Optional external reference:

```bash
REFERENCE_TOKENS=5000000 bash experiments/codex_reasoning_density_v1/run.sh
```

Outputs are written under `experiments/codex_reasoning_density_v1/results/` and are intentionally gitignored.

## Interpretation rule

A lower token count is not a win by itself. A run counts as useful only when the answer still identifies the same verified lifecycle state, bounded adequacy meaning, residual-risk boundary, and safe next action.

The benchmark therefore separates:

`token reduction` from `decision quality`.

The target is not minimum reasoning. The target is **maximum useful reasoning density**: spend deep reasoning on UNKNOWN, not on rediscovering KNOWN.

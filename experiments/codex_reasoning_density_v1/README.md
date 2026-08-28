# Codex Reasoning Density Benchmark v1

Purpose: measure whether RTS externalized knowledge and selective restart context reduce Codex re-reading/reasoning cost without reducing correctness.

This is an **experiment**, not a production authority change. It does not mutate FREEZER, Canon, runtime policy, or completed K0/K1/K2/FRZ-000024 state.

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

```bash
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

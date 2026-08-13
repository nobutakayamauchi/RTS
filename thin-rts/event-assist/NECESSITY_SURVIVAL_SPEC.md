# Event Assist — Necessity Survival Specification

Timestamp: **2026-08-11 20:20 JST**

Status: `GATE_1_EXECUTED / GLUE_SURVIVES / GATE_2_REQUIRED`

Purpose: kill the need before authorizing a concrete implementation.

This is the first of two survival specifications for Event Assist.
It answers only:

> Does each required outcome genuinely need to exist, and if so what irreducible responsibility survives?

It does NOT decide the final implementation shape.

## Inputs

- `FEATURE_SPEC.md` outcome contract;
- Prototype A — external-first composition hypothesis;
- Prototype B — minimal-new-build hypothesis;
- frozen cases M/B and common preservation workload;
- current external tool/service/OS/API/OSS capabilities;
- operator burden, privacy, security, maintenance and cost evidence.

## Gate 1 — Raison d’être Destroy Loop

For every responsibility row:

1. eliminate or simplify the desired outcome;
2. test whether an existing product/OS/SaaS/official portal/API/OSS/CLI/model already solves it;
3. test composition of existing capabilities;
4. test whether a bounded manual step is safer/cheaper;
5. account for integration, provider, auth, privacy, maintenance and failure burden;
6. identify the exact remainder, if any;
7. attack the remainder with DA / Counter-DA and the frozen workload;
8. keep only what cannot be killed under current evidence.

## Allowed row verdicts

- `DROP`
- `EXTERNALIZE`
- `MANUAL_BOUNDED`
- `GLUE_REQUIRED`
- `IRREDUCIBLE_BUILD_REQUIRED`
- `EVIDENCE_INSUFFICIENT`

## Required output

A `SURVIVING_RESPONSIBILITY_MAP` with one row per responsibility:

`RESPONSIBILITY → NEEDED_OUTCOME → A_RESULT → B_RESULT → DESTROY_RESULT → SURVIVING_MINIMUM → EVIDENCE`

No implementation may enter Gate 2 unless its responsibility row survives Gate 1.

## Kill rule

`USEFUL != NECESSARY`

`ALREADY_BUILT != NECESSARY`

`EXTERNAL_EXISTS != EXTERNAL_WINS`

`NECESSITY_SURVIVES != CUSTOM_BUILD_AUTHORIZED`

Gate 1 is complete only when rotated attacks stop producing materially new necessity objections:

`SEARCH_SATURATED_UNDER_CURRENT_EVIDENCE`

## Gate 1 verdict — 2026-08-13

Executed under the 新RTS（仮称） core-completion `/goal` audit.

Result:

`MONOLITHIC_EVENT_ASSIST = KILLED`

`IRREDUCIBLE_CUSTOM_PLATFORM = NOT_JUSTIFIED`

`BOUNDED_EVENT_STATE_GLUE = SURVIVES`

The surviving minimum is limited to cross-boundary EventCase / Evidence Gap / Action Pin / authority / watch-health bindings and handoff references to already-adopted safety, custody and recovery contracts. Retrieval, current-source lookup, calendar/reminders, storage, crypto, document rendering, provider adapters and external actions remain external or replaceable occupants.

Canonical result record:

`NECESSITY_GATE_RESULT_2026-08-13.md`

Gate 1 is therefore complete for the current evidence, but Event Assist is **not** product-complete. The surviving thin responsibility must still survive Gate 2 METEOR and a material real-situation pilot.

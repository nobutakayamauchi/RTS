# FRZ-000019 — Official Docs Intake + Claim Extraction Adapter v1

## Task

Build the missing upstream adapter for H (`RTS-FRZ-000018`): bounded provider-official documentation discovery/fetch, immutable provenance capture, deterministic visible-text normalization, conservative exact-anchor contract claim extraction, coverage audit, and H-compatible Evidence Bundle emission.

## Scope

- Built-in provider policies for OpenAI, Anthropic and Google.
- HTTPS-only, allowlisted-host fetch with redirect revalidation.
- Bounded index/seed discovery; this is not a general crawler.
- Deterministic HTML/text normalization without JavaScript execution.
- Exact-anchor lexical claim candidates for H contract areas.
- Coverage/audit output that surfaces ambiguous contract-like chunks and partial failures.
- Validate every emitted bundle with `model_transition_intelligence.validate_bundle`.
- No model API calls, credentials, runtime routing mutation, profile application or promotion.

## Hard invariants

`FETCHED DOC != OBSERVED MODEL BEHAVIOR`

`EXTRACTED CLAIM != VERIFIED BEHAVIOR`

`OFFICIAL TRUST = PROVIDER POLICY + ALLOWLISTED FINAL HOST`

`UNKNOWN/AMBIGUOUS TEXT != SILENTLY IGNORED`

`INTAKE != EXECUTION AUTHORITY`

## DA death conditions

- An allowlisted starting URL redirects to an untrusted host and is still accepted.
- A contract-like sentence not covered by a rule disappears without an audit finding.
- A synthesized/paraphrased anchor not present in normalized source text enters H.
- Partial fetch failure still yields `READY_FOR_H`.
- Discovery exceeds configured document/link/byte bounds.
- Script/style/navigation noise is treated as product contract text.
- A documentation statement is emitted as observed behavior or hidden architecture proof.

## Completion

A-I focused regressions and FREEZER verification pass, FRZ-000019 reaches COMPLETED, WIP is clear, one-shot workflows are removed, and a cleaned completed-head persistent CI run is green.

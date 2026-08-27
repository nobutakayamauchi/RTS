# Semantic Claim Refinement v1

`semantic_claim_refinement` is a conservative postprocessor for `official_docs_intake` reports.

It exists to reduce manual review only when an ambiguous exact source sentence maps uniquely onto a controlled semantic alias rule. It is **not** a freeform summarizer and it does not turn documentation into observed behavior.

## Hard boundaries

- source text is immutable;
- every added claim keeps the exact source sentence as `anchor`;
- added claims remain `behavior_status=UNVERIFIED`;
- only H-supported contract areas/kinds are emitted;
- unmatched text remains reviewable;
- negated/exception language must fail closed before completion;
- multiple semantic matches must remain reviewable before completion;
- upstream `ambiguous_findings_truncated=true` can never become `READY_FOR_H`;
- refined bundles are revalidated through H `validate_bundle`;
- execution/profile-application/promotion authority remains `NONE`;
- hidden architecture claim remains `NONE`.

## v1 method

The v1 registry is intentionally small. It recognizes recurring provider wording around parallel tool/function calls, background execution, state persistence, automatic tool selection, coordinated agents, schema conformance, isolated execution environments and concurrent request limits.

The semantic value is normalized, while the original exact sentence remains attached as evidence. Review-count reduction is telemetry, not correctness evidence.

A future model-assisted proposer may sit upstream of this verifier, but freeform model output must not bypass these boundaries.

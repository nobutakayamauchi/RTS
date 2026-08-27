# RTS-FRZ-000020 — Semantic Claim Refinement + Review Reduction v1

## Goal

Reduce I's `REVIEW_REQUIRED` surface only where an exact official-document sentence maps uniquely onto a controlled semantic alias ontology.

## Invariants

- source anchor stays exact and immutable;
- docs claims remain `UNVERIFIED`;
- no hidden architecture claim;
- no freeform semantic paraphrase becomes authoritative;
- negated/exception statements do not become positive capability claims;
- multiple ontology matches remain reviewable;
- unmatched text remains reviewable;
- upstream truncated ambiguity cannot become fully covered;
- refined bundle must pass H `validate_bundle`;
- execution/profile-application/promotion authority remains `NONE`.

## Ultimate Loop death conditions

1. `does not support parallel tool calls` is auto-classified as positive parallel-tool support.
2. one source sentence matches two semantic ontology rules and both are silently accepted.
3. `ambiguous_findings_truncated=true` is ignored and output becomes ready.
4. an added claim anchor differs from the exact source sentence.
5. review count falls while unresolved high-risk contract text disappears from the audit.

## Completion

J survivor passes destructive DA + Counter-DA, I/H/G/F/E/D/C/B/A regression, FREEZER verify, and a bounded live official-doc review-reduction smoke without turning unresolved provider wording into certainty.

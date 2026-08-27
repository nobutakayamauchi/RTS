# RTS-FRZ-000011 — Selective Recall + Memory Lifecycle v1

## Status

```text
GOVERNED_IMPLEMENTATION_CANDIDATE
ONE_CHILD_ONLY
NO_PARALLEL_CHILD_WORK
NO_EXECUTION_AUTHORITY_FROM_RECALL
NO_PROMOTION_AUTHORITY_FROM_RECALL
```

## Human build direction

The operator explicitly instructed on 2026-08-27 to implement the adaptive-intelligence parts one by one, carefully. This task interprets that instruction as build authorization **only after** the existing FREEZER Build Assessment returns `BUILD_NOW` and the Implementation Preflight returns `PASS` for this exact child.

If either gate does not pass, do not select or start this item.

## Scope

Implement the smallest read-only semantic layer above the existing RTS memory index.

RTS already owns raw memory sources and a searchable index:

- `logs/`
- `incidents/`
- `memory/index.json`
- `rts_kernel/indexing/memory_index_engine.py`

This child must **not** create a second memory database, vector store, crawler, daemon, provider integration, model runtime, or autonomous promotion engine.

The missing responsibility is narrower:

> Decide whether prior memory should be recalled for the current event, select only the smallest decision-relevant anchors, and fail closed when a record is stale, superseded, quarantined, malformed, or outside scope.

## Canonical ownership

### Existing owners retained

- raw historical bodies: existing repository files under `logs/`, `incidents/`, and other existing evidence locations;
- lexical/search index: `rts_kernel/indexing/memory_index_engine.py` and `memory/index.json`;
- execution authority: existing RTS execution / human gates;
- promotion authority: existing Outcome Learning, Skill Regression, Human Review Ledger, and Promotion Application Preview;
- evidence and provenance: existing repository fingerprints / source references.

### New bounded owner

Create one thin package:

```text
selective_recall/
```

It may own only:

- memory-lifecycle metadata validation;
- deterministic recall routing;
- freshness / supersession / quarantine checks;
- smallest-anchor selection;
- non-authorizing recall output;
- read-only lifecycle-transition validation.

Lifecycle metadata should live as a sidecar under the existing `memory/` ownership surface rather than duplicating raw bodies.

## Lifecycle vocabulary

Exact v1 states:

```text
RAW
ACTIVE_CANDIDATE
VERIFICATION_PENDING
REPEATED
PROMOTION_READY
CANONICAL
FOLDED
SUPERSEDED
ARCHIVED
QUARANTINED
```

Storage never implies activation. Retrieval never implies correctness, decision competence, execution authority, or promotion authority.

## Default recall eligibility

Default eligible states:

```text
ACTIVE_CANDIDATE
VERIFICATION_PENDING
REPEATED
PROMOTION_READY
CANONICAL
```

Default excluded states:

```text
RAW
FOLDED
SUPERSEDED
ARCHIVED
QUARANTINED
```

An explicit research-mode caller may inspect excluded historical metadata later, but v1 normal routing does not return it as an active anchor.

## Freshness contract

Every sidecar record must bind to the exact current source bytes using a deterministic source identity.

For repository-local source files, v1 may use the Git blob identity algorithm without invoking Git or a subprocess:

```text
SHA1("blob " + byte_length + NUL + file_bytes)
```

A mismatch means `STALE` and the record is not recall-eligible.

This identity is a freshness/version binding, not a security claim.

## Sidecar record minimum

Each record must include at least:

```text
memory_id
source_path
source_git_blob_sha
lifecycle_state
event_triggers
scope_tags
as_of
superseded_by
evidence_refs
```

Rules:

- paths must remain inside the repository;
- duplicate `memory_id` values fail closed;
- source files must exist;
- empty provenance is invalid;
- `superseded_by != null` excludes default active recall;
- `QUARANTINED` excludes default active recall;
- stale source identity excludes default active recall.

## Initial seed records

Use only bounded historical context-loss incidents already committed to RTS as the first deterministic examples:

- `incidents/INC_20260222_1545_Cursor_ContextLoss.md`
- `incidents/INC_20260222_1603_ClaudeCode_ContextLoss.md`

Both begin as `ACTIVE_CANDIDATE`, not `REPEATED` or `CANONICAL`.

The seed proves routing mechanics only. It does not prove that the historical root-cause language is universally correct.

## Recall request v1

Minimum request fields:

```text
event
scope_tags
current_context_sufficient
explicit_recall
max_results
```

## No-recall fast path

If current context is sufficient and no explicit recall is requested, the router returns `NO_RECALL` without searching the full history.

Insufficient routing signal must not be guessed into relevance. Return a bounded no-recall/unknown reason.

## Selection rule

When recall is justified:

1. validate registry and sources;
2. filter lifecycle-ineligible records;
3. filter stale/superseded/quarantined records;
4. require event trigger overlap;
5. require scope overlap when scope tags are supplied;
6. rank deterministically;
7. return at most `max_results` **anchors only**.

An anchor contains metadata and source path; it does not inline the full historical body.

## Output authority boundary

Every recall result must state:

```text
execution_authority: NONE
promotion_authority: NONE
```

`CANONICAL` is a memory lifecycle status, not an execution permission.

Existing Ultimate Loop invariants remain controlling:

```text
HISTORICAL EVIDENCE != CURRENT AUTHORITY
RETRIEVAL != DECISION COMPETENCE
ROUTING != AUTHORIZATION
```

## Lifecycle transition validator

v1 validates proposed transitions but does not mutate records automatically.

Allowed transitions:

```text
RAW -> ACTIVE_CANDIDATE | QUARANTINED | ARCHIVED
ACTIVE_CANDIDATE -> VERIFICATION_PENDING | QUARANTINED | ARCHIVED
VERIFICATION_PENDING -> REPEATED | ACTIVE_CANDIDATE | QUARANTINED | ARCHIVED
REPEATED -> PROMOTION_READY | ACTIVE_CANDIDATE | QUARANTINED | ARCHIVED
PROMOTION_READY -> CANONICAL | REPEATED | QUARANTINED | ARCHIVED
CANONICAL -> FOLDED | SUPERSEDED | QUARANTINED
FOLDED -> SUPERSEDED | ARCHIVED
SUPERSEDED -> ARCHIVED
QUARANTINED -> RAW | ARCHIVED
ARCHIVED -> no transition
```

Direct `RAW -> CANONICAL` must fail closed.

A valid transition still grants no authority to apply it.

## Required tests

At minimum:

1. no-recall fast path;
2. deterministic event/scope recall;
3. smallest-anchor-only output;
4. max-results enforcement;
5. stale source identity rejection;
6. superseded record rejection;
7. quarantined record rejection;
8. malformed / duplicate / path-escape registry rejection;
9. insufficient signal remains bounded and does not guess;
10. every output carries `execution_authority=NONE` and `promotion_authority=NONE`;
11. lifecycle state validation fails closed;
12. direct `RAW -> CANONICAL` rejected;
13. allowed staged transition accepted as validation only;
14. no network, subprocess, deploy, publish, payment, provider, or adjacent-repository action path;
15. existing `memory/index.json` search behavior remains untouched;
16. source incident bytes remain unchanged after routing;
17. FREEZER verification remains green;
18. children B-E remain `FROZEN / NOT_APPROVED`;
19. WIP contains only `RTS-FRZ-000011` while implementation is active.

## Rollback boundary

Rollback removes only:

- the new `selective_recall/` package;
- its sidecar registry / examples;
- its tests and task documentation;
- Child A lifecycle revisions created for this implementation.

Raw memory source files, existing Memory Index behavior, Outcome Evidence, Skill promotion governance, and other children remain unchanged.

## Stop conditions

Stop and do not widen scope if:

- Build Assessment is not `BUILD_NOW`;
- Preflight is not `PASS`;
- another FREEZER item is already `IN_PROGRESS`;
- implementation requires rewriting raw memory bodies;
- routing would grant execution or promotion authority;
- freshness cannot be proven deterministically;
- a second persistent memory store becomes necessary;
- Child B, C, D, or E would need implementation to make Child A work.

## Completion condition

Child A is complete only when its bounded implementation and tests are green, the non-authority boundary is proven, FREEZER invariants remain valid, and the result is reviewable without starting any other adaptive-intelligence child.

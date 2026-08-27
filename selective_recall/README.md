# Selective Recall + Memory Lifecycle v1

`selective_recall` is a thin, deterministic, repository-local semantic layer above RTS's existing memory sources and Memory Index.

It does **not** create a second memory database and does not copy raw historical bodies into recall output.

## Purpose

The package answers only three bounded questions:

1. Is recall needed for this event?
2. Which smallest current memory anchor(s) are relevant?
3. Is a proposed lifecycle transition structurally allowed?

It never answers "may this action execute?" or "may this memory be promoted?".

Every recall output carries:

```text
execution_authority: NONE
promotion_authority: NONE
```

## Existing ownership retained

Raw bodies remain in existing RTS locations such as `logs/` and `incidents/`.

The existing lexical/searchable Memory Index remains owned by:

```text
rts_kernel/indexing/memory_index_engine.py
memory/index.json
```

The new `memory/recall_registry.json` stores metadata and exact source identities only.

## No-recall fast path

If the current context is sufficient and the caller did not explicitly request recall, the router returns `NO_RECALL` before loading the registry.

This prevents a small/local task from paying a history-retrieval cost merely to discover that no history is needed.

## Lifecycle states

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

Default active recall accepts only:

```text
ACTIVE_CANDIDATE
VERIFICATION_PENDING
REPEATED
PROMOTION_READY
CANONICAL
```

Stale, superseded, quarantined, archived, folded, and raw records are not returned as default active anchors.

`CANONICAL` is a memory lifecycle label only. It is not execution or promotion permission.

## Freshness

Each record binds to the exact current source bytes with Git blob identity:

```text
SHA1("blob " + byte_length + NUL + file_bytes)
```

This is a deterministic freshness/version identity, not a security claim.

A stale record is excluded from recall. `verify` fails closed while a committed registry contains stale sources.

## Recall request

Example:

```json
{
  "event": "reasoning_continuity_loss",
  "scope_tags": ["context", "reconstruction", "claude-code"],
  "current_context_sufficient": false,
  "explicit_recall": false,
  "max_results": 1
}
```

The output contains only bounded anchors: identity, source path, lifecycle state, freshness, trigger/scope metadata, and evidence references. It does not inline the source body.

## Commands

```bash
python -m selective_recall verify
python -m selective_recall recall --request request.json
python -m selective_recall transition RAW ACTIVE_CANDIDATE
python -m selective_recall states
```

`transition` validates a proposed lifecycle edge only. It never writes the registry and always returns `applied: false`.

## Hard boundaries

```text
HISTORICAL EVIDENCE != CURRENT AUTHORITY
RETRIEVAL != DECISION COMPETENCE
ROUTING != AUTHORIZATION
STORAGE != ACTIVATION
VALID TRANSITION != APPLIED TRANSITION
```

No network, provider, subprocess, deploy, publish, payment, messaging, scheduling, adjacent-repository write, or Skill-application surface is owned by this package.

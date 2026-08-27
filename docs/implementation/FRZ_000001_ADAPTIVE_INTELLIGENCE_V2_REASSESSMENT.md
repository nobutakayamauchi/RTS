# RTS-FRZ-000001 Adaptive Intelligence v2 — Reassessment

## Status

```text
ASSESSMENT_ONLY
NO_IMPLEMENTATION_AUTHORITY
NO_SKILL_APPLICATION_AUTHORITY
NO_MAIN_BRANCH_CHANGE
```

This document is a bounded design and reuse assessment input for the existing `RTS-FRZ-000001 Governed Adaptive Memory Layer`.

It does not revise FREEZER lifecycle state by itself. `RTS-FRZ-000001` remains governed by the existing Build Assessment, Implementation Preflight, WIP=1, human approval, regression, rollback, Human Review Ledger, and Promotion Application Preview contracts.

## Why reassess now

RTS already has most of the governance skeleton that a safe adaptive-intelligence layer would otherwise need:

- FREEZER candidate governance and WIP=1
- Cross-Repo Asset Manifest
- Read-Only Loop Core
- Governed Execution Controller
- Outcome Evidence
- Outcome Learning and Skill Promotion proposal flow
- Skill regression and rollback linkage
- Human Review Ledger
- Promotion Application Preview
- Read-Only Governed Loop Orchestrator

The remaining opportunity is not to duplicate these controls. It is to make accumulated experience selectively reachable, incrementally compilable, restartable, and measurable so future AI work can reuse prior judgment without loading or recomputing the whole history.

## External evidence inspected

### 1. Decision-OS V13 LoopKit

Repository: `shin4141/decision-os-v13-loopkit`

Pinned reference inspected:

```text
fe88f90430bacbb8f5aaf3ac5439e0580c04abd6
```

License: MIT.

Relevant reusable ideas:

- selected external intelligence rather than everything-memory
- event-triggered / lane-based recall
- explicit memory lifecycle states
- conditional reading instead of loading every historical note
- context compression that preserves restart anchors
- completion state separated from next-loop authority
- stale memory must be rechecked before reuse
- routing does not itself grant execution authority

Reuse posture: `ADAPT / REFERENCE`, not wholesale framework import.

### 2. AGENTS.md Compactor

Repository: `shin4141/agents-md-compactor`

Pinned reference inspected:

```text
7679dceddc7213433f885d5054db50213460d266
```

License: Apache-2.0.

Relevant reusable ideas:

- keep universal instructions in a small always-loaded surface
- move conditional detail behind explicit reconnect triggers
- preserve traceability for moved knowledge
- measure active-surface reduction separately from total stored knowledge

Reuse posture: `ADAPT / REFERENCE`. Any direct code reuse must retain Apache-2.0 obligations and attribution.

### 3. Output Surface Integrity

Repository: `shin4141/output-surface-integrity`

Pinned reference inspected:

```text
5aa086171309bf83604360f0ea9fbcb169bbe921
```

License: MIT.

Relevant reusable ideas:

- compact continuation state rather than full history
- preserve exact restart point, unresolved state, evidence, owner, and next safe action
- do not accept fluent `done` as restartable closure
- retain adverse historical results instead of rewriting them after architectural correction

Reuse posture: `ADAPT / REFERENCE`.

### 4. Decision-OS V12 Completion Integrity

Repository: `shin4141/decision-os-v12-completion-integrity`

Relevant reusable ideas:

- `Changed / Unverified / Rollback / Do-not-touch / Next safe action`
- context signal for continuation versus handoff
- restartability as a completion property

Reuse posture: `REFERENCE` until exact reuse surface and license are recorded in a formal Build Assessment.

### 5. OpenClaw memory recovery continuation

Upstream repository: `openclaw/openclaw`

Contributor PR:

```text
#125722 — authored by shin4141
```

Maintainer continuation:

```text
#129927 — merged, explicitly credits @shin4141 for the original fix
```

Relevant reusable design pattern:

- when a batch is known to be too large, retrying the same batch is wasted work
- reuse an existing recursive split path
- preserve item ordering
- isolate self-describing recoverable limit conditions from generic malformed-input failures
- repair the transition so partial work can continue instead of losing the whole run

Reuse posture: `PATTERN_SEED_ONLY`. Do not copy OpenClaw implementation into RTS from this assessment.

## Core synthesis

The proposed v2 direction is:

> Preserve raw experience first, retrieve only the decision-relevant prior structure, spend expensive reasoning only on the unresolved novelty, and compile new reusable intelligence incrementally under the existing RTS approval and rollback system.

This is not model self-training and must not be presented as model-weight learning.

## Proposed architecture

```text
Goal / Event
    ↓
Intent + Risk Router
    ↓
Selective Recall Router
    ├─ current canonical rules
    ├─ relevant decision lane(s)
    ├─ prior failure boundaries
    ├─ restart anchors
    └─ reusable skill candidates
    ↓
Known / Unknown Partition
    ├─ Known → reuse verified decision / skill / invariant
    └─ Unknown → allocate fresh model reasoning
    ↓
Existing RTS Execution + Evidence Pipeline
    ↓
Outcome / Evidence / Human Review
    ↓
Incremental Intelligence Compiler
    ├─ raw observation
    ├─ candidate finding
    ├─ repeated finding
    ├─ reusable decision
    ├─ rule / invariant candidate
    └─ skill proposal
    ↓
Existing RTS Promotion / Regression / Rollback Gates
    ↓
Selective future retrieval
```

## New joint A — Selective Recall Router

Add a bounded retrieval layer before expensive reasoning.

Required properties:

- no recall for tiny local tasks when current context is sufficient
- select at most the smallest set of memory lanes that can change the next action
- retrieve the smallest anchor first
- preserve provenance and As-of state
- stale or superseded memory cannot act as current authority
- retrieved memory can inform a decision but cannot authorize execution
- over-recall is measurable process debt

Candidate lanes for RTS should be derived from actual RTS work rather than copied as fixed categories. Initial seed categories may include:

- execution / runtime evidence
- rollback / recovery
- promotion / skill governance
- public / release boundary
- repeated failure / debugging
- commercial / spend boundary

## New joint B — Memory Lifecycle

Add explicit status to reusable intelligence records.

Candidate lifecycle vocabulary:

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

Rules:

- storage does not imply activation
- repeated observation does not imply automatic promotion
- Canonical status requires existing RTS human-review / regression / promotion gates
- folded and superseded records remain available as provenance
- quarantine isolates contradictory or malformed experience without blocking unrelated learning

## New joint C — Compact Active Surface

Keep the always-loaded instruction surface small.

The active layer should contain only:

- authority and safety invariants
- routing triggers
- evidence rules
- stop conditions
- current goal / operating state pointers

Conditional procedures, historical decisions, examples, and failure records should remain reconnectable outside the active surface.

Do not measure success as total repository size reduction. The relevant measurement is active-load burden plus successful reconnectability.

## New joint D — Compact Restart Surface

A new AI session should not need the full chronology to continue safely.

Minimum restart state should preserve:

- current goal
- current canonical source / commit / branch identity
- what changed
- verified evidence
- unresolved items / UNKNOWNs
- rollback or restart point
- protected / do-not-touch surfaces
- next authorized action
- next owner or human decision point
- reopen-full-history condition

A smaller restart note is a failure if it removes a decision-critical restart item.

## New joint E — Incremental, Resumable, Failure-Isolated Intelligence Compilation

This is a core invariant for long-lived adaptive intelligence.

```text
Evolution must be incremental, resumable, and failure-isolated.
```

Required behavior:

1. raw outcome/evidence is durably recorded before intelligence compilation
2. large learning work is split into bounded chunks
3. each completed chunk can be checkpointed independently
4. one failed chunk does not discard successful chunks
5. failed chunks enter retry or quarantine state
6. a later run resumes from the incomplete chunk instead of replaying the entire compilation
7. only decisions related to changed evidence are reevaluated by default
8. full-corpus recompilation requires a separate explicit reason
9. intelligence compilation failure must not erase or invalidate the completed main task

This generalizes the useful transition pattern demonstrated by the OpenClaw oversized-batch recovery without importing its product-specific code.

## New joint F — Known / Unknown Budget

Do not optimize only by selecting a cheaper model.

Partition work into:

```text
KNOWN
PARTIALLY_KNOWN
UNKNOWN
```

Expensive/high-reasoning model use should concentrate on `UNKNOWN` and unresolved contradictions.

Known work should preferentially use:

- verified prior decisions
- deterministic tools
- existing Skills
- focused evidence reads
- bounded checks

This is a routing policy, not a guarantee of lower quota usage.

## New joint G — Recompute and Knowledge-Debt Accounting

Provider-side token caching and RTS-side intelligence reuse must be measured separately.

Candidate metrics:

- `decision_reuse_rate`
- `failure_reuse_rate`
- `retrieval_precision`
- `retrieval_changed_next_action_rate`
- `novel_reasoning_ratio`
- `recompute_avoidance_rate`
- `retry_avoidance_count`
- `human_intervention_count`
- `restart_surface_load`
- `knowledge_debt_count`
- `promotion_candidate_count`
- `quarantined_learning_count`
- `promotion_rollback_count`
- provider-reported cached input ratio, if available

Do not infer cache or quota causality from External Intelligence metrics.

### Knowledge Debt

Knowledge Debt is unfinished intelligence work that has already produced raw experience but has not yet been safely evaluated, reconciled, promoted, folded, superseded, archived, or quarantined.

A high debt level should trigger bounded background or maintenance work only when current WIP and human authority allow it. It must not silently preempt the active product goal.

## New joint H — External Transition Pattern Seed Corpus

Shin's public repair history and other external OSS repairs can seed candidate failure patterns, but never Canon directly.

Every external seed must record:

- source repository and exact ref / PR
- observed failure boundary
- repair principle
- evidence class
- applicability conditions
- counterexample / non-applicable condition
- license / reuse status
- RTS validation status

Initial pattern families worth seeding:

- partial progress must not be lost when transport or batch work fails
- unknown state must not be silently converted into clean absence
- changing context invalidates stale derived state
- failed transient initialization may need a future retry path while remaining failed for the current caller
- oversized work should be reduced or partitioned instead of replayed unchanged when the failure is self-describing
- completion claims must bind to durable evidence and current identity
- rename/copy transitions must preserve destination identity
- configuration type mismatches should not be silently coerced across policy boundaries

External seeds begin as `VERIFICATION_PENDING` or `RAW`; they do not become RTS Canon because another project merged them.

## Existing RTS capabilities that must not be duplicated

Do not build parallel replacements for:

- FREEZER priority and human-selection governance
- Governed Execution Controller
- Outcome Evidence
- Skill Regression and rollback
- Outcome Learning proposal generation
- Human Review Ledger
- Promotion Application Preview
- Read-Only Governed Loop Orchestrator

The v2 work should connect to these existing components.

## Devil's Advocate — primary failure modes

### 1. Governance drag

Risk: every tiny action starts a memory ritual.

Countermeasure: no-recall fast path; retrieval must change a gate, protected surface, first read, or next action to justify its cost.

### 2. Stale-memory authority leak

Risk: an old decision is retrieved and treated as current permission.

Countermeasure: provenance, freshness state, supersession checks, and strict separation between memory and authority.

### 3. Knowledge bloat

Risk: the system stores everything and active context grows indefinitely.

Countermeasure: lifecycle states, folding, archiving, compact active surface, conditional retrieval, and active-load metrics.

### 4. Bad learning compounds

Risk: one incorrect observation becomes a reusable rule and multiplies future errors.

Countermeasure: evidence separation, repeated observation, falsifier/countercondition, regression, human review, quarantine, rollback.

### 5. Learning pipeline blocks the real job

Risk: main work succeeds but post-run intelligence compilation is too large and causes the whole workflow to fail.

Countermeasure: raw-first persistence, chunking, partial checkpointing, resumability, failure isolation, and non-blocking compilation status.

### 6. Cache-causality confusion

Risk: high provider cache hit rate is credited to RTS memory without evidence.

Countermeasure: separate provider cache metrics from RTS intelligence-reuse metrics and require controlled comparison before causal claims.

### 7. External-pattern overfitting

Risk: repair patterns from unrelated repositories become generic dogma.

Countermeasure: external seeds remain non-canonical until internal recurrence or explicit validation establishes transferability.

### 8. Licensing / attribution drift

Risk: conceptual reference turns into copied code without license accounting.

Countermeasure: Build Assessment must record exact path/ref/reuse mode/license before direct reuse. Reference-only assets are not code-import authority.

## Recommended decomposition

This candidate is too broad for one implementation PR. The expected Preflight posture is `DECOMPOSE_REQUIRED` unless later evidence shows a smaller safe boundary.

Recommended children:

### Child A — Selective Recall + Memory Lifecycle

Scope:

- memory record lifecycle schema
- event / lane routing
- provenance / freshness / supersession checks
- no-recall fast path

### Child B — Compact Active + Restart Surface

Scope:

- reconnect triggers
- compact active instruction surface
- restart-item registry
- restart-equivalence checks

### Child C — Incremental / Resumable Intelligence Compiler

Scope:

- chunk model
- checkpoint model
- retry / quarantine state
- differential reevaluation
- non-blocking learning status

### Child D — Reuse Efficiency + Knowledge Debt Metrics

Scope:

- intelligence-reuse metrics
- recompute metrics
- knowledge-debt accounting
- provider-cache metric separation

### Child E — External Transition Pattern Seed Corpus

Scope:

- source/provenance schema
- first external repair-pattern dataset
- applicability / countercondition fields
- validation and promotion boundary

A separate child for promotion governance is not recommended because RTS already has Outcome Learning, Skill Regression, Human Review Ledger, and Promotion Application Preview.

## Prepared canonicalization packet

The following bounded inputs are now committed under `docs/implementation/frz000001_v2_inputs/`:

- parent v2 revision input
- parent Build Assessment input
- parent `DECOMPOSE_REQUIRED` Preflight input
- five child candidate inputs

The exact governed execution sequence is recorded in:

```text
docs/implementation/FRZ_000001_ADAPTIVE_INTELLIGENCE_V2_EXECUTION_TASK.md
```

These inputs are preparation only. Until the FREEZER CLI runs successfully and verification passes, they are not canonical FREEZER state.

## Formal next action

1. run the bounded execution task on this PR branch
2. canonicalize parent v2, Build Assessment, and `DECOMPOSE_REQUIRED` Preflight
3. create the five children as `FROZEN / NOT_APPROVED`
4. rebuild indexes and manifest
5. verify the exact final head
6. leave every child unselected until a separate Build Assessment, PASS Preflight, and human approval exists

## Completion line for this reassessment

This reassessment is complete when:

- the external evidence and reuse boundaries are reviewable
- proposed new joints are separated from already-implemented RTS governance
- DA / countermeasures are explicit
- decomposition is defined
- canonicalization inputs and execution order are reviewable
- no implementation or child selection authority is implied by this document

# Ultimate Loop Lifecycle — Prototype / METEOR Result

Timestamp: **2026-08-13**

Status: `REPOSITORY_METEOR_SURVIVES_UNDER_CURRENT_EVIDENCE`

Candidate:

`thin-rts/ultimate-loop/lifecycle.py`

Frozen discipline:

`KEEP EXISTING -> EXTRACT FROM EXISTING STRUCTURE -> NEW BUILD ONLY IF IRREDUCIBLE -> PROTOTYPE -> DESTRUCTIVE METEOR -> MINIMAL REPAIR -> SAME WORKLOAD`

The workload was not weakened after failure.

## 1. What the prototype owns

Only typed, side-effect-free lifecycle binding survives:

- core lifecycle state and re-entry routing;
- current/stale trigger evidence handling;
- candidate disposition among candidate/shadow/standby/partial/full-replacement paths;
- separation of Replacement Value from Resilience Value;
- explicit promotion/failover authority boundaries;
- recovery versus PHOENIX regeneration state;
- fail-closed handling of unknown future trigger classes.

It does **not** own crawling, scheduling, databases, deployment, failover execution, backup storage, cryptography, cloud transport, model inference or autonomous promotion.

## 2. Baseline + destructive workload

Repository CI executes:

- baseline lifecycle tests;
- rotated destructive METEOR attacks;
- three canonical lifecycle workloads;
- a separate creator-absent PHOENIX probe.

Current repository evidence after repair:

- lifecycle baseline + destructive METEOR: **30/30 PASS**;
- canonical workload exercise: **PASS**;
- creator-absent lifecycle PHOENIX job: **PASS**.

The three canonical workloads prove, under the current bounded model:

1. a **+3%** candidate with unproven stability but high resilience value can remain `STANDBY` without becoming PRIMARY;
2. an emergency fallback with only a logical independence label is blocked when the failed domain is material;
3. a durable BUILD frame with acceptance, authority, fresh recovery and PHOENIX evidence can transition to `STABLE`.

## 3. Repository METEOR death retained

The first repository lifecycle run did **not** pass.

Attack:

> Feed an unknown future trigger together with an otherwise attractive, promotion-ready candidate.

Expected invariant:

`UNKNOWN_TRIGGER -> INNER_LOOP_REOPEN`

Observed failure:

The trigger layer correctly returned `INNER_LOOP_REOPEN`, but later candidate-disposition logic overwrote the final next state back to `STABLE` because the challenger looked promotion-ready.

Autopsy:

`CORRECT_TRIGGER_CLASSIFICATION != FINAL_TRANSITION_PROTECTION`

and more specifically:

`UNKNOWN_TRIGGER_REOPEN MUST DOMINATE CANDIDATE_PROMOTION`

This was a material lifecycle failure: a genuinely new/unmodeled event could have been silently absorbed by a known replacement path instead of reopening design review.

## 4. Repair

The candidate layer was changed so that:

- unknown/unmodeled triggers suspend challenger promotion and return `BLOCKED_PENDING_INNER_REVIEW`;
- stale or otherwise unusable trigger evidence suspends challenger comparison with `BLOCKED_BY_TRIGGER_EVIDENCE`;
- candidate attractiveness cannot repair or override an invalid trigger boundary.

No crawler, service, policy engine, scheduler or other product capability was added.

The exact failed destructive test remains in the suite and passes after repair.

## 5. Surviving destructive invariants

The current workload verifies at minimum:

- a 300% score alone cannot promote an unstable candidate;
- stale challenger evidence cannot open METEOR;
- rumor/unverified discovery cannot open METEOR;
- failed migration blocks replacement;
- failed rollback blocks replacement;
- a winner does not create promotion authority;
- same-domain labels do not prove failure-domain independence;
- backup presence does not prove recovery;
- recovery does not prove creator-independent PHOENIX regeneration;
- unknown future trigger classes reopen inner design rather than being guessed;
- a small numerical win with high resilience may be preserved as STANDBY;
- non-material novelty does not consume a full METEOR challenge;
- a fully survived, authorized material challenger remains eligible for replacement.

## 6. Threshold status

The prototype currently carries screening priors:

- `5%` — observe/shadow consideration;
- `15%` — material partial/replacement comparison consideration;
- `30%` — full-replacement consideration.

These are **not universal adoption thresholds** and are not encoded as authority.

A candidate cannot become PRIMARY from percentage gain alone. Same-workload survival, migration/rollback evidence, authority and workload-specific constraints still govern promotion.

Real dogfood evidence may recalibrate or kill these screening priors without changing the higher invariant.

## 7. Gate verdict

`GENERAL ULTIMATE LOOP PLATFORM = NOT JUSTIFIED`

`EXISTING WITNESS / METEOR / DARWIN / PHOENIX / CONTINUITY = REUSED`

`PURE LIFECYCLE BINDER = SURVIVES UNDER CURRENT REPOSITORY EVIDENCE`

`KNOWN METEOR DEATH = RETAINED AS PERMANENT REGRESSION MEMORY`

No claim of exhaustive future-event coverage, universal optimal thresholds, perfect resilience or automatic replacement correctness is made.

New material evidence may reopen this frame.

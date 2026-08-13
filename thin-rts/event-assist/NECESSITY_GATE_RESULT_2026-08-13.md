# Event Assist — Gate 1 Necessity Result

Timestamp: **2026-08-13 09:18 JST**

Status: `GATE_1_EXECUTED / GLUE_SURVIVES / GATE_2_REQUIRED`

System: **新RTS（仮称）**

## Question

Does the QRTS-derived Event Assist outcome require a new owned subsystem, or can the responsibility be killed, externalized, composed, bounded manually, or reduced to thin glue?

## Frozen outcome

For a material real-world event, the operator should be able to move from incomplete raw input to an evidence-aware, authority-safe next action without silently losing important facts, deadlines, provenance, or recovery paths.

The gate does **not** require 新RTS（仮称） to become a legal service, crawler, document platform, calendar service, evidence store, or cloud.

## Raison d’être Destroy result

| Responsibility | Destroy result | Surviving minimum |
|---|---|---|
| free-form event interpretation | `EXTERNALIZE / COMPOSE` | external AI/tooling may interpret; retain normalized case state and UNKNOWNs |
| current law/program/fact retrieval | `EXTERNALIZE` | official/current external sources with provenance and staleness recorded when material |
| broad web crawling / background monitoring | `DROP FROM CORE` | use external/native search/watch mechanisms only when workload requires them |
| calendar/reminder execution | `EXTERNALIZE` | external/native scheduler; core keeps only Action Pin identity, deadline/source, state and handoff reference |
| evidence file storage | `EXTERNALIZE / COMPOSE` | existing quarantine/custody/continuity contracts; core keeps evidence references, integrity/provenance and gap state |
| cryptography / vault / cloud | `EXTERNALIZE` | existing external cryptography/provider occupants through adopted custody/recovery contracts |
| document rendering/editor | `EXTERNALIZE` | external document tooling; core keeps facts/evidence/authority/submission-state bindings |
| autonomous submission/contact/publication | `DROP FROM CORE` | explicit authority remains separate; execution by authorized external tool/human only |
| provider-specific scraper/exporter | `EXTERNALIZE` | replaceable adapter; declared required scope must fail closed when absent |
| EventCase state binding | `GLUE_REQUIRED` | normalized facts, claims, assumptions, UNKNOWNs, applicability/provenance references |
| Evidence Gap Register | `GLUE_REQUIRED` | what is held, missing, disputed, stale, or unsafe to infer |
| Action Pins | `GLUE_REQUIRED` | next action, deadline/trigger, source, authority requirement, completion/evidence reference |
| authority boundary | `GLUE_REQUIRED` | analysis/draft/notification/acquisition/submission/promotion remain distinguishable |
| watch/notification health evidence | `GLUE_REQUIRED WHEN DECLARED` | record whether the external watcher exists, last succeeded, and what failure means; do not build a daemon |
| handoff to safety/custody/recovery | `COMPOSE` | reuse Intake/Egress Quarantine and Continuity/Recovery rather than new security/storage systems |

## DA / Counter-DA

### DA-01 — “A complete successor needs an Event Assist platform”

**Killed.** The outcome does not justify a new crawler, daemon, database, object store, calendar, legal engine, document editor, or cloud.

### DA-02 — “If everything is externalized, no owned responsibility remains”

**Fails.** External tools can individually retrieve, schedule, store, draft, or submit, but without a bounded cross-boundary state contract the operator can lose which fact was verified, which evidence is missing, which deadline belongs to which source, and which action was merely proposed versus authorized.

Repair: retain only the small binding contracts above.

### DA-03 — “A checklist is enough”

**Insufficient for the declared zero-omission outcome.** A checklist can guide a bounded manual case, but it does not by itself preserve machine-checkable gap state, deadline/source linkage, authority state, and recovery references across tool/provider changes.

Repair: checklist/manual operation remains allowed, but the material state must be representable by the thin contract.

### Counter-DA-01 — “The glue will grow back into old RTS”

Hard containment:

- no owned watcher daemon;
- no owned retrieval engine;
- no owned calendar;
- no owned evidence blob store;
- no owned crypto/vault;
- no automatic external action authority;
- every concrete adapter remains a DARWIN occupant.

Any proposed addition must rerun Raison d’être Destroy.

### Counter-DA-02 — “One universal event schema will overfit every real case”

Repair: keep only invariant binding fields and allow workload-specific extensions. Unknown or unobserved material facts stay `UNKNOWN`; they are not converted to false certainty to satisfy a schema.

### Counter-DA-03 — “External monitoring can silently die”

Repair: when monitoring is declared material, watch-health evidence becomes part of the case contract. A missing/stale watcher is not silently treated as ‘no change’.

## Gate 1 verdict

`SEARCH_SATURATED_UNDER_CURRENT_REPOSITORY_EVIDENCE`

`MONOLITHIC_EVENT_ASSIST = KILLED`

`IRREDUCIBLE_CUSTOM_PLATFORM = NOT_JUSTIFIED`

`BOUNDED_EVENT_STATE_GLUE = SURVIVES`

Therefore Gate 1 **passes only for the surviving thin responsibility**. This does not authorize product-completion status.

## Next mandatory gate

The surviving glue must enter the already-frozen Event Assist METEOR CRUCIBLE and a material real-situation pilot. The same workload must demonstrate, at minimum:

- missing/stale/contradictory evidence remains visible;
- applicability/current-source provenance is not invented;
- Action Pins preserve deadline/trigger/source identity;
- notification/watch failure is distinguishable from no event;
- draft/analysis is not submission authority;
- evidence and recovery references survive provider/tool change;
- operator burden does not exceed the simpler external/manual composition without compensating safety/reproducibility value.

Until that survives:

`EVENT_ASSIST_PRODUCT_OUTCOME = NOT_COMPLETE`

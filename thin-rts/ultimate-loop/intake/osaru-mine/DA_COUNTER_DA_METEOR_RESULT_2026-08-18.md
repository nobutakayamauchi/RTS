# OSARU MINE → Ultimate Loop — DA / Counter-DA / Contract METEOR

Timestamp: **2026-08-18 JST**

Status: `ATTACKED / 3 DEMOTED / 2 CANONICAL-CANDIDATE SURVIVORS / NO PROMOTION AUTHORITY`

Frozen subject:

`Five possible Ultimate Loop extensions derived from OSARU MINE 100-task universal extraction`

Frozen workload:

`intake/osaru-mine/challenger-workload-v1.json`

Authority:

`NONE`

This result is deliberately narrower than a full real-world METEOR win. Repository tests attack the **contracts and failure boundaries** of the five extensions. They do not prove universal utility, real customer value, or canonical promotion fitness.

Hard rule:

`CONTRACT SURVIVES DESTRUCTIVE TESTS != CANONICAL PROMOTION`

## 1. Attack summary

The original five proposals do **not** survive unchanged.

| Extension | DA attack | Counter-DA survivor | Current disposition |
|---|---|---|---|
| EXT01 First-party signal binding | A mandatory direct-user gate breaks offline/library/non-user workloads and may force unnecessary customer contact | direct evidence may be typed when a human/user surface actually exists; otherwise `NOT_APPLICABLE` | `DEMOTE_TO_CONDITIONAL_EVIDENCE_PROFILE` |
| EXT02 Canonical-source compiler | risks turning Ultimate Loop into a publisher/platform; derived views may drift or leak private fields | a tiny source→adapter contract can preserve fingerprints/provenance and reject leakage without owning channels | `DEMOTE_TO_NONCANONICAL_SUPPORT_CONTRACT` |
| EXT03 Bottleneck re-entry routing | weak metrics/correlation can falsely declare root cause and jump to the wrong gate | route only when failure stage is proven; uncertain causality reopens analysis; router owns no diagnosis | `CANONICAL_EXTENSION_CANDIDATE` |
| EXT04 Scale-proof gate | “prove locally before scale” is false for behavior that only appears under load/scale and can block required learning | safety/correctness dominate; bounded scale probes remain allowed behind guardrails | `DEMOTE_TO_CONDITIONAL_SCALE_PROFILE` |
| EXT05 Decision-capability succession | retrieval/backups/reconstruction can be mistaken for competence or authority; may expand PHOENIX too far | require held-out decisions, authority compliance, escalation behavior and creator absence; retrieval alone fails | `CANONICAL_PHOENIX_EXTENSION_CANDIDATE` |

Result:

`5 PROPOSALS -> 2 POSSIBLE CANONICAL DELTAS + 3 WORKLOAD/SUPPORT PROFILES`

No new top-level five-stage expansion survives.

## 2. EXT01 — First-party signal binding

### DA

Attack:

> Make first-party evidence mandatory for every Ultimate Loop workload.

Death:

- offline libraries may have no user-contact surface;
- infrastructure can have runtime evidence rather than “customer voice”;
- mandatory human contact creates unnecessary authority/privacy burden;
- external discovery and runtime probes are sometimes the correct evidence class.

Therefore:

`FIRST_PARTY_SIGNAL = UNIVERSAL GATE` **dies**.

### Counter-DA

A narrower responsibility survives:

> When a frozen workload has a real human/user/operator surface and the decision materially depends on their current behavior or language, distinguish direct bound evidence from inferred/secondary evidence.

This is an **evidence profile**, not a new lifecycle stage.

Repository attack confirms:

- forcing it onto a non-user workload is rejected;
- a current bound signal with consent/privacy state can be composed conditionally;
- it grants no promotion authority.

Verdict:

`DEMOTE_TO_CONDITIONAL_EVIDENCE_PROFILE`

## 3. EXT02 — Canonical-source compiler

### DA

Attack:

> Let Ultimate Loop own publication/adapters so one source can generate everything.

Death:

That violates the existing externalization boundary. Ultimate Loop must not become a CMS, channel runtime, publishing platform, crawler or general adapter host.

Additional failure classes:

- derivative factual drift;
- provenance loss;
- private-field leakage;
- derived presentation silently becoming a new source of truth.

### Counter-DA

A bounded contract survives:

```text
CANONICAL FACT SET
→ EXPLICIT ADAPTER
→ SAME FACT FINGERPRINT
→ PROVENANCE PRESERVED
→ PRIVATE-FIELD LEAKAGE = FALSE
```

The repository crucible kills an adapter when its fact fingerprint drifts or when a private field leaks.

But the surviving responsibility is support infrastructure for Memory/PHOENIX/public-safe views, not a new Ultimate Loop lifecycle gate.

Verdict:

`DEMOTE_TO_NONCANONICAL_SUPPORT_CONTRACT`

Real cross-adapter dogfood can strengthen or kill this later.

## 4. EXT03 — Bottleneck re-entry routing

### DA

Attack:

> A bad metric appears; the router labels the “weakest stage” and jumps directly there.

This is unsafe.

`CORRELATION != ROOT CAUSE`

A router that also diagnoses causality can silently bypass the broader DA/METEOR path and optimize the wrong layer.

### Counter-DA

The irreducible survivor is much smaller:

> **Given externally established stage evidence, bind a proven failure to the smallest existing re-entry gate. If causality is not proven, reopen analysis.**

Current typed mapping under the frozen contract:

```text
DISCOVERY          → DISCOVERY_REFRESH
IMPLEMENTATION     → DA_COUNTER_DA
DEPLOYMENT         → DEPLOYMENT_IDENTITY
POST_DEPLOY_METRIC → POST_DEPLOY_DEBUG
UNKNOWN/CORRELATED → ANALYSIS_REOPEN
```

It owns **routing only**, not root-cause inference.

Repository destructive tests confirm:

- correlation-only evidence cannot claim a local root cause;
- a wrong local route is rejected;
- a proven stage can route to its smallest existing gate;
- self-promotion remains impossible.

This is the strongest new core-method delta found in the five proposals because it composes existing gates rather than creating another platform.

Verdict:

`CANONICAL_EXTENSION_CANDIDATE`

Not yet canonically promoted.

## 5. EXT04 — Scale-proof gate

### DA

Attack:

> Nothing may scale until the local loop is proven.

Death:

Some failures, queue behavior, concurrency effects, economics, distribution effects, network effects and load-dependent behavior cannot be observed locally. A universal local-proof prerequisite can make the workload impossible to test.

Also:

`BUSINESS METRIC != SAFETY/CORRECTNESS OVERRIDE`

### Counter-DA

A conditional profile survives:

- safety and correctness must already be acceptable for the intended probe;
- known local repeatability may permit bounded scaling with guardrails;
- when behavior is scale-dependent, an explicitly bounded scale probe may occur before “local proof”;
- scaling never creates promotion authority and monitoring continues.

Repository attacks confirm both sides:

- safety failure blocks scale even if local business proof looks attractive;
- scale-dependent learning is allowed only as a bounded guarded probe.

Verdict:

`DEMOTE_TO_CONDITIONAL_SCALE_PROFILE`

No universal Scale Gate is justified.

## 6. EXT05 — Decision-capability succession

### DA

Attack:

> A Succession Packet can be retrieved, therefore a successor can operate correctly.

Death:

`RETRIEVAL != UNDERSTANDING`

`UNDERSTANDING != DECISION COMPETENCE`

`DECISION COMPETENCE != AUTHORITY`

`RECOVERY != SUCCESSION`

A system can reconstruct files perfectly and still choose badly, exceed authority, or fail to escalate an unknown.

### Counter-DA

A PHOENIX-adjacent extension survives if it measures only externally supplied evidence and does not attempt to own a general agent runtime.

Minimum evidence profile:

- canonical protected material is available;
- held-out operational decisions are tested;
- authority compliance passes;
- escalation/UNKNOWN behavior passes;
- creator intervention is absent during the test.

Repository destructive tests confirm:

- retrieval PASS alone is explicitly rejected as competence proof;
- authority failure blocks succession;
- only the full creator-absent evidence profile survives as a PHOENIX extension candidate.

Verdict:

`CANONICAL_PHOENIX_EXTENSION_CANDIDATE`

A real held-out creator-absent exercise is still required before canonical promotion can be argued.

## 7. Repository METEOR evidence

Added:

- `osaru_extension_crucible.py` — side-effect-free, standard-library contract attacker;
- `test_osaru_extension_crucible.py` — destructive regression suite;
- CI integration in `validate-osaru-operator-intake.yml`.

Current CI result after adding the crucible:

- compile: **PASS**;
- original operator-intake regressions: **PASS**;
- extension destructive crucible: **15/15 PASS**;
- universal 100-task pack validation: **PASS**.

The suite retains attacks for:

- self-authorization;
- first-party overreach;
- canonical derivative fact drift;
- private-field leakage;
- correlation→root-cause substitution;
- wrong re-entry routing;
- scale outranking safety;
- universal local-proof blocking scale-dependent learning;
- retrieval→competence substitution;
- successor authority violation.

## 8. Gate verdict

The five proposals were successfully reduced.

```text
EXT01 -> conditional evidence profile
EXT02 -> non-canonical bounded support contract
EXT03 -> canonical extension candidate
EXT04 -> conditional scale profile
EXT05 -> canonical PHOENIX extension candidate
```

Therefore:

`OSARU MINE DOES NOT ADD FIVE NEW ULTIMATE LOOP STAGES.`

Under current repository evidence, it exposes **two potentially material canonical gaps**:

1. fail-closed **smallest-gate re-entry routing** after externally established failure-stage evidence;
2. **decision-capability succession proof** beyond mere recovery/retrieval.

Both remain challengers.

`DA/COUNTER-DA SURVIVOR != CANONICAL`

`CONTRACT METEOR PASS != REAL-WORLD SAME-WORKLOAD WIN`

`CANONICAL PROMOTION AUTHORIZED = FALSE`

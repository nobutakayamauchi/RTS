# Evidence Report Internal Hardening — HARD-002

## Result

```text
INTERNAL_OPERATOR_RUNBOOK_AND_INTAKE_CONTRACT_COMPLETE
HUMAN_INDEPENDENT_READER_REVIEW_PLAN_REQUIRED
```

HARD-002 turns the validated two-case evidence-report workflow into one bounded operator procedure. It defines what may enter the workflow, what must be rejected, where human decisions occur, what outputs are required, how the run stops, and how unresolved questions escalate.

## Instruction provenance lesson

The internal development history supports a useful but bounded observation: rough conversational instructions, including ordinary typing or conversion noise, were sufficient to drive several controlled stages after the intended scope was interpreted.

That observation remains part of the evidence. It does **not** require displaying a user's raw wording.

A presentation risk was later identified: some operator-facing records copied typo-bearing source text even though a one-way audit binding and an intent summary were enough. The project corrected this by separating two properties:

1. **execution robustness** — the system can interpret low-friction conversational instructions under human-reviewed scope;
2. **presentation hygiene** — operator-facing records use normalized intent-preserving language and avoid unnecessary verbatim reproduction.

The correction is recorded openly rather than hidden. The supported narrative is:

> Rough natural-language instructions worked during bounded internal development. After a display and privacy risk was noticed, operator-facing provenance was improved to use normalized intent summaries plus one-way fingerprint linkage.

This does not prove that every malformed instruction is safe, and normalization may never widen authority or silently invent missing intent.

## Intake boundary

The current intake contract accepts only an approved public repository in read-only mode with:

- an exact source ref;
- a bounded analysis objective;
- a human-reviewed normalized instruction and interpreted scope;
- explicit allowed claim classes;
- explicit excluded or withheld topics;
- a raw-input fingerprint without required raw-text retention.

It rejects private sources, credentials, customer or sensitive personal payloads, ambiguous consequential authority, unbounded objectives, and unresolved scope.

This contract is an **internal design artifact**. It does not authorize real customer intake.

## Operator procedure

The runbook contains seven phases:

1. receive and classify;
2. normalize and confirm intent;
3. run intake preflight;
4. freeze source and evidence boundary;
5. generate the deterministic package;
6. review claims and withheld topics;
7. close or roll back.

Human gates are required for scope confirmation, intake acceptance, build authorization, package acceptance, and the final internal decision.

The procedure requires ten output classes, two matching deterministic builds, evidence for every effective record, visible limitations, retained withheld claims, a reconstructable rollback target, and recorded operating metrics.

## Escalation

- `L0_OPERATOR`: formatting, missing non-sensitive fields, deterministic reruns, artifact inventory;
- `L1_PROJECT_OWNER`: scope, claim boundaries, withholding, internal acceptance;
- `L2_SECURITY_PRIVACY_REVIEW`: credential, personal-data, redaction, or retention signals;
- `L3_SEPARATE_GOVERNANCE_DECISION`: any proposed customer, commercial, publication, delivery, or external-execution action.

No external contact is performed by this runbook.

## Completion update

```text
RTS overall planning estimate: 73%
Short-term internal product candidate: 95%
Product-readiness score: 82/100
```

The product-readiness score remains 82 because HARD-002 improves operator control but does not create new evidence for independent-reader usability, third-case generalization, privacy-adversarial behavior, customer value, or production readiness.

## Remaining hardening

```text
HARD-003  Independent-reader usability review
HARD-004  Third-case generalization test
HARD-005  Privacy adversarial pack and operating metrics
```

## Authority boundary

```text
CUSTOMER_INTAKE_NOT_AUTHORIZED
CUSTOMER_PILOT_NOT_AUTHORIZED
NOT_PRICED
OUTREACH_NOT_STARTED
CONTRACT_NOT_STARTED
NOT_DELIVERED
NOT_PUBLISHED
NO_EXTERNAL_EXECUTION
NO_SOURCE_OR_TARGET_REPOSITORY_WRITES
```

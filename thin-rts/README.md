# Thin RTS v0 — External-First Reconstruction Layer

Status: **EXPERIMENTAL / TIME-ATTACK CANDIDATE**

Thin RTS is not a new RTS kernel.
It is the smallest reconstructability layer that survived the current externalization test.

## Goal

Preserve enough structure to reconstruct a material AI-assisted development decision after the original conversation/session is gone, while leaving execution, storage, search, CI, identity observation, review, signing, deployment, and most governance to existing external systems.

## Zero-additional-cost composition

Thin RTS owns no dedicated service.

External/default owners:

- **Git / GitHub** — durable source history, commits, diffs, PR/review evidence, branches/tags, artifact references.
- **Existing AI/tooling** — analysis, implementation assistance, evidence extraction, comparison, and DA; no RTS-owned model runtime.
- **WITNESS** — development existence gate, adversarial review, Destroy Loop, Meteor Gate, saturation stop rule; referenced rather than copied into RTS.
- **Provider/OS/native tools** — deployment/runtime reality (`service/process/route/artifact/revision` evidence where relevant).
- **Existing CI/test systems** — regression evidence and repeatable workload execution.
- **Human/project authority** — final material approval, promotion, disclosure, publication, external contact, and scope expansion.
- **External trust domain/person/org** — administratively independent authority when such independence is genuinely required; Thin RTS must not fake it.

Optional existing OSS may be used when a workload actually requires stronger policy/signing/attestation/tracing, but no optional component is made mandatory merely to make the architecture look complete.

## Thin RTS-owned surface

Only two things are currently justified:

1. **a minimal record contract** binding intent, authority, constraints, action, runtime/deployment evidence when relevant, outcome, review/learning, promotion authority, and next-state references;
2. **a reconstruction rule** that follows those references and refuses to promote missing evidence to VERIFIED.

No controller, kernel, daemon, database, queue, scheduler, vector store, telemetry service, proprietary WORM store, custom replay database, custom agent runtime, or stateful promotion engine is authorized by this version.

## Minimal record

Each material transition records only what cannot safely be reconstructed from an external source later:

- `record_id`
- `timestamp`
- `intent_summary`
- `source_fingerprint_or_reference`
- `constraints`
- `assumptions`
- `authority`
- `action_reference`
- `deployment_identity_reference` when runtime reality matters
- `outcome_reference`
- `classification`
- `learning_or_review_reference`
- `promotion_authority_reference` when state/capability changes
- `next_state_reference`
- `unknowns`

Raw private source wording is not copied merely for convenience. Use normalized intent plus bounded one-way linkage/reference when that is sufficient for auditability.

## Reconstruction rule

A reconstruction is valid only when an independent reader can follow the recorded pointers and distinguish:

- intended state from observed state;
- code/revision from deployed runtime reality;
- execution from outcome;
- review/learning from promotion authority;
- current evidence from stale/replayed evidence;
- known fact from UNKNOWN;
- human/AI analysis from authorized external action.

Missing material links remain `UNKNOWN`, `BLOCKED`, or `EVIDENCE_INSUFFICIENT`. They are never repaired by assumption.

## Fail-closed authority rule

Evidence that a message, patch, analysis, recommendation, test, or learning proposal exists does not authorize a materially different action.

Examples requiring their own authority when applicable include:

- publishing;
- contacting a third party;
- changing a repository or production state;
- spending money;
- disclosing private data;
- merging/promoting/deploying;
- changing security or trust boundaries.

## Security / privacy rule

Thin RTS maximizes reconstructability without maximizing retained sensitive data.

- Do not commit secrets or unnecessary personal/private payloads.
- Preserve provenance by reference/fingerprint where raw disclosure is unnecessary.
- Security-sensitive decisions receive adversarial review and runtime evidence appropriate to the risk.
- Collection breadth does not imply indefinite retention or trust.

## Reference workload for this revival

Thin RTS must demonstrate one real development chain on this branch:

`requirement`
→ `decision/constraints/authority`
→ `repository mutation`
→ `commit evidence`
→ `verification`
→ `outcome classification`
→ `learning/review`
→ `separate authorization for any promotion/change`
→ `next-state reference`

Then the same chain is attacked with deliberate mismatch/destruction cases. At minimum test:

- wrong/stale commit reference;
- code-exists-but-runtime-not-proven claim;
- outcome from the wrong execution/session;
- missing promotion authority;
- raw-sensitive-data retention attempt;
- replay/stale evidence attempt where relevant;
- loss/corruption of a noncanonical convenience copy while canonical Git evidence survives.

The workload must not be weakened after failure.

## Success condition

Thin RTS v0 survives only if the development decision can be reconstructed from external evidence plus this minimal binding layer, and destructive tests fail closed without requiring revival of the old RTS Runtime/Controller/Governance Kernel.

If a material gap remains, it returns to WITNESS for Destroy Loop / Meteor Gate. Only an irreducible remainder may authorize new glue.

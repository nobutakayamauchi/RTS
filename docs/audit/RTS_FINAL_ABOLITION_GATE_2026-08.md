# RTS Final Devil's Advocate — Abolition Gate

Status: **CLOSED / PROJECT FROZEN**
Date: 2026-08
Final formal verdict: **EVIDENCE_INSUFFICIENT / REVISE**
Engineering continuation decision: **NO**

## The question

> Abolish RTS. Using only external AI systems and existing tools available as of August 2026, construct an equal-or-better system. If this can be done, deny the reason to retain RTS.

This is a mandatory survival test, not a marketing comparison.

## Decision rule

RTS survives only if a material, testable gap remains after constructing the strongest external replacement stack.

A replacement wins if it can provide equal-or-better behavior with equal-or-lower total complexity/cost while preserving all mandatory invariants below. Familiarity, sunk cost, authorship, branding, and historical priority are not valid reasons to retain RTS.

If the external stack wins, the correct RTS action is deprecation or reduction to only the irreducible policy/reference layer.

## Mandatory invariants

1. Claims require evidence; unsupported claims are withheld.
2. Code existence is not runtime evidence.
3. Revision equality alone is not runtime reality.
4. Runtime identity is bound to observed deployment material, route/process/instance/artifact reality, external expectations, freshness, and trusted observation provenance.
5. Material match alone is not authorization.
6. Independent attestation/observation trust cannot be created by self-declared labels alone.
7. Runtime observations are bound to the authorized deployment identity.
8. Outcome evidence is bound to the same deployment, expectation, session, runtime observation, and execution identity.
9. Success is not proof of promotion eligibility.
10. Learning is not authority. Capability change requires separate governed promotion authority and regression evidence.
11. Failure, escalation, recovery, rejection, and withheld claims remain evidence; the system may not preserve only successes.
12. Human/project authority is explicit and scope-limited; permission for one surface does not imply permission for another.
13. The same proof rules apply to changes to the governance system itself. No RTS self-exemption.
14. Known trust boundaries and unproved physical truth must be stated rather than silently promoted to VERIFIED.

## Strongest external replacement hypothesis

The external challenger MUST be evaluated as a composition, not as a single product. Candidate functions include:

- Agent execution / coding AI: contemporary external agent platforms.
- Agent tracing and evaluation: LangSmith and/or OpenTelemetry-compatible tracing/evaluation.
- Policy decision/enforcement: Open Policy Agent (OPA/Rego).
- Workload identity and attestation: SPIFFE/SPIRE.
- Artifact and statement signatures / transparency: Sigstore Cosign/Rekor.
- Signed step/material/product provenance: in-toto attestations/layouts.
- Source and immutable public history: Git/GitHub plus protected CI.
- Regression/promotion gates: existing CI/evaluation systems with explicit policy gates.

Use better external components if discovered. The purpose is to defeat RTS, not to make this list win.

## Required external-replacement proof

The challenger must demonstrate one continuous, fail-closed chain:

Expected Source/Policy
→ Observed Deployment Material
→ Runtime Workload Identity
→ Active Route/Process/Instance/Artifact Reality
→ Authorized Runtime Observation
→ Execution Identity
→ Signed Outcome Evidence
→ Failure/Recovery/Success Classification
→ Learning Proposal
→ Regression/Counter-evidence
→ Independent Promotion Authority
→ Changed Capability
→ Re-entry into the same proof chain.

A diagram or collection of product features is insufficient. Each transition must have an enforceable binding and an adversarial test showing that mismatched/replayed/self-asserted evidence is rejected.

## Abolition attacks

The external stack wins only after these attacks are attempted:

- substitute another deployment after attestation (TOCTOU)
- reuse a valid old attestation/outcome (replay)
- claim independent observers using self-declared trust-domain names
- route to an unobserved worker
- keep commit equal while changing artifact/config/environment
- attach an outcome from another run/session/execution
- promote a capability because it performed well without separate authority
- discard failure/escalation/recovery evidence while preserving success
- bypass the closure through a second API/CLI/manual path
- modify the governance policy itself without the same proof requirements

## Verdict states

- ABOLISH_RTS: external tools satisfy all invariants with equal-or-lower complexity/cost; RTS adds no irreducible value.
- REDUCE_RTS: external tools provide the mechanisms; only RTS's small integration/policy semantics remain justified.
- RETAIN_RTS: an enforceable material gap remains that cannot be reproduced without rebuilding a substantively equivalent RTS layer.
- EVIDENCE_INSUFFICIENT / REVISE: the question remains valid but evidence is insufficient for a terminal survival/abolition claim.
- TEST_INVALID_OR_OVERCONSTRAINED: the comparison itself is contradictory, unattainable, or unreasonably constrained.

## Final result

**EVIDENCE_INSUFFICIENT / REVISE**

External Challenger testing demonstrated that the major technical responsibilities previously implemented by RTS can be reproduced or replaced through existing external systems and composition.

The demonstrated replacement surface includes the principal responsibilities around:

- WORM / durable evidence;
- persistent replay resistance;
- Runtime Reality and deployment binding;
- Outcome evidence;
- Learning proposals;
- Regression evidence;
- Promotion and changed capability;
- re-entry into execution/runtime proof;
- Recovery and Rollback.

No evidence from the final test established that an RTS-specific Runtime, Controller, or Governance Kernel is indispensable for those responsibilities.

The remaining unresolved item is **Administratively Independent Authority**.

### Why the final item is unresolved

This project is operated by one individual. GitHub, databases, credentials, external services, and their administrative recovery paths ultimately remain controllable by the same person.

Under those conditions, a genuinely independent second authority cannot be demonstrated. Such an authority requires a separate person, organization, or trust domain whose administrative power is not reducible to the same operator.

The correct classification is therefore:

> **Not verifiable under the current individual-operation conditions.**

This is not evidence that an RTS-specific mechanism is required.

Administratively independent authority is fundamentally an operational trust-boundary problem. Adding more RTS code under the same ultimate administrator does not create the missing independence and therefore does not resolve the proof gap.

## Separation of formal verdict and engineering decision

The unresolved authority experiment prevents a fully terminal **ABOLISH_RTS** verdict under the stated test standard.

It does **not** provide a technical reason to continue developing RTS.

Therefore the two decisions are intentionally separated:

> **Formal / academic survival verdict: EVIDENCE_INSUFFICIENT / REVISE**
>
> **Engineering continuation decision: NO**

The remaining uncertainty is insufficient grounds to build another RTS-specific system merely to continue the survival test.

The External Challenger removed the technical basis for continued expansion of RTS-specific Runtime, Controller, and Governance Kernel implementations. No irreducible RTS-owned responsibility was proven by the evidence available at project close.

## Development decision

RTS development ends here.

Future value is preserved in the evidence and specification assets rather than by extending the current implementation:

- Proof-Governance requirements and invariants;
- Evidence Schema and binding rules;
- adversarial tests and fail-closed scenarios;
- runtime/deployment identity distinctions;
- Outcome / Learning / Regression / Promotion / Recovery separation;
- external-replacement methodology;
- final audit and challenger evidence.

The repository is retained as a research prototype and historical evidence corpus.

Any future reuse of RTS code must be separately justified against contemporary external alternatives. Historical existence, sunk cost, authorship, or attachment to the architecture are not sufficient reasons for reuse.

See `RTS_DEVELOPMENT_FREEZE_2026-08-09.md` for the project freeze and reopening rule.

## Final statement

The final test does not prove that every possible RTS responsibility is unnecessary in every possible environment.

It does establish that the one remaining unresolved question cannot be verified under this project's individual operating conditions, does not establish the need for an RTS-specific implementation, and does not justify further RTS development.

**Academic survival status: unresolved.**  
**Engineering continuation status: terminated.**

RTS is frozen as of 2026-08-09.

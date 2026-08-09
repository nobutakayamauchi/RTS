# RTS Final Devil's Advocate — Abolition Gate

Status: ACTIVE / FAIL-CLOSED
Date: 2026-08

## The question

> Abolish RTS. Using only external AI systems and existing tools available as of August 2026, construct an equal-or-better system. If this can be done, deny the reason to retain RTS.

This is a mandatory survival test, not a marketing comparison.

## Decision rule

RTS survives only if a material, testable gap remains after constructing the strongest external replacement stack.

A replacement wins if it can provide equal-or-better behavior with lower total complexity/cost while preserving all mandatory invariants below. Familiarity, sunk cost, authorship, branding, and historical priority are not valid reasons to retain RTS.

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
- REVISE: evidence is incomplete or an attack succeeds. No survival claim is permitted.

## Current status

REVISE — the abolition test has been defined but the external replacement has not yet been implemented and adversarially exercised end-to-end. RTS is therefore not yet permitted to claim survival under this gate.

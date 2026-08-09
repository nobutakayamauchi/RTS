# RTS Final Existence Gate — 2026-08-09

Status: REVISE

This record exists to prevent RTS from exempting itself from its own proof standard.

## Fatal question

> Abolish RTS and reconstruct an equivalent-or-better system using only external AI and existing tools available as of 2026-08. If that can be done, deny the reason to keep RTS.

A PASS is forbidden unless RTS survives both the internal closure test and the external replacement test.

## Internal closure test

### Confirmed

Deployment Identity / Outcome Closure now establishes a fail-closed chain through source/material expectation, deployment observation, route/process/instance/artifact provenance, attestation quorum, authorized deployment identity, bound runtime observation, execution identity, and signed/replay-checked live outcome evidence.

The existing learning and promotion path remains conservative: simulated evidence is not promoted into external success, promotion eligibility remains separately gated, and target/adjacent writes are not automatically authorized.

### Blocking finding

The new live Outcome Closure is not yet a mandatory input to the Learning Proposal / Promotion path.

`learning_proposals/generation.py` still builds its proposal from the committed `SIMULATED_ONLY` outcome corpus:

- `outcome_evidence/examples/success.json`
- `outcome_evidence/examples/escalation.json`
- `outcome_evidence/examples/recovery.json`

The current code explicitly records that external success has not been observed and keeps human review / mutation authority blocked. This is fail-safe, but it means the claimed complete loop:

`authorized action -> actual runtime -> live outcome -> learning proposal -> regression -> promotion authority -> changed capability -> next authorized action`

is not yet implemented as one mandatory proof chain.

Therefore the internal final verdict is `REVISE`, not `PASS`.

## External replacement test

A strong replacement can be assembled from mature external components:

- agent execution / durable state / HITL / tracing / evaluation / deployment: LangGraph + LangSmith
- human deployment approvals and CI/CD gates: GitHub Actions + Environments
- policy authorization and decision audit: Open Policy Agent
- artifact provenance / signed attestations / supply-chain verification: GitHub Artifact Attestations + Sigstore / SLSA
- runtime telemetry and cross-service correlation: OpenTelemetry

This kills any RTS claim that those component capabilities are unique.

However, the surveyed external components expose separate evidence and governance surfaces. No surveyed native configuration was found that, without a bespoke integration layer, makes one fail-closed responsibility object mandatory across all of:

`policy authority -> exact artifact -> actual deployment/runtime identity -> exact execution -> outcome -> regression/learning -> promotion authority -> next execution`

A replacement can be built, but the integration/policy glue required to make those separate systems obey that invariant is itself the core problem RTS is attempting to package.

## Existence verdict

RTS is NOT justified as:

- a general agent platform;
- an observability product;
- an eval platform;
- a deployment platform;
- a provenance system;
- a policy engine;
- a generic human-approval workflow.

Existing products are already stronger in those individual categories.

RTS remains conditionally justified only if it can prove value as a small, vendor-neutral `Proof-Governed Responsibility Closure` layer / reference implementation that binds those categories into one mandatory evidence-and-authority chain.

If that mandatory cross-boundary closure can be reproduced with existing tools using only native configuration and no RTS-equivalent custom closure logic, RTS should be retired.

## Required correction before PASS

1. Introduce a governed live-outcome input contract for learning proposals.
2. Require proof-closed live outcome fingerprints when a proposal claims evidence from real execution.
3. Preserve `SIMULATED_ONLY` corpus support for research, but prohibit it from satisfying live-evidence requirements.
4. Carry deployment/runtime/execution/outcome fingerprints through regression and promotion decision records.
5. Require the post-promotion capability identity to enter the next execution proof chain.
6. Add adversarial tests proving that simulated, stale, mismatched, replayed, or unbound outcomes cannot influence live promotion authority.
7. Re-run this existence gate after the correction.

Until then, RTS must not claim a complete proof-governed evolution closure.

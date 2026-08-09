# RTS External Replacement Challenger — August 2026

Status: PHASE-1 ARCHITECTURE COMPLETE / FORMAL VERDICT STILL REVISE

This document attempts to abolish RTS using only externally available AI systems, standards, managed services, and existing open-source tools available in August 2026.

Historical priority, authorship, sunk cost, branding, and familiarity are excluded from the survival argument.

## Strongest external stack

### AI execution

- GitHub Copilot cloud agent / supported third-party coding agents for asynchronous coding work and pull requests.
- Copilot hooks for `preToolUse`, `postToolUse`, session-end, error, and audit interception.

Official references:
- https://docs.github.com/en/copilot/concepts/agents/hooks
- https://docs.github.com/en/copilot/concepts/agents/about-third-party-coding-agents

### Source / policy / human authority

- Git / GitHub immutable commit history.
- GitHub rulesets with required status checks and signed commits.
- GitHub protected environments with required reviewers, prevention of self-review, and administrator bypass disabled.
- GitHub custom deployment protection rules when third-party readiness evidence must gate a transition.

Official references:
- https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets
- https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments

### Build and artifact provenance

- GitHub Artifact Attestations for build provenance tied to workflow, repository, environment, commit SHA, and triggering event.
- Sigstore Cosign / in-toto attestations for signed statements and policy verification.
- Sigstore Policy Controller to reject Kubernetes deployment of artifacts that fail attestation policy.
- in-toto layouts/links to bind authorized functionaries, materials, products, commands, and supply-chain steps.

Official references:
- https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations/use-artifact-attestations
- https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations/enforce-artifact-attestations
- https://docs.sigstore.dev/cosign/verifying/attestation/
- https://in-toto.io/docs/getting-started/

### Runtime identity and actual route reality

- SPIFFE/SPIRE node and workload attestation for process-level workload identity.
- Kubernetes EndpointSlice as the control-plane source of truth for active Service backends.
- Kubernetes PodStatus / ContainerStatus for container ID and resolved image ID.
- Immutable ConfigMaps and explicit config digests/resource versions for configuration identity.

Official references:
- https://spiffe.io/docs/latest/spire-about/spire-concepts/
- https://kubernetes.io/docs/concepts/services-networking/endpoint-slices/
- https://kubernetes.io/docs/reference/kubernetes-api/core/config-map-v1/

### Policy decision / fail-closed authorization

- Open Policy Agent / Rego to evaluate arbitrary structured evidence and deny transitions unless all required bindings are present and valid.

Official reference:
- https://www.openpolicyagent.org/docs

### Execution trace / evaluation / regression

- OpenTelemetry-compatible traces for execution correlation.
- LangSmith production tracing, online evaluation, datasets, offline regression, human/code/LLM evaluators, and production-trace-to-dataset feedback loops.

Official references:
- https://docs.langchain.com/langsmith/evaluation
- https://docs.langchain.com/langsmith/evaluation-concepts

### Failure and audit retention

- Signed outcome statements / attestations.
- Append-only or WORM retention using Amazon S3 Object Lock in COMPLIANCE mode when evidence deletion must be prevented even from account administrators/root during the retention period.

Official reference:
- https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock.html

## Candidate external proof chain

```text
Protected Git source / policy
  -> GitHub build provenance + in-toto materials/products
  -> Sigstore admission verification
  -> Kubernetes deployed image/config identity
  -> SPIRE workload identity
  -> EndpointSlice active route set + Pod/Container runtime identity
  -> OPA authorization decision
  -> OpenTelemetry trace_id / execution_id
  -> signed outcome attestation
  -> WORM evidence retention
  -> LangSmith failure/success/recovery evaluation
  -> learning/change proposal as PR
  -> regression dataset + CI/evaluation evidence
  -> GitHub protected environment independent approval
  -> newly signed capability artifact/config
  -> deployment attestation
  -> re-entry through SPIRE / route / OPA / execution chain
```

## Mandatory invariant comparison

| RTS abolition invariant | External mechanism | Phase-1 assessment |
|---|---|---|
| Unsupported claim withheld | OPA/Rego deny without required evidence | REPRODUCIBLE |
| Code existence != runtime evidence | SPIRE + Kubernetes runtime state | REPRODUCIBLE |
| Revision equality != runtime reality | image digest + config identity + runtime workload identity | REPRODUCIBLE |
| Active route/process/instance/artifact reality | EndpointSlice + PodStatus + SPIRE + attestation | REPRODUCIBLE, integration required |
| Material match != authority | OPA + protected environment | REPRODUCIBLE |
| Independent trust cannot be self-declared | SPIRE trust anchors / external keys / policy-bound identities | REPRODUCIBLE |
| Runtime bound to authorized deployment | shared signed digests + OPA transition policy | REPRODUCIBLE, binding policy required |
| Outcome bound to same execution | trace/execution id + signed outcome predicate + OPA | REPRODUCIBLE, binding policy required |
| Success != promotion | protected environment / required check policy | REPRODUCIBLE |
| Learning != authority | PR/eval evidence separate from protected promotion | REPRODUCIBLE |
| Failure/recovery/rejection preserved | tracing + signed evidence + WORM retention | REPRODUCIBLE |
| Scope-limited human authority | environment-specific reviewers + IAM + OPA | REPRODUCIBLE |
| Governance changes governed too | rulesets/CODEOWNERS/status checks on policy repository | REPRODUCIBLE |
| Unproved physical truth remains unproved | explicit trust-root and substrate boundaries | REPRODUCIBLE |

## First brutal finding

No individual RTS mechanism is currently sufficient as a survival argument.

The August 2026 external ecosystem can replace the large majority of RTS mechanism code with stronger and more mature components, especially workload identity, software provenance, admission enforcement, policy decisions, tracing/evaluation, immutable retention, and independent deployment approval.

Therefore RTS MUST NOT justify its continued size by claiming ownership of those mechanisms.

## The remaining question

The unresolved candidate for irreducible RTS value is the cross-tool semantic closure:

```text
one canonical identity/binding model
+ one fail-closed transition model
+ responsibility semantics across execution, outcome, failure, learning, promotion, and re-entry
```

The decisive test is whether this can be expressed as a thin configuration/policy layer over the external stack, or whether implementing it recreates a substantively equivalent RTS controller/evidence layer.

### If the glue is thin

If a bounded Rego/in-toto/GitHub configuration can enforce the complete chain without a custom stateful governance runtime, the correct verdict trends toward:

`REDUCE_RTS`

RTS should become a small reference architecture / invariant set and stop reimplementing mature external mechanisms.

### If the glue becomes a new runtime

If the challenger requires a custom controller to canonicalize identities, persist transition state, reject replay/TOCTOU, correlate outcome evidence, govern failure paths, gate learning/promotion, and self-govern policy changes, then the challenger has rebuilt RTS under another name.

The correct verdict then trends toward:

`RETAIN_RTS`

but only for that irreducible closure layer.

## Current formal verdict

`REVISE`

Phase 1 establishes architectural feasibility only. The external replacement has not yet passed the required adversarial end-to-end implementation test.

Next test: implement the closure using only thin OPA/Rego, in-toto/Sigstore statements, and GitHub-native protection semantics. Measure how much custom semantic/state machinery is required. If that layer remains small, deny the need for the current RTS implementation surface.
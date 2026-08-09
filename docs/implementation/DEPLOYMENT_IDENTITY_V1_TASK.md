# Deployment Identity — Completion Contract through v3

## Problem

RTS must not classify source presence, matching revisions, or stale attestations as runtime reality.

Governing invariants:

```text
Code existence != runtime evidence.
Revision equality != runtime reality.
```

## v1 proof boundary

v1 established the minimum runtime subject: service/unit, working directory, executable/module, active surface, deployed revision, expected source revision, and timezone-aware observation time. Missing evidence failed closed.

## Devil's Advocate v2

v2 closed three immediate bypasses:

- self-declared observer trust;
- stale/replayed evidence and bounded TOCTOU;
- runtime observation bypass of Deployment Identity.

It requires an externally supplied trusted observer set, observer/session identity, freshness reference/window, and fingerprint/session/time binding into Runtime Observation.

## Devil's Advocate v3

v3 attacks the assumption that a matching commit implies an identical runtime.

The expectation is now externally supplied and contains:

1. source revision;
2. expected artifact digest;
3. expected configuration fingerprint;
4. expected environment fingerprint.

The runtime observation additionally requires:

1. deployed artifact digest;
2. runtime configuration fingerprint;
3. runtime environment fingerprint;
4. exact `CLEAN` source-tree state;
5. enumerated runtime instances;
6. enumerated active-route instance ids.

Every instance reachable from the active route MUST match the external expectation across revision, artifact, config, and environment. Unknown route targets, duplicate identities, dirty source state, mixed routed workers, or material mismatch fail closed.

## Evidence chain

```text
Expected Source / Material
    -> Trusted + Fresh Deployment Observation
    -> Active Route Instance Set
    -> Observation + Expectation Fingerprints
    -> Session/Time-Bound Runtime Observation
    -> Outcome Evidence
```

## Acceptance criteria

- source existence alone cannot establish runtime identity;
- a matching revision with dirty source state fails closed;
- a matching revision with a different artifact fails closed;
- config/environment drift fails closed;
- the expected revision/material cannot be self-declared by the runtime observation;
- every routed worker is measured against the same expectation;
- an unknown route target fails closed;
- a heterogeneous routed worker set fails closed;
- runtime observation must bind both observation and expectation fingerprints;
- replay/future evidence and oversized TOCTOU windows fail closed;
- dedicated and full-repository test suites pass.

## Remaining boundary

v3 remains an attestation validator, not cryptographic host truth. A trusted observer may still lie or be compromised. Reverse-proxy/service-mesh discovery, privileged host collection, signed evidence, key management, TPM/container attestation, and secret-safe material measurement require separate governed implementation and review.

Deployment Identity authorizes runtime classification only. It does not prove outcome correctness and does not authorize deployment, mutation, publication, provider execution, or capability promotion.

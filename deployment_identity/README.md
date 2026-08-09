# Deployment Identity v5

Deployment Identity v5 adds independently sourced collector provenance before runtime classification can be authorized.

## Invariants

```text
Code existence != runtime evidence.
Revision equality != runtime reality.
Material match != authorization.
Single-observer trust != proof quorum.
Attestor count != independent observation.
Shared observation path != independent provenance.
```

A signed quorum over one observation is necessary but no longer sufficient. RTS now requires independent measured provenance for the route, process, routed instance set, and artifact.

## Provenance requirement

At least two independent `trust_domain` paths are required by default. Every domain must independently cover:

```text
route -> process -> instance -> artifact
```

Every provenance record is signed by an externally trusted collector key and binds the exact deployment observation fingerprint, expectation fingerprint, observation session and issue time. Every trust domain must cover every routed instance. Artifact measurements must agree with the authorized deployment material.

The following fail closed:

- two collectors in the same trust domain pretending to be independent;
- missing route/process/instance/artifact stages;
- failure to cover every routed worker;
- provenance for another observation, expectation, or session;
- stale/future records;
- unknown collectors or forged signatures;
- artifact measurement drift.

## Proof chain

```text
Expected Source / Material
  -> Fresh Deployment Material Observation
  -> Active Route Instance Set
  -> Non-authorizing Material Proof
  -> Signed Attestation Quorum
  -> Independent Collector Provenance
       route -> process -> instance -> artifact
       across >= 2 trust domains
  -> Authorized Deployment Identity
  -> fingerprint/session/time-bound Runtime Observation
  -> Outcome Evidence
```

## Security boundary

v5 proves authenticated provenance diversity and consistency. It still does not prove physical truth against a substrate capable of deceiving every independent collector. Hardware-backed attestation, platform-native measured identity, privileged discovery, key lifecycle management and secret-safe environment measurement remain separately governed extensions.

The verifier itself remains deterministic and performs no network, shell, provider, deployment, or repository mutation.

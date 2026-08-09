# Deployment Identity v5

Deployment Identity v5 adds independently sourced collector provenance before runtime classification can be authorized.

## Invariants

```text
Code existence != runtime evidence.
Revision equality != runtime reality.
Material match != authorization.
Single-observer trust != proof quorum.
Attestor count != independent observation.
Collector-declared domain != trusted independence.
Shared observation path != independent provenance.
Partial artifact coverage != runtime proof.
```

A signed quorum over one observation is necessary but no longer sufficient. RTS requires independent measured provenance for route, process, every routed instance, and every routed artifact.

## Externally bound independence

Collector independence is policy data, not collector self-description. The caller must provide both:

- an external collector keyring; and
- an external `collector_id -> trust_domain` map.

A signed record whose claimed `trust_domain` disagrees with that external map fails closed. Reusing one `source_locator` across separate trust domains also fails closed.

## Provenance requirement

At least two policy-bound trust domains are required by default. Every domain must independently cover:

```text
route -> process -> instance -> artifact
```

Route measurements must identify the active route and complete routed-worker set. Process measurements must match the active executable/module. Every trust domain must measure every routed instance and the artifact digest for every routed instance.

Every record also binds the exact deployment observation fingerprint, expectation fingerprint, observation session and issue time.

## Proof chain

```text
Expected Source / Material
  -> Fresh Deployment Material Observation
  -> Active Route Instance Set
  -> Non-authorizing Material Proof
  -> Signed Attestation Quorum
  -> Externally Bound Independent Collector Provenance
       route -> process -> every instance -> every artifact
       across >= 2 policy trust domains
  -> Authorized Deployment Identity
  -> fingerprint/session/time-bound Runtime Observation
  -> Outcome Evidence
```

## Security boundary

v5 proves authenticated provenance diversity, externally anchored independence, and complete routed-instance/artifact coverage. It still does not prove physical truth against a lower substrate capable of deceiving every independent collector. Hardware-backed attestation, platform-native measured identity, privileged discovery, key lifecycle management and secret-safe environment measurement remain separately governed extensions.

The verifier itself remains deterministic and performs no network, shell, provider, deployment, or repository mutation.

# Deployment Identity v6

Deployment Identity v6 closes the live proof chain from authorized deployment and runtime observation into signed outcome evidence.

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
Runtime proof != outcome proof.
Matching execution label != proof closure.
Unsigned outcome != authorized evidence.
Replayed outcome != new evidence.
```

## Live Outcome Closure

A runtime result becomes eligible as live Outcome Evidence only after the runtime observation has already been bound to an authorized Deployment Identity.

The Outcome Closure verifier then requires the exact same:

- deployment observation fingerprint;
- external expectation fingerprint;
- observation session id;
- runtime observation fingerprint; and
- execution id.

The supplied runtime observation is hashed again and must match the fingerprint already preserved by the Runtime Binding result. This prevents an outcome from being attached to a runtime record that was changed after authorization.

Outcome Evidence also requires an externally trusted `outcome_source_id` signature, an unused `evidence_id` relative to the caller-supplied evidence ledger, and an outcome timestamp within the governed execution window. Different run/session/deployment/runtime fingerprints, forged or unknown sources, replayed evidence ids, and temporally impossible outcomes fail closed.

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
  -> execution-bound Runtime Observation fingerprint
  -> signed, replay-checked Outcome Evidence
  -> Proof-Closed Outcome
```

## Existing Outcome Evidence Corpus boundary

The existing `outcome_evidence/` package remains a `SIMULATED_ONLY` research corpus and remains permanently non-promoting. v6 does not reinterpret those fixtures as external or production success. The live Outcome Closure is a separate verification layer and does not weaken the corpus boundary.

## Security boundary

v6 proves cryptographic origin from a policy-trusted outcome source and deterministic binding to one already-authorized runtime execution. It does **not** prove physical truth if the trusted outcome source itself or a lower substrate is compromised. Hardware-backed/platform-native measurement and external real-world success verification remain separately governed concerns.

Replay rejection depends on the caller supplying the current accepted evidence-id ledger. The verifier is deterministic and read-only; it does not mutate that ledger itself.

# Deployment Identity v4

Deployment Identity establishes which runtime material and route set were active before RTS classifies runtime behavior, then requires independent signed attestations before that classification authority is granted.

## Invariants

```text
Code existence != runtime evidence.
Revision equality != runtime reality.
Material match != authorization.
Single-observer trust != proof quorum.
```

A matching Git revision is insufficient. Runtime identity also depends on artifact, configuration, environment, source-tree cleanliness, and the instances reachable from the active route. Even when all of those match, the lower-level material proof is deliberately non-authorizing until a signed attestation quorum is verified.

## External expectation

The verifier requires a caller-supplied deployment expectation containing:

- `source_revision`
- `artifact_digest`
- `config_fingerprint`
- `environment_fingerprint`

Expected truth is not accepted from the runtime observation itself.

## Signed attestation quorum

Final runtime classification authority requires at least two distinct trusted attestors by default. Each attestation signs the exact:

- deployment observation fingerprint;
- external expectation fingerprint;
- observation session id;
- attestation issue time.

The current deterministic implementation uses HMAC-SHA256. The attestation keyring is supplied externally; no attestation secret is stored in this repository.

A single attestor, duplicated attestor id, forged signature, unknown attestor, stale/future attestation, different observation, different expectation, or different session fails closed.

## Authorization split

`establish_deployment_identity(...)` performs the material proof only. A successful material match returns:

```text
material_match_verified: true
runtime_classification_authorized: false
reason: RUNTIME_MATERIAL_MATCH_ATTESTATION_REQUIRED
```

`establish_attested_deployment_identity(...)` verifies the independent signed quorum over that exact material proof. Only then may it emit:

```text
runtime_classification_authorized: true
reason: SIGNED_MULTI_ATTESTOR_RUNTIME_MATERIAL_MATCH
```

A Runtime Observation refuses to bind to a raw material proof that has not crossed the attestation boundary.

## Proof chain

```text
Expected Source / Material
  -> Fresh Deployment Material Observation
  -> Active Route Instance Set
  -> Non-authorizing Material Proof
  -> Independent Signed Attestation Quorum
  -> Authorized Deployment Identity
  -> fingerprint/session/time-bound Runtime Observation
  -> Outcome Evidence
```

## CLI

```bash
python -m deployment_identity.cli verify \
  --observation path/to/observation.json \
  --expectation path/to/expected-deployment.json \
  --attestations path/to/attestations.json \
  --attestation-keyring path/to/keyring.json \
  --trusted-observer-id observer-prod-01 \
  --reference-time 2026-08-09T17:00:10+09:00 \
  --min-attestors 2 \
  --max-age-seconds 300
```

## Security boundary

v4 proves authenticated agreement by independent policy-recognized attestors over one exact deployment claim. It does **not** prove physical host truth against colluding or jointly compromised collectors.

The next hardening layer is independently collected route/process provenance and stronger measured attestation such as container/image platform evidence or hardware-backed mechanisms where available. Privileged collection, key lifecycle management, Kubernetes/service-mesh discovery, secret-safe environment measurement, and hardware roots of trust remain separately governed work.

The verifier itself remains deterministic and performs no network, shell, provider, deployment, or repository mutation.

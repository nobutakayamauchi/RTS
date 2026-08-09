# Deployment Identity v3

Deployment Identity establishes which runtime material and route set were actually active before RTS classifies runtime behavior.

## Invariant

```text
Revision equality != runtime reality.
```

A matching Git commit is insufficient. Runtime identity also depends on the built artifact, configuration, environment, source-tree cleanliness, and the actual instances reachable from the active route.

## External expectation

The verifier now requires a caller-supplied `expected_deployment` object containing:

- `source_revision`
- `artifact_digest`
- `config_fingerprint`
- `environment_fingerprint`

These values are not accepted from the runtime observation itself as the expected truth.

## Required runtime material

The observation must include:

- service/unit, working directory, executable/module, active route surface;
- deployed revision and artifact digest;
- runtime config and environment fingerprints;
- `source_tree_state`, which must be exactly `CLEAN`;
- trusted observer/session/time evidence;
- a non-empty `runtime_instances` set;
- a non-empty `active_route_instance_ids` set.

Every instance reachable through the active route must match the externally expected revision, artifact, config, and environment. Unknown route targets, duplicate instance identities, dirty source state, mixed blue/green workers, or material drift fail closed.

An observed but non-routed stale worker does not define the active route reality. The route set is the classification boundary.

## Proof chain

The Runtime Observation must bind both the observation fingerprint and the external expectation fingerprint, plus the same observation session and bounded time window.

```text
Expected Source/Material
  -> Trusted + Fresh Deployment Material Observation
  -> Active Route Instance Set
  -> observation + expectation fingerprints
  -> Runtime Observation
  -> Outcome Evidence
```

## Commands

```bash
python -m deployment_identity.cli verify \
  --observation path/to/observation.json \
  --expectation path/to/expected-deployment.json \
  --trusted-observer-id observer-prod-01 \
  --reference-time 2026-08-09T17:00:10+09:00 \
  --max-age-seconds 300
```

## Security boundary

v3 still does **not** prove that the trusted observer or host cannot lie. It validates an externally anchored expectation against a fresh, policy-trusted runtime attestation and route set.

Cryptographic host attestation, signed collector evidence, secret-safe config/environment measurement, reverse-proxy discovery, Kubernetes/service-mesh discovery, and privileged live-host collection remain separately governed work.

The verifier is deterministic, standard-library-only, read-only, and performs no network, shell, provider, deployment, or repository mutation.

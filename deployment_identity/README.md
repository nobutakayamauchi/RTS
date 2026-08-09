# Deployment Identity v2

Deployment Identity establishes what code and execution surface were actually active at observation time before RTS classifies runtime behavior.

## Invariant

```text
Code existence != runtime evidence.
```

A repository file, branch, or commit is source evidence only. Runtime implementation classification is forbidden until deployed identity is established from explicit, trusted, fresh observations.

## Required deployment observation

A v2 observation identifies:

- `service_unit`
- `working_directory`
- `executable_or_module`
- `active_route_surface`
- `deployed_revision`
- `source_revision`
- `observer_id`
- `observation_session_id`
- `observed_at`

The verifier also requires an external trust anchor (`trusted_observer_ids`), a caller-supplied `reference_time`, and a bounded freshness window. An observation cannot make itself trusted by merely naming an observer.

## Fail-closed rules

Deployment identity is established only when:

1. every required field is present exactly, without normalization of surrounding whitespace;
2. `observer_id` is in the externally supplied trusted observer set;
3. the observation is not future-dated or older than the allowed freshness window;
4. `deployed_revision == source_revision` exactly.

Otherwise runtime classification remains unauthorized.

## Runtime observation binding

An established deployment proof is not enough by itself to classify a later runtime observation. The runtime observation must carry:

- the exact Deployment Identity observation fingerprint;
- the same `observation_session_id`;
- a timezone-aware observation timestamp within the configured binding window.

This closes the direct proof-chain bypass and bounds the TOCTOU interval:

```text
Source Identity
  -> trusted + fresh Deployment Identity
  -> fingerprint/session-bound Runtime Observation
  -> Outcome Evidence
```

## Commands

```bash
python -m deployment_identity.cli verify \
  --observation path/to/observation.json \
  --trusted-observer-id observer-prod-01 \
  --reference-time 2026-08-09T17:00:10+09:00 \
  --max-age-seconds 300

python -m deployment_identity.cli fingerprint --observation path/to/observation.json
```

## Security boundary

v2 deliberately does **not** claim cryptographic proof that a host observation is truthful. `trusted_observer_ids` is a policy trust anchor supplied from outside the observation. Privileged live-host collection, signatures/attestation, key management, route-to-process verification, container/image/config/environment measurement, and distributed deployment identity remain separately governed work.

Therefore v2 proves: **a trusted policy-recognized observer supplied a fresh, internally consistent deployment attestation and a later runtime observation is explicitly bound to it.** It does not prove the physical host cannot lie.

The verifier remains deterministic, standard-library-only, read-only, and performs no network, shell, provider, deployment, or repository mutation.

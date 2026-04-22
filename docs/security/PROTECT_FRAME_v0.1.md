# Protect Frame v0.1

## Purpose
Protect Frame v0.1 is a lightweight boundary-audit layer added beside RTS Core.
It does not replace RTS recording behavior; it clarifies what must be protected,
where boundaries exist, and how current state can be verified and reconstructed later.

## Scope
This version defines only:
- a minimal protected asset registry,
- a minimal secret scope registry,
- a minimal trust zone definition,
- and an offline verification script for structural consistency.

It is intentionally insert-only and avoids operational behavior changes in RTS Core.

## Non-Goals
Protect Frame v0.1 does **not** implement:
- active access enforcement,
- runtime blocking or isolation,
- automated incident generation,
- SIEM-style aggregation,
- production intrusion detection,
- secret storage backends.

## Protected Assets
Assets are tracked in `security/asset_registry.yaml` with normalized fields:
- `asset_id`, `category`, `criticality`, `owner`, `notes`, `zone`.

The registry is intended as a practical initial baseline for real operation,
while still keeping sensitive implementation detail out of this layer.

## Trust Zones
Zones are tracked in `security/trust_zones.yaml` and separate operational surfaces:
- daily
- development
- admin
- external_ai
- public_surface

Each zone documents allowed assets, forbidden crossings, and notes for reviewers.
The objective is explicit boundary readability rather than hard enforcement.

## Secret Scope Rules
Secret scope entries are tracked in `security/secret_scope_registry.yaml`.

Design rules in v0.1:
- avoid omnibus credentials,
- prefer short-lived secrets,
- separate credentials by usage context,
- document expected blast radius on leak,
- maintain explicit status for lifecycle review.

## Verification Rules
`scripts/security/verify_protect_frame.py` verifies:
1. required Protect Frame files exist,
2. all registries are valid YAML and loadable,
3. each registry entry contains required keys,
4. selected value constraints and zone consistency rules.

The script is non-mutating and returns non-zero on any violation.

## Operational Notes
- Initial registries are scaffolded for real use and periodic review.
- Secrets are represented as metadata and scope intent, not secret values.
- Verification currently checks structural consistency and constrained value validity.
- CI and incident linkage are intentionally deferred to later phases.

## Incident Reconstruction Intent
Protect Frame v0.1 is designed for post-event reconstruction support.
By preserving explicit boundary and scope metadata, reviewers can reconstruct
which asset, secret scope, and zone relationships were in effect at validation time.

Future versions may connect this scaffold to ledgers, incident packs, and workflow
automation, but v0.1 keeps those integrations out of scope.

# 新RTS（仮称） — Continuity / Recovery v0

Status: `ADOPTED_CONTRACT / REFERENCE_OCCUPANTS`

This component exists for one reason:

> A critical external substrate may disappear, be corrupted, lock the operator out, or become untrustworthy. 新RTS（仮称） must still preserve enough trusted Tier-0 state to reconstruct its critical responsibilities somewhere else.

It is **not** a new cloud, source host, key vault, scheduler, database, or backup platform.

## Hard invariants

Only the high-value invariants are base-system requirements:

1. **Safety** — hostile/tampered backup material must not be silently trusted or executed.
2. **Reproducibility** — Tier-0 state must reconstruct to the same committed Git refs/history and declared provider metadata.
3. **Recoverability** — a backup is not proven until a fresh reconstruction drill succeeds.
4. **Exitability** — critical state needs a provider-neutral representation, not only a provider-native copy.
5. **Failure-domain separation** — protected backup material needs more than one recovery path; one failed/corrupt path must not poison another.

Everything else is situational policy. Do not bloat the base system to chase a fictional universal 100% score.

## Priority / discard policy

### Tier 0 — must survive

- committed Git objects and refs containing the current system, invariants, specs and regression capsules;
- provider-only metadata explicitly declared necessary for governance/reconstruction (for example issues/PR records or repository rules);
- integrity manifests, recovery receipts and key-epoch/recipient identity metadata;
- access to separately held recovery identities/keys needed to decrypt protected backups.

Secret values themselves are **not** placed into provider metadata exports. Recovery secrets belong to a separate trust boundary.

### Tier 1 — preserve when useful

- expensive-to-regenerate analysis results;
- selected build/release artifacts;
- derived indexes or reports.

Tier 1 loss may cost time/money but must not make Tier-0 reconstruction impossible.

### Tier 2 — disposable

- caches;
- downloaded dependencies that can be re-fetched;
- temporary build/work directories;
- cheap derived state.

Do not turn Tier 2 into a reason to build another platform.

## Provider-neutral Git capture

`continuity.py capture` creates a Git bundle plus a continuity manifest.

It fails closed on known partial-custody states:

- dirty/untracked working tree;
- shallow clone;
- partial/promisor clone;
- Git submodules without a separate export;
- Git LFS declarations without a separate export;
- source Git object corruption.

A self-consistent *partial* backup is more dangerous than an explicit failure, so these states are rejected rather than silently omitted.

## Provider metadata export contract

Git does not preserve provider-only state such as issue/PR conversations or repository/ruleset settings.

新RTS（仮称） does not own provider scrapers. An external exporter may supply a directory containing `EXPORT_ATTESTATION.json`:

```json
{
  "schema": "new-rts-provisional-platform-export-attestation/v0",
  "producer_id": "provider-exporter:...",
  "captured_at": "...",
  "secret_values_excluded": true,
  "scope": ["issues", "pull_requests", "repository_rules"]
}
```

The workload declares which scopes are Tier 0. Missing declared scopes fail closed. This keeps provider adapters replaceable.

## Fresh recovery drill

`continuity.py drill`:

1. verifies hashes/manifests;
2. verifies the Git bundle;
3. clones it into a fresh mirror repository;
4. runs `git fsck --full`;
5. requires restored refs to equal captured refs;
6. verifies optional platform-export content;
7. **does not execute restored project code**.

`BACKUP_EXISTS != RECOVERY_PROVEN`

## Encryption and alternate recovery

Encryption remains externalized to the Encrypted Cloud Custody occupant (GnuPG/OpenPGP). The producer receives public recovery keys; private identities remain outside the producer/provider trust boundary.

The adoption drill generated two real recovery identities, bound producer trust to their exact full fingerprints, encrypted the continuity capsule, destroyed the primary replica domain, recovered ciphertext only from the alternate domain, decrypted using only the alternate private identity, and completed a fresh Git reconstruction. A wrong unrelated recovery identity failed as required.

## Replica contract

`replicate` is a thin local reference adapter for an already protected/opaque artifact. It requires at least two declared failure-domain IDs and non-overlapping local paths, verifies SHA-256 after each copy, and writes a receipt.

Important limitation:

> Two labels or two paths do not prove physical/provider independence.

Production independence requires external evidence that the domains really differ (provider/account/device/region/control plane as appropriate). The local adapter tests failover semantics without inventing a cloud platform.

## What is deliberately cut

- custom cryptography;
- custom object store;
- custom source host;
- custom secret vault;
- always-on backup daemon;
- mandatory one-size-fits-all retention/freshness schedule;
- automatic preservation of every Tier-1/Tier-2 artifact.

Freshness, RPO, retention, offline/WORM and provider/geographic separation become hard only when the current workload declares them critical.

## Current evidence

Observed adoption evidence on PR #318 before the final record-only update:

- provider-neutral capture/drill on the actual RTS PR repository: `PASS`;
- Git bundle: 5,701,092 bytes;
- captured/restored refs: 103;
- fresh mirror `git fsck`: `PASS`;
- 10 Continuity Meteor regressions: `PASS`;
- real GPG alternate-domain recovery: `PASS`;
- wrong recovery identity: `BLOCK` as required;
- inherited Cloud Custody Meteor suite: `PASS`;
- Unicode Guard and independent Semgrep: `PASS`.

## DARWIN rule

The **contract** is adopted. The Python/file/GnuPG/GCS occupants have no permanent implementation right.

A challenger may replace any occupant if it preserves the hard invariants and all inherited death causes with equal-or-better evidence and lower burden.

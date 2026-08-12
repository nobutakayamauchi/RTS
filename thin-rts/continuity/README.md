# 新RTS（仮称） — Continuity / Recovery v0

Status: `METEOR_CANDIDATE / NOT_YET_PROMOTED`

This component exists for one reason:

> A critical external substrate may disappear, be corrupted, lock the operator out, or become untrustworthy. 新RTS（仮称） must still preserve enough trusted state to reconstruct its Tier-0 responsibilities somewhere else.

It is **not** a new cloud, source host, key vault, scheduler, database, or backup platform.

## What matters most

Hard invariants are intentionally few:

1. **Safety** — hostile/tampered backup material must not be silently trusted or executed.
2. **Reproducibility** — Tier-0 state must reconstruct to the same committed Git refs/history and declared provider metadata.
3. **Recoverability** — a backup is not PASS until a fresh reconstruction drill succeeds.
4. **Exitability** — critical state must have a provider-neutral representation, not only a provider-native copy.
5. **Failure-domain separation** — protected backup material must have more than one recovery path, and one failed/corrupt path must not poison the other.

Everything else is situational and may be dropped when cost/complexity exceeds value.

## Priority / discard policy

### Tier 0 — must survive

- committed Git objects and refs containing the current system, invariants, specs and regression capsules;
- provider-only metadata explicitly declared necessary for governance/reconstruction (for example issues/PR records or repository rules);
- integrity manifests, recovery receipts and key-epoch/recipient identity metadata;
- the ability to obtain the separately held recovery identity/key needed to decrypt the protected backup.

Secret values themselves are **not** placed into the provider metadata export. Recovery secrets belong to a separate trust boundary.

### Tier 1 — preserve when useful

- expensive-to-regenerate analysis results;
- selected build/release artifacts;
- derived indexes or reports.

Tier 1 loss may hurt time/cost but must not make Tier-0 reconstruction impossible.

### Tier 2 — disposable

- caches;
- downloaded dependencies that can be re-fetched;
- temporary build/work directories;
- cheap derived state.

Do not turn Tier 2 into a reason to build another platform.

## Provider-neutral Git capture

`continuity.py capture` creates a Git bundle plus a continuity manifest.

Before capture it fails closed on known partial-custody states:

- dirty/untracked working tree;
- shallow clone;
- partial/promisor clone;
- Git submodules without a separate export;
- Git LFS declarations without a separate export;
- source Git object corruption.

A self-consistent *partial* backup is more dangerous than an explicit failure, so these cases are rejected rather than silently omitted.

## Provider metadata export contract

Git alone does not preserve provider-only state such as issue/PR conversations or repository/ruleset settings.

新RTS（仮称） does not own provider scrapers. Instead, an external exporter may supply a directory containing `EXPORT_ATTESTATION.json`:

```json
{
  "schema": "new-rts-provisional-platform-export-attestation/v0",
  "producer_id": "provider-exporter:...",
  "captured_at": "...",
  "secret_values_excluded": true,
  "scope": ["issues", "pull_requests", "repository_rules"]
}
```

The caller decides which scopes are Tier 0 for the current provider. If a required scope is absent, capture fails closed.

This keeps the continuity contract stable while provider adapters remain replaceable.

## Fresh recovery drill

`continuity.py drill`:

1. verifies hashes and manifests;
2. verifies the Git bundle;
3. clones it into a new mirror repository;
4. runs `git fsck --full`;
5. requires the restored refs to equal the captured refs;
6. verifies optional platform-export content;
7. **does not execute restored project code**.

`BACKUP_EXISTS != RECOVERY_PROVEN`

## Encryption and recovery identity

Encryption remains externalized to the existing encrypted Cloud Custody candidate (GnuPG/OpenPGP). The producer receives public recovery keys; private recovery identities remain outside the producer/provider trust boundary.

The continuity integration test performs a real two-recipient GPG encryption, destroys the primary storage domain, recovers ciphertext only from the alternate domain, decrypts using only the alternate recovery identity, and runs the fresh Git reconstruction drill.

## Replica contract

`replicate` is a thin local reference adapter for an already protected/opaque artifact. It requires at least two declared failure-domain IDs and non-overlapping local paths, verifies SHA-256 after each copy, and writes a receipt.

Important limitation:

> Two labels or two paths do not prove physical/provider independence.

Production independence requires external evidence that the domains really differ (provider/account/device/region/control plane as appropriate). The local adapter exists to test failover semantics without inventing a cloud platform.

## What is deliberately cut

- custom cryptography;
- custom object store;
- custom source host;
- custom secret vault;
- always-on backup daemon;
- mandatory one-size-fits-all retention/freshness schedule;
- automatic preservation of every Tier-1/Tier-2 artifact.

Freshness/retention are policy inputs because acceptable recovery age depends on the workload. A stale backup may be degraded evidence, but emergency recovery should not destroy the last surviving copy merely because a universal timer expired.

## `/goal` adoption rule

The **contract** may be promoted after inherited Cloud Custody regressions plus Continuity Meteor attacks and the real alternate-domain GPG recovery drill are green.

Concrete Python/file adapters remain replaceable DARWIN occupants. A better external tool may replace them if it preserves all inherited death causes and the same Tier-0 evidence contract.

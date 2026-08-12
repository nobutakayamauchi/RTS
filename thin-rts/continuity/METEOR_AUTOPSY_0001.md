# METEOR AUTOPSY 0001 — Continuity / Recovery Attack Surface

Status: `ATTACK_CORPUS_FROZEN / AWAITING_CI`

Target: 新RTS（仮称） Continuity / Recovery v0 candidate, composed with inherited Encrypted Cloud Custody v0.

## Raison d'être attack

Candidate responsibility survives only if this narrower statement remains necessary:

> Critical state must be able to leave a failed external substrate and reconstruct elsewhere with bounded integrity evidence.

Killed responsibilities:

- build a new cloud;
- build a new source host;
- build custom cryptography;
- build a custom key vault;
- preserve every artifact forever;
- define one universal backup interval for every workload.

## Frozen Meteor attacks

### M-01 — dirty working tree

A committed-history backup that silently drops uncommitted/untracked Tier-0 work is a false PASS.

Required result: `BLOCK`.

### M-02 — shallow or partial/promisor clone

A bundle created from missing history/objects can be internally consistent but incomplete.

Required result: `BLOCK`.

### M-03 — Git LFS or submodule external state

A repository bundle can preserve only pointers/references while real content lives elsewhere.

Required result: `BLOCK unless separately exported`.

### M-04 — provider-only metadata omitted

Issues, PR decisions, rulesets/settings and similar provider state are not contained in ordinary Git history.

Required result: caller may declare provider scopes Tier 0; missing declared scopes => `BLOCK`.

### M-05 — secret material contaminates metadata export

A convenient provider export must not turn backup custody into credential exfiltration.

Required result: exporter must explicitly attest `secret_values_excluded=true`; otherwise `BLOCK`.

### M-06 — bundle / manifest / provider export tamper

Required result: digest/ref/manifest mismatch => `BLOCK`.

### M-07 — stale restore destination

Restoring into a dirty destination can mix old and recovered state.

Required result: `BLOCK`.

### M-08 — fake redundancy

Two replica labels that point to the same or nested local root are not two local failure domains.

Required result: `BLOCK`.

External note: distinct paths still do not prove distinct physical/providers. Production independence needs external evidence.

### M-09 — one replica corrupted

Required result: corrupted domain => `BLOCK`; healthy domain remains independently recoverable.

### M-10 — primary storage domain disappears

Required result: alternate domain alone can return the exact protected artifact.

### M-11 — wrong recovery identity

Required result: encrypted backup cannot be decrypted by an unrelated recovery identity.

### M-12 — fresh separated recovery

Generate two real OpenPGP recovery identities, expose only their public keys to the producer, encrypt the continuity capsule, destroy the primary replica domain, recover from the alternate replica, decrypt using only the alternate private identity, then reconstruct the Git mirror and verify refs/fsck.

Required result: `PASS` without executing restored project code.

### M-13 — validator self-corruption

The first test prototype accidentally overrode `unittest.TestCase.run`, making the validation harness itself invalid.

Required result: retain this as process regression: validation code must not replace framework lifecycle methods accidentally; CI discovery must execute the intended tests.

## Strength semantics

Passing this corpus does **not** mean perfect resilience. It proves only the frozen responsibilities above.

Remaining situational decisions include:

- actual backup cadence / recovery-point objective;
- retention;
- which provider metadata scopes are Tier 0;
- which real second provider/device/account constitutes an independent failure domain;
- geographic separation;
- offline/WORM copy requirements;
- recovery-key operational custody.

Those should be tightened when the workload justifies them rather than bloating the base system pre-emptively.

## Promotion rule

`METEOR GREEN + INHERITED CLOUD-CUSTODY GREEN + REAL GPG ALTERNATE-DOMAIN DRILL GREEN -> CONTRACT MAY BE ADOPTED`

Any newly observed material miss becomes an inherited regression for future DARWIN occupants.

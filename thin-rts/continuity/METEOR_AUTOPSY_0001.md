# METEOR AUTOPSY 0001 — Continuity / Recovery

Status: `ROUND_2_GREEN / DEATH_CAUSES_INHERITED`

Target: 新RTS（仮称） Continuity / Recovery v0, composed with Encrypted Cloud Custody v0.

## Raison d'être verdict

`SURVIVES`

The surviving responsibility is narrow:

> Critical Tier-0 state must be able to leave a failed external substrate and reconstruct elsewhere with bounded integrity evidence.

Killed responsibilities:

- new cloud/source host/object store;
- custom cryptography/key vault;
- preserve everything forever;
- one universal backup interval/retention policy;
- pretend that two labels prove physical independence.

## Frozen Meteor attacks

The inherited regression corpus now requires:

- dirty/untracked working tree => `BLOCK`;
- shallow or partial/promisor clone => `BLOCK`;
- LFS/submodule state without a separate export => `BLOCK`;
- required provider-metadata export/scope missing => `BLOCK`;
- provider export that does not attest secret-value exclusion => `BLOCK`;
- bundle/manifest/provider-export tamper => `BLOCK`;
- dirty restore destination => `BLOCK`;
- one/fake/nested replica domain => `BLOCK`;
- corrupt replica => `BLOCK` for that domain while a healthy domain remains usable;
- primary replica disappearance => alternate domain must recover exact protected bytes;
- wrong recovery identity => decrypt must fail;
- fresh alternate recovery identity + alternate replica => decrypt + manifest verify + Git mirror reconstruction + `git fsck` + exact refs => `PASS`;
- restored project code must not execute during verification.

## Observed Meteor Round 1 — prototype killed

The focused unit corpus passed, but the real integration surface produced two material failures.

### Death C-01 — validator mutated the source before capture

`py_compile` created validation artifacts before the live repository capture. The continuity gate correctly saw a dirty/untracked tree and refused to claim a complete snapshot.

Repair:

- run the real repository continuity capture **before** any validator/build step can mutate the worktree;
- do not weaken the dirty-tree invariant.

### Death C-02 — exact OpenPGP recipient still lacked unattended trust binding

The producer contained only the two public recovery keys and correctly had no secret-key records, but GnuPG refused unattended encryption because the newly imported UIDs had no local certification trust.

The custody contract already selected recipients by exact full primary fingerprint, so the repair was not to trust a name/UID or disable key separation.

Repair:

- explicitly bind producer owner-trust to the exact selected full fingerprints before unattended encryption;
- private recovery identities remain outside the producer;
- wrong unrelated recovery identity must still fail decryption.

### Death C-03 — validator lifecycle collision

The first test prototype accidentally named a helper `run`, overriding `unittest.TestCase.run`.

Repair:

- rename the helper and retain actual unittest discovery/execution as a process regression.

## Observed Meteor Round 2 — survived

GitHub Actions `Continuity Recovery Candidate Tests` run #6:

- actual PR repository capture on untouched worktree: `PASS`;
- provider-neutral Git bundle: 5,701,092 bytes;
- bundle SHA-256: `8efd6e01be3656034f9ee99a69344f1040f6f47201122b7ea91d373fa6dfad14`;
- captured/restored refs: `103`;
- fresh mirror `git fsck`: `PASS`;
- restored project code execution: `NOT_PERFORMED`;
- 10 focused Continuity Meteor regressions: `PASS`;
- real two-recipient GPG alternate-domain recovery: `PASS`;
- wrong recovery identity failure regression: `PASS`.

Inherited `Cloud Custody Candidate Tests` run #27: `PASS`.

Unicode Guard / independent Semgrep on the same head: `PASS`.

## Strength classification

No universal “100% safe” claim is made.

- Tier-0 Git reproducibility: `STRONG_UNDER_CURRENT_EVIDENCE`;
- incomplete/tampered snapshot rejection: `STRONG_UNDER_CURRENT_EVIDENCE`;
- encrypted alternate-domain failover semantics: `STRONG_UNDER_CURRENT_EVIDENCE`;
- provider-neutral Git exitability: `STRONG_UNDER_CURRENT_EVIDENCE`;
- provider-only metadata exitability: `CONTRACT_PROVEN / LIVE_EXPORTER_DEPLOYMENT_DEPENDENT`;
- real physical/provider/geographic independence: `OPERATIONAL_EVIDENCE_REQUIRED`;
- cadence/RPO/retention/offline-WORM requirements: `SITUATIONAL_POLICY`.

## Promotion verdict

`ADOPT_CONTRACT`

Adopt the hard invariants, Tier policy, regression deaths, and current reference occupants into 新RTS（仮称）.

Do **not** convert situational controls into mandatory base-system weight. When a workload declares a provider metadata scope, RPO, WORM requirement, or real failure-domain requirement critical, that declared requirement becomes fail-closed for that workload.

Any future material miss becomes inherited regression memory for the next DARWIN occupant.

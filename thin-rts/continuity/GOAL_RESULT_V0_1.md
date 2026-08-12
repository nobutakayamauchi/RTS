# /goal Result — 新RTS（仮称） Continuity / Recovery v0.1

Status: `ADOPT / FINAL-CI-RECHECK`

## Goal

Make 新RTS（仮称） resilient to loss, corruption or lockout of an external management substrate without recreating a giant custom platform.

## WITNESS decomposition

Durable responsibilities:

1. provider-neutral Tier-0 capture;
2. explicit provider-only metadata export contract;
3. integrity-bound fresh reconstruction;
4. separated recovery identity;
5. more than one recovery path for protected backup material;
6. permanent inheritance of observed recovery death causes.

Responsibilities rejected from the base system:

- custom cloud/source host/object store;
- custom cryptography/key vault;
- universal backup cadence/retention;
- mandatory preservation of cheap derived state;
- claiming physical independence from two logical labels.

## ULTIMATE LOOP / METEOR result

### Round 1

Focused unit attacks were green, but real integration killed the candidate on:

- validator-created worktree dirt before live capture;
- GPG unattended encryption trust not established for newly imported exact-fingerprint recipients;
- earlier validator helper collision with `unittest.TestCase.run`.

The workload was not weakened.

Repairs:

- capture untouched real repository before validator/build mutation;
- bind local GPG owner-trust to the exact selected full primary fingerprints while keeping private recovery identities outside the producer;
- repair the validator lifecycle collision.

### Round 2

Observed GitHub evidence on head `1a936c40f832ca776204af7ffe43fcd844059b52`:

- Continuity Recovery Candidate Tests run #6: `SUCCESS`;
- real RTS PR repository capture/drill: `PASS`;
- provider-neutral Git bundle size: `5,701,092` bytes;
- bundle SHA-256: `8efd6e01be3656034f9ee99a69344f1040f6f47201122b7ea91d373fa6dfad14`;
- captured/restored refs: `103`;
- fresh mirror `git fsck`: `PASS`;
- restored code execution: `NOT_PERFORMED`;
- focused Continuity Meteor regressions: `10/10 PASS`;
- real two-recipient GPG alternate-domain recovery: `PASS`;
- wrong unrelated recovery identity: rejected as required;
- inherited Cloud Custody Candidate Tests run #27: `SUCCESS`;
- Unicode Guard and independent Semgrep on the same head: `SUCCESS`.

## Strength assessment

No perfect-security percentage is assigned.

| Surface | Current assessment |
|---|---|
| Tier-0 Git history/ref reproducibility | `STRONG_UNDER_CURRENT_EVIDENCE` |
| Partial/incomplete capture rejection | `STRONG_UNDER_CURRENT_EVIDENCE` |
| Backup tamper detection | `STRONG_UNDER_CURRENT_EVIDENCE` |
| Fresh non-executing recovery proof | `STRONG_UNDER_CURRENT_EVIDENCE` |
| Encrypted alternate-domain failover semantics | `STRONG_UNDER_CURRENT_EVIDENCE` |
| Provider-neutral Git exitability | `STRONG_UNDER_CURRENT_EVIDENCE` |
| Provider-only metadata export | `CONTRACT_PROVEN / LIVE_ADAPTER_DEPLOYMENT_DEPENDENT` |
| Real provider/device/region independence | `OPERATIONAL_EVIDENCE_REQUIRED` |
| Cadence / RPO / retention / offline-WORM | `SITUATIONAL_POLICY` |

## Priority rule

Base-system effort is spent first on:

`SAFETY > REPRODUCIBILITY > RECOVERABILITY > EXITABILITY > DECLARED FAILURE-DOMAIN RESILIENCE`

Tier-1/Tier-2 completeness is allowed to lose against simplicity, cost and speed as long as Tier-0 invariants remain intact.

A situational requirement becomes hard only when the workload declares it critical. Example: if a legal/evidence workload requires WORM + 24h RPO + two providers, those become fail-closed requirements for that workload; they do not automatically become permanent weight for every use of 新RTS（仮称）.

## Adoption verdict

`ADOPT`

Adopt:

- the Continuity / Recovery contract;
- Tier-0/Tier-1/Tier-2 preservation policy;
- provider export attestation/scope contract;
- fresh-recovery proof requirement;
- alternate-recovery/failure-domain semantics;
- all observed Meteor death causes as permanent regression memory.

Keep replaceable:

- Python implementation;
- local filesystem replica adapter;
- GnuPG/OpenPGP occupant;
- GCS/provider transport occupant;
- future provider metadata exporter.

## Final guard

This result authorizes merge only if the documentation-only final head re-runs the same security, inherited custody and continuity CI without new failures.

A final-head failure reopens METEOR. It must not be waived to preserve the adoption decision.

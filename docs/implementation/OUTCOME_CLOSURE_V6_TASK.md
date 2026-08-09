# Outcome Closure v6 completion contract

Status: DEVIL'S ADVOCATE VALIDATION

## Invariant

```text
Authorized Deployment != Outcome Evidence.
Bound Runtime Observation != Outcome Evidence.
Matching execution label != proof closure.
Unsigned or replayed outcome != authorized evidence.
```

## Required proof chain

```text
Authorized Deployment Identity
  -> exact bound Runtime Observation
  -> execution identity
  -> signed Outcome source
  -> replay check
  -> temporal binding
  -> Proof-Closed Outcome Evidence
```

## Required adversarial failures

- unbound runtime
- runtime mutation after binding
- different execution id
- different session
- different deployment fingerprint
- different expectation fingerprint
- different runtime fingerprint
- unknown outcome source
- forged outcome signature
- replayed evidence id
- outcome before runtime
- outcome outside the governed time window

## Boundary

This layer proves deterministic binding and authenticated source provenance for one live outcome claim. It does not prove physical truth when the trusted outcome source or lower substrate is compromised, and it does not reinterpret `outcome_evidence/` SIMULATED_ONLY fixtures as production success.

Completion requires dedicated tests, full repository regression, Unicode Guard, review-thread resolution, and merge to `main`.

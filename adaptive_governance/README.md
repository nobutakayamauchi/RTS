# Adaptive Governance Compiler v1

This package deterministically compiles the **minimum non-authorizing governance plan** required for an exact change context.

It does not approve, apply, mutate, merge, publish, deploy, message, call providers, or perform external actions.

## Fixed constitutional boundary

The compiler cannot relax these rules:

- no self-approval;
- no authority escalation;
- no unrecorded policy relaxation;
- a plan is evidence only and remains `NOT_APPLIED`;
- G3/G4 work requires independent review;
- G4 work requires two explicit human approvals and manual execution.

## Profiles

- `G0`: documentation or test-only, local, read-only change;
- `G1`: reversible local implementation change;
- `G2`: approval-flow, schema, workflow, historical-failure, or high-uncertainty change;
- `G3`: sensitive data, adjacent/external repository, external action, or production effect;
- `G4`: financial/contractual or irreversible production effect.

Emergency status never lowers the selected level.

## Commands

```bash
python -m adaptive_governance.cli compile --context context.json --output plan.json
python -m adaptive_governance.cli verify --plan plan.json --context context.json
python -m adaptive_governance.cli profiles
```

There is intentionally no `apply`, `approve`, `merge`, or `execute` command.

## Cost control

Each plan records implementation steps, governance steps, their ratio, and one of:

- `BALANCED`
- `HEAVY`
- `OVER_GOVERNED`

Assessment and Preflight are compressed into one initial compiler step. Completion evidence is also a single step. The profile itself defines a maximum governance-step budget.

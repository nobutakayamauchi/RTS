# Read-Only Governed Loop Orchestrator v1

This package composes current repository-local RTS verification contracts into one deterministic, one-shot loop-run record.

## Commands

```text
python -m governed_loop.cli generate
python -m governed_loop.cli verify
python -m governed_loop.cli summary
```

`generate` and `summary` write canonical JSON only to stdout. `verify` recomputes every governed source fingerprint, invokes component verification in a fixed order, proves deterministic equality, validates the committed loop run, and verifies that source files were unchanged.

## Fixed verification order

1. Asset Manifest
2. Read-Only Loop Core
3. Governed Execution Controller self-verification
4. Outcome Evidence
5. Skill Regression and rollback
6. Proposal-Only Outcome Learning

The controller stage uses its bounded local self-verification. It does not dispatch a live provider. Exact controller plan and authorization fingerprints are linked from the governed outcome bundles.

## Authority boundary

Every run remains:

```text
mode: ONE_SHOT_READ_ONLY
external_execution_performed: false
scheduler_authorized: false
provider_authorized: false
adjacent_repository_write_authorized: false
skill_mutation_authorized: false
approval_status: NOT_APPROVED
application_status: NOT_APPLIED
automatic_rollback_authorized: false
```

The package cannot schedule itself, poll, call a network or provider, execute subprocesses or shell commands, publish, deploy, message, mutate or apply a Skill, write an adjacent repository, or claim external success from `SIMULATED_ONLY` evidence.

It stores approved summaries and fingerprints only. Raw prompts, credentials, customer data, provider payloads, and private repository bodies are rejected.

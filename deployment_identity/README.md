# Deployment Identity v1

Deployment Identity establishes what code and execution surface were actually active at observation time before RTS classifies runtime behavior.

## Invariant

```text
Code existence != runtime evidence.
```

A repository file, branch, or commit is source evidence only. Runtime implementation classification is forbidden until the deployed identity is established from explicit observations.

## Required observations

A v1 deployment observation must identify all of:

- `service_unit` — the running service, unit, container, job, or equivalent execution owner;
- `working_directory` — the runtime working directory;
- `executable_or_module` — the executable, module, image entrypoint, or equivalent;
- `active_route_surface` — the active route, command, worker queue, interface, or other exercised surface;
- `deployed_revision` — the exact deployed commit/revision/image digest;
- `source_revision` — the exact source revision whose behavior is being classified;
- `observed_at` — timezone-aware observation timestamp.

## Fail-closed rule

Deployment identity is established only when every required field is present and `deployed_revision == source_revision`.

Otherwise the result is `DEPLOYMENT_IDENTITY_NOT_ESTABLISHED`, and runtime implementation classification remains unauthorized.

## Commands

```bash
python -m deployment_identity.cli verify --observation path/to/observation.json
python -m deployment_identity.cli fingerprint --observation path/to/observation.json
```

The verifier is deterministic, standard-library-only, read-only, and performs no network, shell, provider, deployment, or repository mutation.

## Boundary

Deployment Identity does not prove that an outcome is correct. It proves only that the runtime surface being discussed is bound to the expected source revision and required runtime identity observations.

The intended evidence chain is:

```text
Source Identity -> Deployment Identity -> Runtime Observation -> Outcome Evidence
```

# Governed Execution Controller v1

This package turns one already-selected and explicitly authorized FREEZER item into a bounded, reconstructable **local dry-run**.

It does not grant approval, select work, call a network, run a shell command, invoke a provider, publish, deploy, message, schedule, mutate another repository, or perform customer actions.

## Authority

The only v1 authority is `DRY_RUN_APPROVED`. The only permitted capability is `LOCAL_CHECKPOINT_WRITE`, and writes are restricted to an explicit `--state-dir`.

## Commands

```bash
python -m execution_controller.cli plan --authorization PATH
python -m execution_controller.cli run --authorization PATH --state-dir PATH --script PATH
python -m execution_controller.cli resume --authorization PATH --state-dir PATH --script PATH
python -m execution_controller.cli stop --authorization PATH --state-dir PATH --timestamp VALUE
python -m execution_controller.cli inspect --authorization PATH --state-dir PATH
python -m execution_controller.cli verify
```

`plan` is deterministic and writes only JSON to stdout. `run`, `resume`, and `stop` append hash-chained events below `<state-dir>/<plan-id>/`. `events.jsonl` is the source of truth; `checkpoint.json` is a derived current pointer.

A retryable dry-run failure leaves the run in `RUNNING` when attempt budget remains. A later explicit `resume` consumes the next attempt. Budget exhaustion escalates instead of retrying without limit.

Dry-run success is labelled `SIMULATED_ONLY`; it is never represented as an externally verified outcome.

## Stop and audit behavior

`resume` always re-evaluates the current FREEZER, Assessment, Preflight and WIP gates. `stop` and `inspect` instead verify the existing event chain and checkpoint under the supplied state directory. This means gate drift cannot grant continuation authority, but it also cannot block an emergency stop or audit of an already-started run.

Script results are screened recursively for private-field names. Persisted summaries are bounded, single-line text and reject obvious prompt, secret, credential, token, customer-data, provider-payload and tool-argument markers. Invalid scripts are rejected before the first run event is written.

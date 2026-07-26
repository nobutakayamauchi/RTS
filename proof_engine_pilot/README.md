# Proof Engine Pilot v1

A deterministic, standard-library-only minimum vertical slice for evidence-backed achievement discovery.

## Commands

```bash
python -m proof_engine_pilot.cli generate
python -m proof_engine_pilot.cli verify
python -m proof_engine_pilot.cli summary
python -m proof_engine_pilot.cli review-template
```

There is no approve, publish, outreach, contract, provider, merge, or external-execution command. The committed first run stops at human review with 12 candidates and a blocked `NOT_PUBLISHED` output asset.

# Proof Engine Pilot v1

A deterministic, standard-library-only minimum vertical slice for evidence-backed achievement discovery.

## Candidate-run commands

```bash
python -m proof_engine_pilot.cli generate
python -m proof_engine_pilot.cli verify
python -m proof_engine_pilot.cli summary
python -m proof_engine_pilot.cli review-template
```

## Human-review commands

```bash
python -m proof_engine_pilot.review_cli verify
python -m proof_engine_pilot.review_cli summary
python -m proof_engine_pilot.review_cli effective
```

The original candidate run remains immutable with 12 `REVIEW_REQUIRED` candidates. Human review is appended separately: seven originals are approved, five originals remain preserved with `REVISE` decisions, and five factually corrected revisions are approved.

The effective set is ready only for an internal asset draft. There is no approve, publish, outreach, contract, provider, merge, or external-execution command, and publication remains `NOT_PUBLISHED`.

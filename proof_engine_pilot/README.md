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

## Review-derived learning commands

```bash
python -m proof_engine_pilot.learning_cli verify
python -m proof_engine_pilot.learning_cli summary
python -m proof_engine_pilot.learning_cli replay
python -m proof_engine_pilot.learning_cli preflight path/to/future_candidate.json
```

Round 0001 stores seven accepted originals and five original-to-revision correction pairs as a repository-local learning dataset. Six active rules now provide `SUGGEST_ONLY` factuality and classification preflight for candidate runs after `PROOF-ENGINE-P3-RUN-0001`.

This is not a model-weight update. It does not silently rewrite candidates or manufacture approval. Originals remain append-only, every correction stays linked to its human decision, and all future warnings still terminate at a human review gate.

The effective reviewed set is ready only for an internal asset draft. There is no approve, publish, outreach, contract, provider, merge, model-training, or external-execution command, and publication remains `NOT_PUBLISHED`.

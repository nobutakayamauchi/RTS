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

Round 0001 stores seven accepted originals and five original-to-revision correction pairs as a repository-local learning dataset. Six active rules provide `SUGGEST_ONLY` factuality and classification preflight for candidate runs after `PROOF-ENGINE-P3-RUN-0001`.

## Six-part internal asset commands

```bash
python -m proof_engine_pilot.asset_cli generate
python -m proof_engine_pilot.asset_cli verify
python -m proof_engine_pilot.asset_cli summary
python -m proof_engine_pilot.asset_cli review-template
```

The twelve effective reviewed candidates are consolidated exactly once into six internal asset drafts:

1. Governed Loop Engine
2. WIP=1 and Human-Gated Delivery
3. Append-Only Human Review and Integrity Checks
4. Promotion Application Preview
5. Adaptive Governance Compiler and Audit Remediation
6. Conversation-to-Seed Project Ingestion

## Internal asset review commands

```bash
python -m proof_engine_pilot.asset_review_cli verify
python -m proof_engine_pilot.asset_review_cli summary
python -m proof_engine_pilot.asset_review_cli effective
```

All six internal assets were reviewed against factuality, contribution separation, non-overlap, privacy, and internal-source readiness. They are approved only as sources for the public-wording draft stage.

## Audience-facing wording draft commands

```bash
python -m proof_engine_pilot.public_wording_cli generate
python -m proof_engine_pilot.public_wording_cli render-markdown
python -m proof_engine_pilot.public_wording_cli verify
python -m proof_engine_pilot.public_wording_cli summary
python -m proof_engine_pilot.public_wording_cli review-template
```

The six approved internal sources are translated into English audience-facing wording with a headline, summary, value explanation, evidence note, human and AI-tool attribution, and explicit limits. Every draft passes the active review-learning preflight and remains `PUBLICATION_REVIEW_REQUIRED / NOT_PUBLISHED`.

Original candidates, corrected revisions, internal assets, and human decisions remain preserved. This is not a model-weight update and does not manufacture approval.

There is no approve, publish, outreach, contract, provider, merge, model-training, or external-execution command. Publication requires a separate append-only human decision and remains unauthorized in this stage.

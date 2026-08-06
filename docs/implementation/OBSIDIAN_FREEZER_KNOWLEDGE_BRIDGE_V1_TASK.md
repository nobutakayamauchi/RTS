# Obsidian → FREEZER Knowledge Bridge v1 — Implementation Task

Status: READY FOR IMPLEMENTATION
Parent specification: `docs/architecture/OBSIDIAN_FREEZER_KNOWLEDGE_BRIDGE_V1.md`

## Goal

Implement a local, read-only-by-default bridge that scans an external Obsidian Markdown vault, preserves immutable source captures, normalizes and challenges knowledge records, routes them to the correct RTS knowledge destination, and exports human-reviewable FREEZER drafts without granting build authority.

## Package layout

```text
knowledge_bridge/
├── __init__.py
├── cli.py
├── config.py
├── intake.py
├── capture_store.py
├── normalize.py
├── challenge.py
├── connect.py
├── recall.py
├── route.py
├── sensitivity.py
├── freezer_export.py
├── schemas/
│   ├── knowledge_record.schema.json
│   ├── challenge_result.schema.json
│   └── bridge_config.schema.json
└── README.md

tests/knowledge_bridge/
├── fixtures/vault/
├── test_intake.py
├── test_capture_store.py
├── test_normalize.py
├── test_challenge.py
├── test_recall.py
├── test_sensitivity.py
└── test_freezer_export.py
```

## Commands

```bash
python -m knowledge_bridge.cli scan --vault /path/to/vault
python -m knowledge_bridge.cli normalize --capture CAPTURE_ID
python -m knowledge_bridge.cli challenge KNOWLEDGE_ID
python -m knowledge_bridge.cli recall --event SPEC_DRAFTED --project PROJECT_ID
python -m knowledge_bridge.cli route KNOWLEDGE_ID
python -m knowledge_bridge.cli export-freezer KNOWLEDGE_ID --output /tmp/item.json
python -m knowledge_bridge.cli verify
```

Every state-changing command writes a new immutable derivative record. No command edits source Markdown.

## Phase 1 — contracts and storage

1. Add JSON schemas.
2. Add configuration loader.
3. Define stable IDs and timestamps.
4. Implement content hashing and immutable captures.
5. Implement derived indexes that can be rebuilt.
6. Add synthetic vault fixtures.

Exit gate: repeated scan is idempotent and changed notes create a new capture version.

## Phase 2 — normalization and sensitivity

1. Parse YAML frontmatter when present.
2. Treat folder names as hints, never authority.
3. Add deterministic rule-based classification fallback.
4. Preserve source excerpt, source hash, and confidence.
5. Detect likely secrets and protected personal categories.
6. Block public export by default for non-public records.

Exit gate: fixture notes are classified and sensitive fixtures cannot be publicly exported.

## Phase 3 — connection and Devil's Advocate

1. Link records by explicit IDs, project IDs, tags, and source references.
2. Detect exact and near-duplicate claims using deterministic text fingerprints in v1.
3. Record possible contradictions without overwriting either side.
4. Implement the ten-question challenge gate.
5. Require unresolved human decisions to remain explicit.
6. Distinguish intentional supersession from unresolved contradiction.

Exit gate: proposals cannot become promotion-ready without a challenge result.

## Phase 4 — routing and recall

1. Implement destinations: recall, pattern, test, project context, FREEZER, archive.
2. Implement event query for:
   - SPEC_DRAFTED
   - DEVILS_ADVOCATE
   - ASSET_SEARCH
   - FREEZER_INTAKE
   - PREFLIGHT
   - UI_BOOTSTRAP
   - BUG_REPORTED
   - RELEASE_GATE
   - RESUME_WORK
3. Return ranked records with reasons and source references.
4. Stay silent when no result passes the configured relevance threshold.

Exit gate: required acceptance events return expected synthetic records.

## Phase 5 — FREEZER draft export

1. Map promotion-ready records to the current FREEZER item schema.
2. Validate against `freezer/schemas/item.schema.json`.
3. Force `build_authority: NOT_APPROVED`.
4. Never invoke `freezer.cli add` from the exporter.
5. Include challenge evidence and source hashes in `source_refs` or a sidecar review report.
6. Reject exports missing original problem, why-it-matters, triggers, negative triggers, dependencies, effort range, or human review.

Exit gate: a valid draft passes schema validation and cannot select or approve itself.

## Phase 6 — repository integration

1. Document the bridge in RTS system map.
2. Add bridge verification to CI.
3. Add a disabled-by-default example configuration.
4. Confirm current FREEZER tests remain unchanged and pass.
5. Add a migration guide for an existing vault that does not require folder restructuring.

Exit gate: disabling or removing bridge configuration leaves current RTS behavior intact.

## Required tests

- source Markdown remains byte-identical after all commands;
- duplicate scans do not duplicate captures;
- note movement between folders does not silently change authority;
- edited notes preserve prior capture versions;
- contradictory decisions remain visible;
- supersession requires explicit relation;
- personal and restricted notes cannot be publicly exported;
- secret-like content causes hard failure;
- archive-only notes do not enter FREEZER;
- promotion-ready FREEZER drafts always have `NOT_APPROVED`;
- no bridge command changes FREEZER item state;
- event recall explains why each record was returned;
- no-action events can produce an empty result;
- malformed frontmatter does not destroy raw capture;
- unavailable vault fails safely without affecting FREEZER.

## Human review checkpoints

Human review is mandatory when:

- sensitivity is personal or restricted;
- the system detects a contradiction with approved/frozen knowledge;
- promotion destination is FREEZER;
- confidence is low;
- a record claims intentional supersession;
- the record changes public claims or release documentation.

## Completion report

The implementation PR must report:

- files added and modified;
- schema versions;
- test results;
- known limitations;
- whether any existing FREEZER behavior changed;
- sample event recall output;
- sample challenged record;
- sample valid FREEZER draft;
- explicit confirmation that automatic approval and implementation remain impossible.

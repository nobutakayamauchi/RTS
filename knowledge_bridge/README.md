# RTS Knowledge Bridge

The bridge reads an external Obsidian Markdown vault without modifying source files. Phase 1 provides deterministic scanning, immutable captures, and verification. Phase 2 adds deterministic normalization and a deny-by-default sensitivity gate.

## Safety boundary

- Source Markdown is read-only.
- The bridge does not write into Obsidian.
- The bridge does not add, select, approve, or modify FREEZER items.
- State is stored separately under `.rts/knowledge_bridge` unless configured otherwise.
- Public export is denied unless a record is explicitly public and contains no detected secret or protected personal category.

## Scan

```bash
python -m knowledge_bridge.cli scan \
  --vault /absolute/path/to/vault \
  --state /absolute/path/to/bridge-state
```

A repeated scan of unchanged notes returns the existing capture. Editing a note creates another immutable capture while preserving the earlier version.

## Normalize

```bash
python -m knowledge_bridge.cli normalize \
  --vault /absolute/path/to/vault \
  --state /absolute/path/to/bridge-state \
  --capture KBC-CAPTURE-ID
```

Normalization parses simple YAML frontmatter when valid, preserves malformed source unchanged, classifies knowledge using explicit metadata first and deterministic hints second, and records confidence, source excerpt, sensitivity, and public-export eligibility. Folder names are hints only and never grant authority.

Supported initial knowledge types:

- `problem`
- `decision`
- `spec`
- `test`
- `pattern`
- `project_context`
- `evidence`
- `idea`
- `archive`

Sensitivity levels are `public`, `internal`, `personal`, and `restricted`. Secret-like material is always restricted. Medical, employment-dispute, financial, email, and phone patterns are personal unless a stricter result applies.

## Verify

```bash
python -m knowledge_bridge.cli verify \
  --vault /absolute/path/to/vault \
  --state /absolute/path/to/bridge-state
```

## Configuration

```json
{
  "vault_path": "/absolute/path/to/vault",
  "state_path": "/absolute/path/to/bridge-state",
  "include_globs": ["**/*.md"],
  "exclude_dirs": [".obsidian", ".git", ".trash"]
}
```

Use with `--config /path/to/config.json`.

## Current completion boundary

Phases 1 and 2 now cover capture, normalization, and sensitivity blocking. Devil's Advocate execution, connection, recall, routing, and FREEZER draft export remain unavailable. Existing FREEZER behavior is unchanged.

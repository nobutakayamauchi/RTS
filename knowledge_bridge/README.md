# RTS Knowledge Bridge

The bridge reads an external Obsidian Markdown vault without modifying source files. Phase 1 provides deterministic scanning, SHA-256 content identity, immutable versioned captures, and a rebuildable JSON index.

## Safety boundary

- Source Markdown is read-only.
- The bridge does not write into Obsidian.
- The bridge does not add, select, approve, or modify FREEZER items.
- State is stored separately under `.rts/knowledge_bridge` unless configured otherwise.

## Scan

```bash
python -m knowledge_bridge.cli scan \
  --vault /absolute/path/to/vault \
  --state /absolute/path/to/bridge-state
```

A repeated scan of unchanged notes returns the existing capture. Editing a note creates another immutable capture while preserving the earlier version.

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

Phase 1 is complete when scanning is idempotent, source bytes remain unchanged, changed notes create new immutable versions, unavailable vaults fail without changing FREEZER, and the capture store verifies cleanly. Normalization, sensitivity analysis, challenge, recall, routing, and FREEZER draft export remain intentionally unavailable until later phases.

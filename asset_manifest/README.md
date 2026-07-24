# RTS Cross-Repo Asset Manifest v1

A deterministic, append-only inventory of repository responsibilities and reusable assets across the RTS ecosystem.

It records metadata and exact references. It does **not** copy repository bodies, execute tools, mutate adjacent repositories, or promote an asset into RTS core.

## Commands

```bash
python -m asset_manifest.cli verify
python -m asset_manifest.cli list-repos
python -m asset_manifest.cli list-assets
python -m asset_manifest.cli show RTS-AM-A0001
python -m asset_manifest.cli show nobutakayamauchi/RTS
python -m asset_manifest.cli diff 1 2
python -m asset_manifest.cli reindex
python -m asset_manifest.cli create --input /path/to/snapshot.json
```

`create` appends `vNNN.json`; it refuses to overwrite immutable history. Indexes and the SHA-256 manifest are derived from the current snapshot.

## Hard verification rules

- unique repository names and asset IDs
- assets must reference a known repository
- a capability may have only one canonical owner
- private/restricted assets require safe logical locators
- restricted assets cannot be committed to the public manifest
- direct reuse requires a compatible or not-applicable license state
- current pointer, indexes, version history, and hashes must match
- obvious secret material is rejected

The seed snapshot covers the 19 currently classified repositories. Private repositories are represented only as approved metadata.

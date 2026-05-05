# RTS Ecosystem Repository Map

## Core repository (this repo)

RTS trust and reconstruction core:
- canonical schemas
- append-only session/evidence surfaces
- reconstruction and integrity rules
- governance and rollback-safe documentation

## External/adjacent domains (reference only)

The following are ecosystem-adjacent and intentionally out of this repository implementation scope:
- Skills runtime/catalog
- MCP Packs
- Hermes orchestration layer
- Talent Registry operations
- Signal Feed operations

## Integration posture

This repository should expose stable contracts (schemas/rules/docs) that external systems can consume.
It should not absorb execution harness implementations from adjacent domains.

# Execution Record and Evidence Reference

## Purpose
Provide a minimal structural overview of how `execution_record` and `evidence_ref` relate in the current RTS core.

## Execution Record
`execution_record` is the minimal record of a skill execution and includes:
- `skill_id`
- `drive_id`
- `pack_id`
- `trigger`
- `result`
- `timestamp`

## Evidence Reference
`evidence_ref` is the minimal reference to evidence used in reconstructable flows and includes:
- `evidence_id`
- `source_type`
- `source_ref`
- `retrieved_at`

## Relationship
Reconstructable execution may rely on both execution records and evidence references.

## Boundary
This document is a structural overview only. It does not define full linkage or runtime implementation.

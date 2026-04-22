# Intent and Execution

## Purpose
This note describes the minimal structural relationship between `intent_record` and `execution_record` in the RTS core.

## Intent Record
`intent_record` is the minimal record of requested execution intent. It includes:
- `intent_id`
- `skill_id`
- `requested_by`
- `requested_at`

## Execution Record
`execution_record` is the minimal record of executed skill flow. It includes:
- `skill_id`
- `drive_id`
- `pack_id`
- `trigger`
- `result`
- `timestamp`

## Relationship
Reconstructable execution may rely on both intent records and execution records.

## Boundary
This is a structural overview only. It does not define full linkage or runtime implementation.

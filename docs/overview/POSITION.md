# RTS Repository Position

## What this repository is

RTS is the trust and reconstruction core.

This repository defines how execution is recorded, how evidence is preserved, how checkpoints are created, and how work can be reconstructed later.

RTS is not an execution harness.
RTS is not an MCP connector collection.
RTS is not a task runner.

RTS is the base layer that preserves:
- intent
- execution records
- evidence snapshots
- checkpoints
- manifests
- reconstruction rules
- governance rules

## Core responsibility

RTS is responsible for:
- defining canonical record formats
- preserving append-only operational history
- defining reconstruction rules
- defining integrity and evidence rules
- defining checkpoint and resume semantics
- defining governance boundaries for structural change

## Non-responsibility

RTS does not:
- directly orchestrate day-to-day job execution
- directly own external tool integrations
- directly define business workflow logic
- directly act as a chat interface or agent runtime

## Design stance

RTS prioritizes reconstructability over convenience.

If a process is easy to run but difficult to reconstruct, RTS should reject that direction.

If a process can be replayed, inspected, and verified later, RTS should prefer that direction.

## Dependency stance

Other components may depend on RTS schemas and record rules.

RTS should minimize reverse dependency on execution environments, harnesses, or vendors.

RTS must remain usable even if a specific runtime, connector, or orchestration layer is replaced.

## Expected artifacts

Typical artifacts in this repository include:
- schemas
- manifests
- ledger rules
- session rules
- evidence rules
- integrity rules
- governance specifications
- reconstruction documentation

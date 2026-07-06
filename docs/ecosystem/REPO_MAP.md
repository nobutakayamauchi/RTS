# RTS Ecosystem Repository Map

This document maps repositories around RTS without changing RTS core behavior.

RTS remains the canonical decision reconstructability protocol and structural ledger.

Surrounding repositories may implement, demonstrate, sell, test, or extend RTS-style workflows, but they are not RTS core unless explicitly promoted by a separate decision record.

## Core Repository

### RTS

Role: Canonical protocol / structural ledger.

Status: ACTIVE / CANON.

Purpose:

- define reconstructable decision and execution structures
- preserve decision authority, assumptions, and execution state
- expose stable schemas, rules, and documentation that other systems can consume
- serve as the reference point for the surrounding ecosystem

Boundary:

- do not absorb execution harness implementations from adjacent domains
- do not use surrounding repository behavior to silently redefine RTS core
- do not merge runtime, sales, connector, signal, design, or product experiments into RTS core without a separate decision record

## Reference Runtime

### RTS-Minimal-Runtime

Role: Minimal reference runtime.

Status: ACTIVE / REFERENCE.

Purpose:

- demonstrate the smallest reconstructable flow
- preserve `intent -> spec -> execution_record -> manifest -> reconstruction` as a reference path

Boundary:

- do not expand into RTS-AGE
- do not turn into a UI, cloud runner, or multi-agent platform

## Execution Gateway

### RTS-AGE

Role: Agentic Gateway & Execution Lab.

Status: RESCUE / GATEWAY.

Purpose:

- receive work orders, signals, and operator instructions
- produce plans, patches, dry-runs, validation reports, and RTS record proposals

Boundary:

- not RTS core
- not the canonical home of skills, packs, feeds, design research, or talent registry data
- proposal-first by default

## Money-Line / Business Operations

### RTS-minicompany

Role: Solo business operation MVP.

Status: ACTIVE / MONEY-LINE.

Purpose:

- process one business case at a time
- generate sales, proposal, delivery preparation, risk check, and trace outputs
- support human-reviewed solo business execution

Boundary:

- not a fully autonomous sales agent
- not a customer contact system by default
- human approval remains required for price, scope, contract, and contact decisions

### rts01-offer

Role: Static offer landing page.

Status: ACTIVE / SALES-LP.

Purpose:

- present the AI development reset / project audit offer
- direct prospects to a human-reviewed contact path

Boundary:

- not the delivery workflow itself
- not RTS core
- should not overpromise results or automation capability

## Product Candidates

### seminar-compass

Role: Learning reconstruction product candidate.

Status: ACTIVE / PRODUCT.

Purpose:

- transform learning material into structured outputs such as claims, assumptions, prerequisites, priorities, practical takeaways, and retrieval prompts

Boundary:

- not a generic summarizer
- not RTS core
- not RTS-AGE

## Public Profile Surface

### nobutakayamauchi

Role: Public profile and RTS positioning surface.

Status: ACTIVE / PROFILE.

Purpose:

- present the operator identity and RTS positioning
- point readers toward the canonical RTS repository and ecosystem direction

Boundary:

- not RTS core
- not a runtime or delivery workflow
- should stay aligned with the current RTS ecosystem position

## Parts / Extension Shelves

### RTS-Skills

Role: Reusable operational skills.

Status: PARTS / SKILLS.

Purpose:

- hold reusable AI-agnostic operational skills and wrappers

### RTS-MCP-Packs

Role: Connector pack definitions.

Status: PARTS / CONNECTOR-PACKS.

Purpose:

- hold reusable MCP connector pack definitions for future operator environments

### RTS-Hermes-Drive

Role: Orchestration bridge.

Status: PARTS / ORCHESTRATION.

Purpose:

- bridge RTS skills and pack concepts into Hermes-style drive/orchestration structures

### RTS-Design-Research

Role: Design research extension layer.

Status: PARTS / DESIGN-LAYER.

Purpose:

- convert design references and UI research into RTS-compatible design decision material

### rts-dev-protocol

Role: Development doctrine notes.

Status: PARTS / DOCTRINE.

Purpose:

- preserve structure-first development protocol notes and architecture vocabulary

## Freeze / Later Review

### RTS-Talent-Registry

Role: AI talent governance registry.

Status: FREEZE / GOVERNANCE-PARTS.

### RTS-Signal-Feeds

Role: Signal intelligence layer.

Status: FREEZE / SIGNAL-PARTS.

### rts-video-flow

Role: Video workflow scaffold.

Status: FREEZE / MEDIA-PARTS.

### AIX

Role: Execution-aware arbitrage research scaffold.

Status: FREEZE / RESEARCH.

## Archive / Delete Candidates

### codex-connector-test

Role: Connector test repository.

Status: ARCHIVE CANDIDATE.

### ryoushuushotesutoyou

Role: Receipt image/output test.

Status: DELETE CANDIDATE.

### rts-lite

Role: Empty or obsolete lightweight RTS placeholder.

Status: ARCHIVE / DELETE CANDIDATE.

## Rule of Thumb

- RTS defines the protocol.
- RTS-Minimal-Runtime proves the smallest runtime.
- RTS-AGE prepares proposals and validation artifacts.
- RTS-minicompany operates the money-line workflow.
- rts01-offer sells the audit/reset offer.
- seminar-compass is an independent product candidate.
- nobutakayamauchi is the public profile and positioning surface.
- skills, packs, drive, design, talent, and signal repositories are extension shelves until promoted.

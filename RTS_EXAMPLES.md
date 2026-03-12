# RTS Examples

This document provides practical examples of how RTS records decision structures in real operational situations.

The goal is to demonstrate how decision reconstructability works in practice.


---

Example 1 — AI-Assisted Development Decision

Situation

A developer is working with an AI assistant to implement a new feature in a repository.

The AI proposes several approaches.

The developer chooses one implementation strategy.


Decision Snapshot

Context  
Implement logging system for AI execution tracing.

Decision  
Use append-only JSONL ledger stored in repository.

Constraints  
Must work in smartphone-only development environment.

Assumptions  
Git commit history will provide reliable timestamps.

Action  
Implemented JSONL ledger writer.

Outcome  
System successfully records execution traces.


Reconstruction

Later analysis can determine:

Why JSONL was chosen  
What constraints existed  
What assumptions influenced the decision  
What action was executed


---

Example 2 — Incident Reconstruction

Situation

An automated AI workflow modifies several files in a repository.

Later the system produces incorrect output.


Decision Snapshot

Context  
Automated refactor of analysis scripts.

Decision  
Allow AI agent to perform multi-file edits.

Constraints  
No full test environment available.

Assumptions  
Changes are limited to analysis layer.

Action  
AI modifies multiple files.

Outcome  
Unexpected side effects occur.


Reconstruction

RTS allows investigators to determine:

Who authorized the change  
What the AI was instructed to do  
Which assumption failed  
Which decision changed system trajectory


---

Example 3 — Authority Boundary Recording

Situation

A critical system configuration change must be approved by an operator.


Decision Boundary Record

Authority Holder  
System Operator

Scope  
Repository configuration change

Justification  
Enable execution logging infrastructure

Commit State  
Hash representing system state at approval time


Reconstruction

The record allows later verification of:

Who approved the decision  
What system state existed at the time  
Why the decision was made


---

Example 4 — AI Execution Trace

Situation

An AI agent performs automated analysis.


Execution Trace Record

Human Intent  
Generate execution analysis summary.

AI Action  
Scan run logs and summarize anomalies.

Constraints  
No external database allowed.

Assumptions  
Run logs contain sufficient signal.

Outcome  
Summary generated and committed.


Reconstruction

Operators can reconstruct:

The human objective  
The AI action path  
The constraints applied  
The final outcome


---

Summary

RTS records the structural elements necessary to reconstruct how decisions were made.

The protocol does not judge correctness.

Instead it ensures that decision processes remain visible and traceable after execution.

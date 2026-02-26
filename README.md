# RTS — Execution Provenance Protocol for AI Workflows

AI output is reproducible.  
Decision context is not.

RTS preserves execution provenance for AI-assisted work.

It records decision state so outcomes can be reconstructed, audited, and defended.

---

## The Problem

AI systems increase execution speed.

They do not preserve:

- why a decision was made  
- which assumptions were active  
- which alternatives were rejected  
- what constraints influenced the action  

When execution scales, traceability collapses.

RTS restores state-level reproducibility.

---

## What RTS Does

RTS converts execution into structured provenance blocks.

Each block records:

- Context  
- Decision  
- Constraint  
- Assumption  
- Action  
- Outcome  

This enables reconstruction of the decision environment — not just the output.

Execution becomes traceable.  
Incidents become reproducible.

---

## What RTS Is Not

RTS is not:

- memory embedding  
- vector retrieval  
- workflow automation  
- monitoring software  

It does not control agents.  
It observes and formalizes execution.

---

## Quick Start (60 seconds)

Run locally:

```bash
cd starter/python
python START_HERE.py

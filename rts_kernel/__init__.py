"""RTS OS Kernel (v0.1)

Core modules:
- state_engine: determine RTS status from repository state
- memory_index: build searchable index over logs/incidents/radar artifacts
- self_audit: append-only integrity checks + audit log emission
- cli: single entry point for local + GitHub Actions execution

Design goals:
- Smartphone-friendly: minimal commands, deterministic outputs
- Evidence-first: writes logs to /logs and indexes to repo root
"""

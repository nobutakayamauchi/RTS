# RTS OS Kernel (v0.1)

This kernel adds three core runtime capabilities:

1) **STATE ENGINE**
   - Detects repository readiness and evidence presence.
   - Outputs: `rts_state.json`

2) **MEMORY INDEX**
   - Builds a searchable index over logs/incidents/radar.
   - Outputs: `rts_index.json`

3) **SELF AUDIT**
   - Append-only integrity check (heuristic) for `logs/EXECUTION_LOG.md`.
   - Outputs:
     - `logs/SELF_AUDIT_LOG.md` (append-only)
     - `logs/.rts_hashchain.json` (hashchain baseline)

## Run (local or GitHub Actions)

```bash
python -m rts_kernel.cli
```

Or run individual steps:

```bash
python -m rts_kernel.cli --state
python -m rts_kernel.cli --index
python -m rts_kernel.cli --audit
```

## Notes

- The audit is intentionally conservative and smartphone-friendly.
- In v0.2 we will expand:
  - stronger git-based integrity checks
  - incident/radar summarization
  - operator prompts for categorization

# RUN

- run_id:
- created_at:
- operator:
- system:
- goal:
- env:
- mode: auto | semi | manual

---

# CONFIG

- agent_stack:
- config_fingerprint:
- success_flag: unknown

---

# EXECUTION PATH

Run → Span Tree → Artifacts → Flags

---

## SPAN 000

- span_id: "000"
- parent_span_id: null
- order_index: 0

- node_type: planner
- agent_name:

- action_type:
- intent:

- status: ok | warn | fail | drift

- timestamp_start:
- timestamp_end:
- duration_ms:

- input_hash:
- output_hash:

- input_ref:
- output_ref:

- tool_name:

- evidence:
  -

- error:

---

## SPAN 010

- span_id: "010"
- parent_span_id: "000"
- order_index: 1

- node_type: executor
- agent_name:

- action_type:
- intent:

- status:

- timestamp_start:
- timestamp_end:
- duration_ms:

- input_hash:
- output_hash:

- input_ref:
- output_ref:

- evidence:
  -

- error:

---

# ARTIFACT INDEX

Artifacts must exist outside memory.

- artifact_id:
- type: prompt | response | tool_call | code | config
- content_ref:
- checksum:

---

# FLAGS

Generated when structural anomaly detected.

- flag_id:
- span_id:
- severity: low | medium | high | critical
- category:
- description:

---

# MODE RECOMMENDATION

recommended_mode:

reason:

---

# NOTES

Human operator judgment remains final.

RTS observes execution.

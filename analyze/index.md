<!-- AUTO-GENERATED. DO NOT EDIT DIRECTLY. -->

# RTS ANALYZE

Operational pattern analysis from execution history (evidence-first).

---

## Snapshot

- generated utc: `2026-02-23T03:31:10Z`

---

## Incident Trend

- [RTS INCIDENT REPORT](../incidents/INC_20260222_1545_Cursor_ContextLoss.md)
  - note: Long Cursor coding sessions lose operational context. Autocomplete breaks randomly. Old chats reopen unexpectedly. ---
- [RTS INCIDENT REPORT](../incidents/INC_20260222_1704_GPT_ContextResearcher.md)
  - note: AI researcher publicly reports reasoning instability and early prompt failures across frontier LLM models. Observed degradation includes proper noun failures and early reasoning collapse. ---
- [RTS INCIDENT REPORT](../incidents/INC_20260222_1603_ClaudeCode_ContextLoss.md)
  - note: Long Claude Code workflows lose structural reasoning continuity across sessions. Outputs become inconsistent and require repeated manual prompting to restore context. ---
- [RTS INCIDENT REPORT](../incidents/INC_YYYYMMDD_HHMM_System_Problem.md)
  - note: - AI forgot prior instructions - Workflow interruption occurred - Context reset without warning ---
- [RTS INCIDENT REPORT](../incidents/INC_20260222_1818_ChatGPT_RadarHit_2471f850d6dd.md)
  - note: Title: Amure Pinho on X: "@grok and @OpenAI getting "Error saving GPT - Internal Server Error" when I try to add files do knowledge creating a custom GPT. Txt, PDF, not working, img works. Failed to load resource: the server responded with 
- [RTS INCIDENT REPORT](../incidents/INC_20260222_1840_ChatGPT_RadarHit.md)
  - note: Title: Amure Pinho on X: "@grok and @OpenAI getting "Error saving GPT - Internal Server Error" when I try to add files do knowledge creating a custom GPT. Txt, PDF, not working, img works. Failed to load resource: the server responded with 
- [RTS INCIDENT REPORT](../incidents/INC_TEMPLATE.md)
  - note: What happened?
- [RTS INCIDENT REPORT](../incidents/INC_20260222_1818_Claude_RadarHit_3e4912f6ac44.md)
  - note: Title: Gilad Avidan on X: "@nemibanigo Designer friend of mine showed me a Figma/Claude workflow this morning and it looked amazing" / X

---

## Execution Stability

- evidence: [logs/EXECUTION_LOG.md](../logs/EXECUTION_LOG.md)
- status: `ACTIVE` (based on latest execution evidence when available)

---

## Observed Risk Patterns

- context loss / memory fragmentation: `3`
- session reset discontinuity: `3`
- workflow / kernel interruption: `3`
- tool failure: `3`
- server / internal error: `2`

Operator verification recommended for destructive actions.

---

## Governance Signals

- Backup-first enforcement: `ACTIVE`
- AI destructive instruction verification: `REQUIRED`
- Deletion treated as last resort; branch/tag preservation preferred.

---

## Navigation

- memory index: [memory/index.md](../memory/index.md)
- incidents: [incidents/](../incidents/)
- logs: [logs/](../logs/)

RTS Analyze converts execution into understanding.

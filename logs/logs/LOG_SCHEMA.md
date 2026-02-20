# RTS LOG SCHEMA
(Execution Record Standard)

## PURPOSE
Standardize log format so RTS can parse, audit, and replicate execution.

RTS reads logs as structured blocks:
INTENT → ACTION → RESULT → REFLECTION → NEXT

Operator authority remains final.

---

## 1) EXECUTION_LOG Entry Format

### Required Fields
- DATE
- BLOCK_ID
- INTENT
- ACTION
- RESULT
- STATUS
- NEXT

### Template
DATE: YYYY-MM-DD HH:MM (+0900)
BLOCK_ID: BLOCK_########
INTENT:
- What will be done (one sentence)
ACTION:
- What was actually executed (bullet list)
RESULT:
- Observable outcome (facts only)
STATUS: SUCCESS / PARTIAL / FAIL
NEXT:
- Next smallest step (one action)

---

## 2) RESULT_LOG Entry Format
DATE: YYYY-MM-DD HH:MM (+0900)
BLOCK_ID: BLOCK_########
OUTCOME:
- measurable / visible results
NOTES:
- constraints / risks / surprises

---

## 3) SUCCESS_LOG Entry Format
DATE: YYYY-MM-DD HH:MM (+0900)
PATTERN_NAME:
- short name of success pattern
CONTEXT:
- when/why it worked
STEPS:
1) ...
2) ...
3) ...
REPEAT_RULE:
- how to reproduce
CONFIDENCE: LOW / MED / HIGH

---

## 4) REFLECTION_LOG Entry Format
DATE: YYYY-MM-DD HH:MM (+0900)
BLOCK_ID: BLOCK_########
WHAT_WORKED:
- ...
WHAT_FAILED:
- ...
LEARNING:
- ...
AUTO_CUT_NEEDED: YES / NO
GOVERNANCE_NOTE:
- rule breach / drift / none

---

## SAFETY RULE
- No fabricated results.
- Facts before interpretation.
- If uncertain, mark as PARTIAL.

Status: ACTIVE

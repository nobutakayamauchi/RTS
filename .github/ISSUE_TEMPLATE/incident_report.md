name: "RTS Incident Report"
description: "Report a safety or reliability incident (evidence-first)"
title: "INC_YYYYMMDD_HHMM__<short_title>"
labels: ["incident"]
assignees:
  - nobutakayamauchi
body:
  - type: markdown
    attributes:
      value: |
        **Evidence-first. No inference beyond evidence.**
        Paste repository links (logs/incidents/radar). Do not paste secrets.

  - type: textarea
    id: summary
    attributes:
      label: Summary
      description: What happened?
      placeholder: "Short, factual description."
    validations:
      required: true

  - type: dropdown
    id: severity
    attributes:
      label: Severity
      options:
        - LOW
        - MED
        - HIGH
    validations:
      required: true

  - type: textarea
    id: impact
    attributes:
      label: Impact
      description: Who/what was affected?
      placeholder: "What broke or was at risk?"
    validations:
      required: true

  - type: textarea
    id: evidence
    attributes:
      label: Evidence (required)
      description: Paste repository evidence links
      placeholder: |
        - logs/...
        - incidents/...
        - radar/...
        - screenshots (if any)
    validations:
      required: true

  - type: textarea
    id: reproduction
    attributes:
      label: Reproduction
      description: Steps to reproduce (if applicable)
      placeholder: "1) ... 2) ... 3) ..."
    validations:
      required: false

  - type: textarea
    id: expected_actual
    attributes:
      label: Expected vs Actual
      placeholder: |
        Expected:
        Actual:
    validations:
      required: false

  - type: textarea
    id: mitigation
    attributes:
      label: Mitigation / Recovery
      description: How was the system stabilized?
    validations:
      required: false

  - type: textarea
    id: prevention
    attributes:
      label: Prevention
      description: What should change to prevent recurrence?
    validations:
      required: false

  - type: input
    id: operator_handle
    attributes:
      label: Operator handle
      placeholder: "@your-handle"
    validations:
      required: true

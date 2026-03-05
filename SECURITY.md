# Security Policy

## Overview

RTS (Real-Time Trust System) is an evidence-first operational logging framework.
It records execution history and links to repository artifacts.

RTS is not a security product.
It is a structural integrity and traceability system.

---

## Core Safety Principles

- No inference beyond evidence.
- Humans provide final judgment.
- Do not publish secrets or personal data.
- When uncertain, stop and request review.

---

## Prohibited Content (Do NOT Publish)

The following must never be committed publicly:

- API keys, tokens, passwords
- Private URLs, invoices, personal identifiers
- Private chat logs containing sensitive information
- Data without explicit disclosure rights
- Internal infrastructure credentials
- Personal data (GDPR-protected or similar)

---

## Reporting a Security Issue

If you believe RTS content exposes sensitive information:

1. **Do not open a public Issue.**
2. Redact or remove the sensitive artifact if possible.
3. Contact the maintainer privately.

High-impact issues should not be discussed in public threads.

---

## Operational Guardrails

- Public Issues and PRs must reference evidence links only.
- High-impact structural changes require Pull Request review.
- Maintainers may remove violating content without notice.

---

## Disclaimer

RTS does not guarantee correctness, privacy, or safety.
Use at your own risk and validate outputs independently.

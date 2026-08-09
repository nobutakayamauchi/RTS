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
- Do not use RTS with intent to cause harm or materially enable abuse.

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

## Prohibited Security-Abusive Use

The RTS license does not grant permission for intentional harmful or abusive use, including use intended to facilitate:

- unauthorized access;
- credential theft;
- malware deployment;
- fraud;
- stalking, harassment, or coercion;
- deliberate privacy invasion;
- destructive interference with systems or data;
- comparable bad-faith abuse.

Security research, defensive testing, audit, red-team work, and vulnerability analysis are not prohibited merely because they study harmful techniques; intent, authorization, scope, and actual use matter.

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
- Provenance and authorship records must not be intentionally falsified.

---

## License / Use Boundary

See `LICENSE` and `docs/legal/USE_POLICY.md` for the controlling grant and project-level acceptable-use policy.

---

## Disclaimer

RTS does not guarantee correctness, privacy, or safety.
Use at your own risk and validate outputs independently.

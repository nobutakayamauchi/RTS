from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SensitivityResult:
    level: str
    reasons: tuple[str, ...]
    public_export_allowed: bool


_SECRET_PATTERNS = (
    ("private_key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("github_token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b")),
    ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("generic_secret", re.compile(r"(?i)\b(?:api[_ -]?key|secret|password|token)\b\s*[:=]\s*[^\s]{8,}")),
)

# English alternatives can use word boundaries. Japanese text does not have
# whitespace-delimited words, so Japanese alternatives must be matched
# without \b boundaries.
_PERSONAL_PATTERNS = (
    ("email", re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)),
    ("phone", re.compile(r"(?<!\d)(?:0\d{1,4}-\d{1,4}-\d{3,4}|0\d{9,10})(?!\d)")),
    ("medical", re.compile(r"(?i)(?:\b(?:diagnosis|medical|hospital|medication)\b|診断|病院|服薬|症状|体調不良)")),
    ("employment_dispute", re.compile(r"(?i)(?:\b(?:harassment|dismissal|labor dispute)\b|パワハラ|退職勧奨|労働問題|カスハラ)")),
    ("financial", re.compile(r"(?i)(?:\b(?:bank account|credit card|debt)\b|口座|借金|カード番号|金銭難)")),
)


def assess_sensitivity(text: str, frontmatter: dict[str, Any] | None = None) -> SensitivityResult:
    metadata = frontmatter or {}

    # Content safety outranks user-provided publication metadata. A note cannot
    # mark a detected secret or protected personal category as public.
    secret_reasons = tuple(name for name, pattern in _SECRET_PATTERNS if pattern.search(text))
    if secret_reasons:
        return SensitivityResult("restricted", secret_reasons, False)

    personal_reasons = tuple(name for name, pattern in _PERSONAL_PATTERNS if pattern.search(text))
    if personal_reasons:
        return SensitivityResult("personal", personal_reasons, False)

    explicit = str(metadata.get("sensitivity", "")).lower()
    if explicit in {"public", "internal", "personal", "restricted"}:
        return SensitivityResult(explicit, ("explicit_frontmatter",), explicit == "public")

    if str(metadata.get("public", "")).lower() == "true" or metadata.get("public") is True:
        return SensitivityResult("public", ("explicit_public",), True)
    return SensitivityResult("internal", ("default_internal",), False)


def assert_public_export_allowed(result: SensitivityResult) -> None:
    if not result.public_export_allowed:
        raise PermissionError(f"public export blocked: {result.level} ({', '.join(result.reasons)})")

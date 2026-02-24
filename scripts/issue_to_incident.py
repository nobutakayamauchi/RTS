import os
import re
from datetime import datetime, timezone

ISSUE_NUMBER = os.environ.get("ISSUE_NUMBER", "")
ISSUE_TITLE = os.environ.get("ISSUE_TITLE", "")
ISSUE_BODY = os.environ.get("ISSUE_BODY", "")
ISSUE_URL = os.environ.get("ISSUE_URL", "")
REPO = os.environ.get("REPO", "")

INCIDENT_DIR = "incidents"


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def safe_slug(s: str, maxlen: int = 60) -> str:
    s = (s or "").lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = s.strip("_")
    return s[:maxlen] if s else "incident"


def extract_field(label: str, body: str) -> str:
    """
    GitHub Issue Form はだいたいこうなる:
    ### Summary
    text...

    なので「### {label}」の直後のブロックを拾う。
    旧形式 "label: value" もフォールバックで拾う。
    """
    if not body:
        return ""

    # 1) Issue Form (### Heading) 形式
    # 見出し直後～次の見出し(### )または末尾まで
    pattern = rf"(?is)^\s*###\s*{re.escape(label)}\s*\n(.*?)(?=^\s*###\s+|\Z)"
    m = re.search(pattern, body, flags=re.MULTILINE)
    if m:
        val = m.group(1).strip()
        # "No response" は空扱い
        if val.lower() == "no response":
            return ""
        return val

    # 2) "label: value" 形式（フォールバック）
    pattern2 = rf"(?im)^\s*{re.escape(label)}\s*:\s*(.+)$"
    m2 = re.search(pattern2, body)
    if m2:
        return m2.group(1).strip()

    return ""


def build_incident_md():
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    slug = safe_slug(ISSUE_TITLE)
    filename = f"INC_{ts}_{slug}.md"

    os.makedirs(INCIDENT_DIR, exist_ok=True)
    path = os.path.join(INCIDENT_DIR, filename)

    # Issue Body から拾う（フォームの見出し名と一致させる）
    operator_handle = extract_field("Operator Handle", ISSUE_BODY) or "unknown"
    severity = extract_field("Severity", ISSUE_BODY) or "unknown"

    content = f"""# RTS INCIDENT REPORT

incident_id: INC_{ts}

source_issue: {ISSUE_URL or ("#" + ISSUE_NUMBER)}

operator: {operator_handle}

severity: {severity}

created_at: {now_iso()}

---

## Summary

{ISSUE_TITLE}

---

## Issue Body

{ISSUE_BODY}

---

Generated automatically from GitHub Issue #{ISSUE_NUMBER}

Repository: {REPO}
"""

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    print("Incident file generated:", path)


if __name__ == "__main__":
    build_incident_md()

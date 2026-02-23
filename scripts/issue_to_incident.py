import os
import re
from datetime import datetime, timezone

ISSUE_NUMBER = os.environ.get("ISSUE_NUMBER", "unknown")
ISSUE_TITLE = os.environ.get("ISSUE_TITLE", "incident")
ISSUE_BODY = os.environ.get("ISSUE_BODY", "")
ISSUE_URL = os.environ.get("ISSUE_URL", "")
REPO = os.environ.get("REPO", "")

INCIDENT_DIR = "incidents"


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def safe_slug(s: str, maxlen: int = 40):
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s[:maxlen].strip("_") or "incident"


def extract_field(name, body):
    pattern = rf"{name}:(.*)"
    m = re.search(pattern, body, re.IGNORECASE)
    return m.group(1).strip() if m else "unknown"


def build_incident_md():

    ts = datetime.now().strftime("%Y%m%d_%H%M")

    slug = safe_slug(ISSUE_TITLE)

    filename = f"INC_{ts}_{slug}.md"

    os.makedirs(INCIDENT_DIR, exist_ok=True)

    path = os.path.join(INCIDENT_DIR, filename)

    operator = extract_field("operator", ISSUE_BODY)

    severity = extract_field("severity", ISSUE_BODY)

    content = f"""# RTS INCIDENT REPORT

incident_id: INC_{ts}

source_issue: {ISSUE_URL}

operator: {operator}

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

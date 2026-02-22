# vibecode/radar.py
# RTS AI Radar — minimal, robust, GitHub Actions friendly
# - Reads targets from radar/targets.txt
# - Fetches each URL (via r.jina.ai proxy for easier text extraction)
# - Detects "incident-like" complaints via keywords
# - Dedupes via seen.json
# - Writes:
#   - logs/RADAR_LOG.md (append)
#   - incidents/INC_YYYYMMDD_HHMM_System_RadarHit_<hash>.md
#   - radar/seen.json

import os
import re
import json
import hashlib
import datetime
import time
import urllib.request
import urllib.error
from typing import Dict, List, Tuple

TARGETS_PATH = "radar/targets.txt"
SEEN_PATH = "radar/seen.json"
RADAR_LOG_PATH = "logs/RADAR_LOG.md"
INC_DIR = "incidents"

# -----------------------
# Utilities
# -----------------------

def sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:12]

def now_jst_dt() -> datetime.datetime:
    return datetime.datetime.utcnow() + datetime.timedelta(hours=9)

def now_jst_str(fmt: str = "%Y%m%d_%H%M") -> str:
    return now_jst_dt().strftime(fmt)

def ensure_dirs() -> None:
    os.makedirs("radar", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    os.makedirs(INC_DIR, exist_ok=True)

def normalize_whitespace(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()

def safe_read_text(path: str) -> str:
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def safe_write_text(path: str, content: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def append_log(lines: List[str]) -> None:
    # Ensure file has a header if new
    if not os.path.exists(RADAR_LOG_PATH):
        safe_write_text(RADAR_LOG_PATH, "# RTS AI RADAR LOG\n\n")
    with open(RADAR_LOG_PATH, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

# -----------------------
# Targets / Seen store
# -----------------------

def load_targets() -> List[str]:
    """
    Each line in radar/targets.txt can be:
      - URL (https://...)
      - or with label: LABEL | https://...
    Comments:
      - lines starting with # are ignored
    """
    if not os.path.exists(TARGETS_PATH):
        # Create a default template to reduce confusion
        default = [
            "# RTS AI Radar targets",
            "# One per line:",
            "#   https://x.com/user/status/123...",
            "# or",
            "#   ClaudeCode | https://x.com/user/status/123...",
            "",
        ]
        safe_write_text(TARGETS_PATH, "\n".join(default))

    raw = safe_read_text(TARGETS_PATH).splitlines()
    targets: List[str] = []
    for line in raw:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # allow LABEL | URL
        if "|" in line:
            parts = [x.strip() for x in line.split("|", 1)]
            url = parts[1] if len(parts) == 2 else parts[0]
            line = url.strip()
        targets.append(line)

    # Basic cleanup
    targets = [t for t in targets if t.startswith("http://") or t.startswith("https://")]
    # de-dup order preserving
    seen = set()
    uniq = []
    for t in targets:
        if t not in seen:
            uniq.append(t)
            seen.add(t)
    return uniq

def load_seen() -> Dict:
    if os.path.exists(SEEN_PATH):
        try:
            with open(SEEN_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict) and "seen" in data and isinstance(data["seen"], list):
                return data
        except Exception:
            pass
    return {"seen": []}

def save_seen(seen: Dict) -> None:
    with open(SEEN_PATH, "w", encoding="utf-8") as f:
        json.dump(seen, f, ensure_ascii=False, indent=2)

# -----------------------
# Fetching
# -----------------------

def jina_proxy_url(url: str) -> str:
    # x.com本文は直取りが厳しいことが多いので r.jina.ai 経由にする
    # Example: https://r.jina.ai/http://x.com/...
    u = url.replace("https://", "").replace("http://", "")
    return "https://r.jina.ai/http://" + u

def fetch_text(url: str, timeout: int = 30) -> Tuple[str, str]:
    """
    Returns (text, source_url_used)
    Tries jina proxy first. If fails, tries direct.
    """
    headers = {"User-Agent": "Mozilla/5.0 (RTS-Radar)"}

    # 1) via jina proxy
    proxy = jina_proxy_url(url)
    try:
        req = urllib.request.Request(proxy, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            txt = r.read().decode("utf-8", errors="ignore")
            return txt, proxy
    except Exception:
        pass

    # 2) direct fallback
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            txt = r.read().decode("utf-8", errors="ignore")
            return txt, url
    except Exception as e:
        return f"FETCH_ERROR: {type(e).__name__}: {e}", url

# -----------------------
# Extraction / Detection
# -----------------------

KEYWORDS = [
    # breakage / instability
    "broken", "breaks", "unstable", "bug", "downtime", "outage", "not working", "stopped working",
    "regression", "degraded", "worse", "unusable", "frustrated",
    # instruction following / behavior changes
    "ignores", "ignored", "refuses", "reset", "resets", "changed", "behavior",
    # memory / context
    "context", "memory", "forget", "forgets", "lost", "loss", "leak",
    # errors
    "error", "500", "404", "429", "rate limit", "timeout",
    # common AI tool terms
    "custom gpt", "gpts", "gpt", "chatgpt", "claude", "cursor",
]

def extract_candidate_snippet(page_text: str) -> str:
    """
    Pick a meaningful line from fetched text.
    This is heuristic: choose the first long-ish non-empty line.
    """
    lines = [normalize_whitespace(x) for x in page_text.splitlines()]
    lines = [x for x in lines if x]

    # If fetch error, surface it
    if lines and lines[0].startswith("FETCH_ERROR:"):
        return lines[0][:300]

    # Prefer longer lines that likely include the complaint
    long_lines = [x for x in lines if len(x) >= 80]
    if long_lines:
        return long_lines[0][:600]

    # Otherwise, join a few short lines
    joined = " ".join(lines[:5])
    return joined[:400]

def classify_system(url: str, snippet: str) -> str:
    s = (url + " " + snippet).lower()
    if "cursor" in s:
        return "Cursor"
    if "claude" in s or "anthropic" in s:
        return "Claude"
    if "chatgpt" in s or "custom gpt" in s or "gpts" in s or re.search(r"\bgpt\b", s):
        return "ChatGPT"
    if "gemini" in s:
        return "Gemini"
    if "grok" in s:
        return "Grok"
    return "Other"

def should_create_incident(snippet: str) -> bool:
    s = snippet.lower()
    return any(k in s for k in KEYWORDS)

# -----------------------
# Incident creation
# -----------------------

def make_incident(url: str, snippet: str, fetched_via: str) -> str:
    """
    Writes an incident markdown file, returns filepath.
    """
    ts = now_jst_str("%Y%m%d_%H%M")
    system = classify_system(url, snippet)

    # Stable unique key per URL+snippet (so edits still create new)
    hit_hash = sha(url + "|" + snippet)

    incident_id = f"INC_{ts}_{system}_RadarHit_{hit_hash}"
    path = os.path.join(INC_DIR, f"{incident_id}.md")

    body = f"""# RTS INCIDENT REPORT

- Incident ID: {incident_id}
- Severity: S2
- System: {system}
- Status: OPEN

## Symptom
{snippet}

## Root Cause (Hypothesis)
Likely context/memory fragmentation, instruction-following regression, or workflow instability reported by user.

## Operational Impact
Operator must rebuild context manually, losing time and continuity.

## RTS Intervention
Log execution decisions + evidence links to preserve operational memory across sessions.

## Evidence
- Source URL: {url}
- Fetched via: {fetched_via}

## Notes
- Auto-generated by RTS AI Radar.
"""
    safe_write_text(path, body)
    return path

# -----------------------
# Main
# -----------------------

def main() -> None:
    ensure_dirs()

    targets = load_targets()
    seen = load_seen()
    seen_set = set(seen.get("seen", []))

    run_ts = now_jst_str("%Y-%m-%d %H:%M JST")
    lines = [
        "",
        f"## Run — {run_ts}",
        f"- Targets: {len(targets)}",
    ]

    created = 0
    skipped_seen = 0
    skipped_nohit = 0
    fetch_errors = 0

    if not targets:
        lines.append("- Result: No targets found. Add URLs to `radar/targets.txt`.")
        append_log(lines)
        save_seen(seen)
        return

    for i, url in enumerate(targets, start=1):
        # A short polite delay to reduce rate limit risk (especially with proxy)
        time.sleep(0.4)

        page_text, fetched_via = fetch_text(url)
        snippet = extract_candidate_snippet(page_text)

        # create a "hit id" for dedupe
        hit_id = sha(url + "|" + snippet)

        if snippet.startswith("FETCH_ERROR:"):
            fetch_errors += 1
            lines.append(f"- [{i}/{len(targets)}] FETCH_ERROR {url} :: {snippet}")
            # Still mark as seen? No. (keep retrying next run)
            continue

        if hit_id in seen_set:
            skipped_seen += 1
            continue

        # Mark as seen regardless of incident or not to avoid noisy repeats
        seen_set.add(hit_id)
        seen["seen"] = list(seen_set)

        if should_create_incident(snippet):
            path = make_incident(url, snippet, fetched_via)
            created += 1
            lines.append(f"- ✅ Incident: `{path}`")
            lines.append(f"  - URL: {url}")
            lines.append(f"  - Snippet: {snippet[:180]}{'...' if len(snippet) > 180 else ''}")
        else:
            skipped_nohit += 1

    lines.append("")
    lines.append("### Summary")
    lines.append(f"- Incidents created: {created}")
    lines.append(f"- Skipped (already seen): {skipped_seen}")
    lines.append(f"- Skipped (no incident keywords): {skipped_nohit}")
    lines.append(f"- Fetch errors: {fetch_errors}")

    append_log(lines)
    save_seen(seen)

if __name__ == "__main__":
    main()

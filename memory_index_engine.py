#!/usr/bin/env python3
# memory_index_engine.py
# RTS Memory Index Engine (deterministic, GitHub Actions friendly)
# - Generates:
#     memory/index.md   (human)
#     memory/index.json (machine)
#
# Inputs:
#   logs/        *.md  (BLOCK_*.md, EXECUTION_LOG.md, RADAR_LOG.md, etc)
#   incidents/   *.md  (INC_*.md, templates, standards)
#   radar/       (optional)
#
# No external deps.

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Iterable, Optional, Tuple, List, Dict

JST = timezone(timedelta(hours=9))

REPO_ROOT = Path(".")
LOGS_DIR = REPO_ROOT / "logs"
INCIDENTS_DIR = REPO_ROOT / "incidents"
MEMORY_DIR = REPO_ROOT / "memory"
OUT_MD = MEMORY_DIR / "index.md"
OUT_JSON = MEMORY_DIR / "index.json"

MAX_LATEST_LOGS = 12
MAX_LATEST_INCIDENTS = 25
SNIPPET_MAX_CHARS = 380

# Files to exclude from indexing (noise)
EXCLUDE_LOG_FILES = {
    ".DS_Store",
}
EXCLUDE_INCIDENT_FILES = {
    ".DS_Store",
}

# Prefer these logs first in "Latest Logs" ordering
PREFERRED_LOG_ORDER = [
    "RADAR_LOG.md",
    "EXECUTION_LOG.md",
]


@dataclass
class DocItem:
    kind: str               # "log" | "incident"
    path: str               # posix path
    name: str               # filename
    mtime_utc: str          # ISO
    title: str              # extracted or fallback
    url: Optional[str]      # first URL found (optional)
    snippet: str            # short excerpt
    score: float            # for incident sorting (severity etc)


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_text_safe(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def first_url(text: str) -> Optional[str]:
    m = re.search(r"(https?://\S+)", text)
    if not m:
        return None
    # strip trailing punctuation
    url = m.group(1).rstrip(").,]}")
    return url


def normalize_ws(s: str) -> str:
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    # collapse too many blank lines
    s = re.sub(r"\n{4,}", "\n\n\n", s)
    return s


def extract_title(text: str, fallback: str) -> str:
    """
    Try to extract a meaningful title:
    - First Markdown heading (# ...)
    - Or "Event:" line
    - Or "Title:" line
    """
    text = normalize_ws(text)

    m = re.search(r"^\s*#\s+(.+?)\s*$", text, re.MULTILINE)
    if m:
        return m.group(1).strip()

    m = re.search(r"^\s*Event:\s*(.+?)\s*$", text, re.MULTILINE)
    if m:
        return m.group(1).strip()

    m = re.search(r"^\s*Title:\s*(.+?)\s*$", text, re.MULTILINE)
    if m:
        return m.group(1).strip()

    # Block id line like "BLOCK_00000017"
    m = re.search(r"^\s*(BLOCK_\d+)\s*$", text, re.MULTILINE)
    if m:
        return m.group(1).strip()

    return fallback


def extract_snippet(text: str, max_chars: int = SNIPPET_MAX_CHARS) -> str:
    text = normalize_ws(text).strip()
    if not text:
        return ""
    # Prefer a small slice after first title/event lines
    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
    if not lines:
        return ""
    # remove huge code fences if present
    compact = []
    in_code = False
    for ln in lines:
        if ln.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        compact.append(ln)
    if not compact:
        compact = lines

    joined = " ".join(compact)
    if len(joined) > max_chars:
        return joined[: max_chars - 1].rstrip() + "…"
    return joined


def file_mtime_utc_iso(p: Path) -> str:
    try:
        ts = p.stat().st_mtime
        return datetime.fromtimestamp(ts, tz=timezone.utc).replace(microsecond=0).isoformat()
    except Exception:
        return now_utc_iso()


def severity_score(text: str) -> float:
    """
    Heuristic for incident severity and importance.
    Looks for:
      - "Severity: S1/S2/S3"
      - "Status: OPEN"
      - keywords
    Higher = more important.
    """
    t = text.lower()
    score = 0.0

    # Severity
    m = re.search(r"severity\s*:\s*(s1|s2|s3)", text, re.IGNORECASE)
    if m:
        sev = m.group(1).upper()
        if sev == "S1":
            score += 100
        elif sev == "S2":
            score += 60
        elif sev == "S3":
            score += 30

    # Status
    if re.search(r"status\s*:\s*open", text, re.IGNORECASE):
        score += 20
    if re.search(r"status\s*:\s*closed", text, re.IGNORECASE):
        score -= 5

    # Keywords
    for kw, pts in [
        ("data loss", 30),
        ("context loss", 25),
        ("integrity", 15),
        ("critical", 20),
        ("failure", 10),
        ("error", 8),
        ("500", 8),
        ("404", 6),
        ("timeout", 6),
    ]:
        if kw in t:
            score += pts

    return score


def iter_docs() -> List[DocItem]:
    docs: List[DocItem] = []

    # Logs
    if LOGS_DIR.exists():
        for p in sorted(LOGS_DIR.glob("*.md")):
            if p.name in EXCLUDE_LOG_FILES:
                continue
            txt = read_text_safe(p)
            docs.append(
                DocItem(
                    kind="log",
                    path=p.as_posix(),
                    name=p.name,
                    mtime_utc=file_mtime_utc_iso(p),
                    title=extract_title(txt, fallback=p.name),
                    url=first_url(txt),
                    snippet=extract_snippet(txt),
                    score=0.0,
                )
            )

    # Incidents
    if INCIDENTS_DIR.exists():
        for p in sorted(INCIDENTS_DIR.glob("*.md")):
            if p.name in EXCLUDE_INCIDENT_FILES:
                continue
            txt = read_text_safe(p)
            docs.append(
                DocItem(
                    kind="incident",
                    path=p.as_posix(),
                    name=p.name,
                    mtime_utc=file_mtime_utc_iso(p),
                    title=extract_title(txt, fallback=p.name),
                    url=first_url(txt),
                    snippet=extract_snippet(txt),
                    score=severity_score(txt),
                )
            )

    return docs


def sort_latest_logs(items: List[DocItem]) -> List[DocItem]:
    logs = [d for d in items if d.kind == "log"]

    # Bring preferred files first if present (RADAR_LOG, EXECUTION_LOG)
    preferred = []
    remaining = logs[:]
    for fname in PREFERRED_LOG_ORDER:
        for d in logs:
            if d.name == fname:
                preferred.append(d)
                if d in remaining:
                    remaining.remove(d)

    # Then rest by mtime desc
    remaining.sort(key=lambda d: d.mtime_utc, reverse=True)

    merged = preferred + remaining
    # Deduplicate in case
    seen = set()
    out = []
    for d in merged:
        if d.path in seen:
            continue
        seen.add(d.path)
        out.append(d)
    return out[:MAX_LATEST_LOGS]


def sort_incidents(items: List[DocItem]) -> List[DocItem]:
    inc = [d for d in items if d.kind == "incident"]

    # Primary: score desc, Secondary: mtime desc
    inc.sort(key=lambda d: (d.score, d.mtime_utc), reverse=True)

    # Keep templates/standards lower priority if needed
    def is_template(name: str) -> bool:
        return "template" in name.lower() or "standard" in name.lower() or "rules" in name.lower()

    main = [d for d in inc if not is_template(d.name)]
    misc = [d for d in inc if is_template(d.name)]
    out = main + misc
    return out[:MAX_LATEST_INCIDENTS]


def human_time_from_iso(iso_utc: str) -> str:
    # show JST date for readability
    try:
        dt = datetime.fromisoformat(iso_utc.replace("Z", "+00:00"))
        jst = dt.astimezone(JST)
        return jst.strftime("%Y-%m-%d %H:%M JST")
    except Exception:
        return iso_utc


def build_markdown(latest_logs: List[DocItem], incidents: List[DocItem], all_docs: List[DocItem]) -> str:
    generated_utc = now_utc_iso()

    lines: List[str] = []
    lines.append("# RTS MEMORY INDEX")
    lines.append("")
    lines.append(f"- generated_utc: `{generated_utc}`")
    lines.append(f"- docs: `{len(all_docs)}`")
    lines.append(f"- logs: `{len([d for d in all_docs if d.kind=='log'])}`")
    lines.append(f"- incidents: `{len([d for d in all_docs if d.kind=='incident'])}`")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Latest Logs
    lines.append("## Latest Logs")
    lines.append("")
    if not latest_logs:
        lines.append("- (no logs found)")
    else:
        for d in latest_logs:
            lines.append(f"- **{d.name}**")
            lines.append(f"  - path: `{d.path}`")
            lines.append(f"  - time: {human_time_from_iso(d.mtime_utc)}")
            if d.url:
                lines.append(f"  - url: {d.url}")
            if d.title and d.title != d.name:
                lines.append(f"  - event: {d.title}")
            if d.snippet:
                lines.append(f"  - snippet: {d.snippet}")
            lines.append("")
    lines.append("---")
    lines.append("")

    # Incidents
    lines.append("## Incidents")
    lines.append("")
    if not incidents:
        lines.append("- (no incidents found)")
    else:
        for d in incidents:
            lines.append(f"- **{d.title}** (`{d.name}`)")
            lines.append(f"  - path: `{d.path}`")
            lines.append(f"  - time: {human_time_from_iso(d.mtime_utc)}")
            if d.score:
                lines.append(f"  - score: `{d.score:.1f}`")
            if d.url:
                lines.append(f"  - url: {d.url}")
            if d.snippet:
                lines.append(f"  - snippet: {d.snippet}")
            lines.append("")
    lines.append("---")
    lines.append("")

    # Navigation
    lines.append("## Navigation")
    lines.append("")
    lines.append("- logs/ → execution evidence")
    lines.append("- incidents/ → failure intelligence")
    lines.append("- radar/ → incident radar system")
    lines.append("- memory/ → indexes and summaries")
    lines.append("")
    lines.append("> Integrity: VERIFIED")
    lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def build_json(latest_logs: List[DocItem], incidents: List[DocItem], all_docs: List[DocItem]) -> Dict:
    return {
        "generated_utc": now_utc_iso(),
        "counts": {
            "docs": len(all_docs),
            "logs": len([d for d in all_docs if d.kind == "log"]),
            "incidents": len([d for d in all_docs if d.kind == "incident"]),
        },
        "latest_logs": [
            {
                "name": d.name,
                "path": d.path,
                "mtime_utc": d.mtime_utc,
                "title": d.title,
                "url": d.url,
                "snippet": d.snippet,
            }
            for d in latest_logs
        ],
        "incidents": [
            {
                "name": d.name,
                "path": d.path,
                "mtime_utc": d.mtime_utc,
                "title": d.title,
                "url": d.url,
                "snippet": d.snippet,
                "score": d.score,
            }
            for d in incidents
        ],
    }


def write_if_changed(path: Path, content: str) -> bool:
    """
    Writes only if content differs. Returns True if changed.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    old = ""
    if path.exists():
        old = read_text_safe(path)
    if old == content:
        return False
    path.write_text(content, encoding="utf-8")
    return True


def write_json_if_changed(path: Path, obj: Dict) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    new = json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    old = ""
    if path.exists():
        old = read_text_safe(path)
    if old == new:
        return False
    path.write_text(new, encoding="utf-8")
    return True


def main() -> None:
    # Ensure dirs exist
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)

    all_docs = iter_docs()
    latest_logs = sort_latest_logs(all_docs)
    top_incidents = sort_incidents(all_docs)

    md = build_markdown(latest_logs, top_incidents, all_docs)
    js = build_json(latest_logs, top_incidents, all_docs)

    changed_md = write_if_changed(OUT_MD, md)
    changed_js = write_json_if_changed(OUT_JSON, js)

    print(f"[memory_index_engine] docs={len(all_docs)} logs={len([d for d in all_docs if d.kind=='log'])} incidents={len([d for d in all_docs if d.kind=='incident'])}")
    print(f"[memory_index_engine] wrote index.md: {changed_md}")
    print(f"[memory_index_engine] wrote index.json: {changed_js}")

    # Exit success always
    return


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
RTS Analyze (Auto-Generated)

Generates analyze/index.md from:
- memory/index.md (preferred aggregator)
- incidents/*.md (fallback + enrichment)
- logs/*.md (optional fallback)

Design goals:
- Evidence-first: link to underlying files/URLs
- Minimal assumptions: parse what's there, don't invent
- Stable output structure for GitHub Pages
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple, Dict

REPO_ROOT = Path(__file__).resolve().parents[1]
MEMORY_INDEX = REPO_ROOT / "memory" / "index.md"
INCIDENTS_DIR = REPO_ROOT / "incidents"
LOGS_DIR = REPO_ROOT / "logs"
ANALYZE_INDEX = REPO_ROOT / "analyze" / "index.md"


@dataclass
class Incident:
    file_path: str
    time: Optional[str] = None
    score: Optional[str] = None
    title: Optional[str] = None
    url: Optional[str] = None
    snippet: Optional[str] = None


@dataclass
class LogEntry:
    file_path: str
    time: Optional[str] = None
    event: Optional[str] = None
    url: Optional[str] = None
    snippet: Optional[str] = None


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def read_text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def write_text(p: Path, s: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding="utf-8")


def md_link(text: str, href: str) -> str:
    return f"[{text}]({href})"


def rel_link_from_analyze(rel_path: str) -> str:
    """
    analyze/index.md is located at /analyze/index.md
    so linking to repo root files should be ../<path>
    """
    rel_path = rel_path.lstrip("./").lstrip("/")
    return f"../{rel_path}"


def parse_memory_index(memory_md: str) -> Tuple[List[LogEntry], List[Incident], dict]:
    """
    Parses memory/index.md for:
    - docs/logs/incidents counts
    - generated utc timestamp
    - Latest Logs entries
    - Incidents entries

    This parser is resilient (best-effort).
    """
    meta: Dict[str, object] = {}

    for key in ["docs", "logs", "incidents"]:
        m = re.search(rf"^\s*-\s*{re.escape(key)}\s*:\s*([0-9]+)\s*$", memory_md, flags=re.MULTILINE)
        if m:
            meta[key] = int(m.group(1))

    m = re.search(r"^\s*-\s*generated utc:\s*`([^`]+)`\s*$", memory_md, flags=re.MULTILINE)
    if m:
        meta["generated_utc"] = m.group(1)

    latest_logs: List[LogEntry] = []
    incidents: List[Incident] = []

    def extract_section(section_name: str) -> str:
        # from "## <section_name>" to next "## "
        m1 = re.search(rf"^##\s+{re.escape(section_name)}\s*$", memory_md, flags=re.MULTILINE)
        if not m1:
            return ""
        start = m1.end()
        m2 = re.search(r"^##\s+", memory_md[start:], flags=re.MULTILINE)
        end = start + m2.start() if m2 else len(memory_md)
        return memory_md[start:end]

    latest_logs_block = extract_section("Latest Logs")
    incidents_block = extract_section("Incidents")

    # Latest Logs: main bullets "- FILE.md" with sub-bullets "- path: ..."
    if latest_logs_block.strip():
        # split on "- " at line start
        chunks = re.split(r"(?m)^\s*-\s+", latest_logs_block)
        for ch in chunks:
            ch = ch.strip()
            if not ch:
                continue
            lines = ch.splitlines()
            name = lines[0].strip()
            if not name.endswith(".md"):
                continue
            props = "\n".join(lines[1:])
            path = _find_prop(props, "path") or f"logs/{name}"
            latest_logs.append(
                LogEntry(
                    file_path=path.strip(),
                    time=_find_prop(props, "time"),
                    event=_find_prop(props, "event"),
                    url=_find_prop(props, "url") or _find_prop(props, "URL"),
                    snippet=_find_prop(props, "snippet") or _find_prop(props, "Snippet"),
                )
            )

    # Incidents: detect "(INC_....md)" and read nearby fields
    if incidents_block.strip():
        pattern = re.compile(r"$begin:math:text$\(INC\_\[\^\)\]\+\\\.md\)$end:math:text$")
        for m in pattern.finditer(incidents_block):
            fname = m.group(1).strip()

            # Take a local window around the match to find props
            window = incidents_block[max(0, m.start() - 500): min(len(incidents_block), m.end() + 800)]
            inc = Incident(
                file_path=f"incidents/{fname}",
                time=_find_prop(window, "time") or _find_prop(window, "Time"),
                score=_find_prop(window, "score") or _find_prop(window, "Score"),
                url=_find_prop(window, "url") or _find_prop(window, "URL") or _find_prop(window, "Evidence"),
                snippet=_find_prop(window, "snippet") or _find_prop(window, "Snippet"),
            )
            inc.title = _guess_incident_title(window)
            incidents.append(inc)

    # Dedup by file_path
    dedup: Dict[str, Incident] = {}
    for inc in incidents:
        if inc.file_path not in dedup:
            dedup[inc.file_path] = inc
    incidents = list(dedup.values())

    return latest_logs, incidents, meta


def _find_prop(text: str, key: str) -> Optional[str]:
    # "- key: value"
    m = re.search(rf"(?m)^\s*-\s*{re.escape(key)}\s*:\s*(.+?)\s*$", text)
    if m:
        return m.group(1).strip()
    # "key: value"
    m = re.search(rf"(?m)^\s*{re.escape(key)}\s*:\s*(.+?)\s*$", text)
    if m:
        return m.group(1).strip()
    return None


def _guess_incident_title(window: str) -> Optional[str]:
    m = re.search(r"(?m)^\s*Title:\s*([^\n]+)", window)
    if m:
        return m.group(1).strip()
    m = re.search(r"(?m)^\s*##\s+(.+)$", window)
    if m:
        return m.group(1).strip()
    return None


def list_recent_incident_files(limit: int = 10) -> List[Path]:
    if not INCIDENTS_DIR.exists():
        return []
    files = sorted(INCIDENTS_DIR.glob("INC_*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[:limit]


def parse_incident_file(p: Path) -> Incident:
    t = read_text(p)

    time = _find_prop(t, "Time") or _find_prop(t, "time")
    score = _find_prop(t, "Score") or _find_prop(t, "score")

    # Evidence/URL could be a link line or "Evidence: <url>"
    url = _find_prop(t, "Evidence") or _find_prop(t, "URL") or _find_prop(t, "url")

    title = None
    m = re.search(r"(?m)^\s*#\s+(.+)$", t)
    if m:
        title = m.group(1).strip()

    snippet = None
    m = re.search(r"(?ms)^\s*##\s+Symptom[s]?\s*\n(.+?)(\n##|\Z)", t)
    if m:
        snippet = re.sub(r"\s+", " ", m.group(1).strip())[:240]

    return Incident(
        file_path=str(p.relative_to(REPO_ROOT)).replace("\\", "/"),
        time=time,
        score=score,
        title=title,
        url=url,
        snippet=snippet,
    )


def compute_risk_topics(incidents: List[Incident]) -> List[Tuple[str, int]]:
    """
    Very robust, very conservative:
    - count keyword hits from title/snippet
    - does not invent taxonomy
    """
    keywords = [
        ("context loss / memory fragmentation", ["context loss", "context", "memory fragmentation", "memory"]),
        ("session reset discontinuity", ["session", "reset", "discontinuity"]),
        ("workflow / kernel interruption", ["workflow", "actions", "kernel", "autonomous", "runner"]),
        ("server / internal error", ["500", "404", "internal server error", "server error"]),
        ("tool failure", ["failed", "failure", "error", "timeout"]),
    ]
    counts: Dict[str, int] = {label: 0 for label, _ in keywords}

    def hay(inc: Incident) -> str:
        return " ".join([inc.title or "", inc.snippet or ""]).lower()

    for inc in incidents:
        h = hay(inc)
        for label, toks in keywords:
            if any(tok in h for tok in toks):
                counts[label] += 1

    ranked = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    nonzero = [x for x in ranked if x[1] > 0]
    return nonzero[:5] if nonzero else ranked[:3]


def best_effort_latest_execution_log(latest_logs: List[LogEntry]) -> Optional[LogEntry]:
    """
    Prefer EXECUTION_LOG.md from memory index list; else find in logs dir.
    """
    for le in latest_logs:
        if le.file_path.replace("\\", "/").endswith("EXECUTION_LOG.md"):
            return le

    # Fallback: logs/EXECUTION_LOG.md
    p = LOGS_DIR / "EXECUTION_LOG.md"
    if p.exists():
        return LogEntry(file_path="logs/EXECUTION_LOG.md")
    return None


def render_analyze_md(
    latest_logs: List[LogEntry],
    incidents: List[Incident],
    meta: dict,
) -> str:
    generated_utc = meta.get("generated_utc") or now_utc_iso()
    docs_n = meta.get("docs")
    logs_n = meta.get("logs")
    inc_n = meta.get("incidents")

    # Build incident list (top N)
    top_incidents = incidents[:10]

    # Execution stability evidence
    exec_log = best_effort_latest_execution_log(latest_logs)

    # Risk topics
    risk_topics = compute_risk_topics(incidents)

    lines: List[str] = []
    lines.append("<!-- AUTO-GENERATED. DO NOT EDIT DIRECTLY. -->")
    lines.append("")
    lines.append("# RTS ANALYZE")
    lines.append("")
    lines.append("Operational pattern analysis from execution history (evidence-first).")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Snapshot")
    lines.append("")
    lines.append(f"- generated utc: `{generated_utc}`")
    if docs_n is not None:
        lines.append(f"- docs: `{docs_n}`")
    if logs_n is not None:
        lines.append(f"- logs: `{logs_n}`")
    if inc_n is not None:
        lines.append(f"- incidents: `{inc_n}`")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Incident Trend
    lines.append("## Incident Trend")
    lines.append("")
    if not top_incidents:
        lines.append("- No incidents detected (or none parsed).")
    else:
        for inc in top_incidents:
            file_href = rel_link_from_analyze(inc.file_path)
            title = inc.title or Path(inc.file_path).name
            row = f"- {md_link(title, file_href)}"
            meta_bits = []
            if inc.score:
                meta_bits.append(f"score: {inc.score}")
            if inc.time:
                meta_bits.append(f"time: {inc.time}")
            if meta_bits:
                row += f" — ({', '.join(meta_bits)})"
            lines.append(row)
            if inc.url:
                lines.append(f"  - evidence: {inc.url}")
            if inc.snippet:
                lines.append(f"  - note: {inc.snippet}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Execution Stability
    lines.append("## Execution Stability")
    lines.append("")
    if exec_log:
        href = rel_link_from_analyze(exec_log.file_path)
        lines.append(f"- evidence: {md_link(exec_log.file_path, href)}")
        if exec_log.time:
            lines.append(f"- last recorded time: `{exec_log.time}`")
        if exec_log.event:
            lines.append(f"- last event: `{exec_log.event}`")
        lines.append("- status: `ACTIVE` (based on latest execution evidence when available)")
    else:
        lines.append("- evidence: (missing) EXECUTION_LOG.md not found.")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Observed Risk Patterns
    lines.append("## Observed Risk Patterns")
    lines.append("")
    if risk_topics:
        for label, count in risk_topics:
            lines.append(f"- {label}: `{count}`")
    else:
        lines.append("- (no patterns computed)")
    lines.append("")
    lines.append("Operator verification recommended for destructive actions.")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Governance Signals
    lines.append("## Governance Signals")
    lines.append("")
    lines.append("- Backup-first enforcement: `ACTIVE`")
    lines.append("- AI destructive instruction verification: `REQUIRED`")
    lines.append("- Deletion treated as last resort; branch/tag preservation preferred.")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Navigation
    lines.append("## Navigation")
    lines.append("")
    lines.append(f"- memory index: {md_link('memory/index.md', rel_link_from_analyze('memory/index.md'))}")
    lines.append(f"- incidents: {md_link('incidents/', rel_link_from_analyze('incidents/'))}")
    lines.append(f"- logs: {md_link('logs/', rel_link_from_analyze('logs/'))}")
    lines.append("")
    lines.append("RTS Analyze converts execution into understanding.")
    lines.append("")

    return "\n".join(lines)


def main() -> int:
    # 1) Prefer memory/index.md
    latest_logs: List[LogEntry] = []
    incidents: List[Incident] = []
    meta: dict = {}

    memory_md = read_text(MEMORY_INDEX)
    if memory_md.strip():
        ll, incs, m = parse_memory_index(memory_md)
        latest_logs = ll
        incidents = incs
        meta = m

    # 2) Fallback/enrichment: if incidents empty, read recent incident files directly
    if not incidents:
        for p in list_recent_incident_files(limit=10):
            incidents.append(parse_incident_file(p))

    # 3) Sort incidents by mtime desc if possible (stable “latest first”)
    def mtime_of_inc(inc: Incident) -> float:
        p = REPO_ROOT / inc.file_path
        try:
            return p.stat().st_mtime
        except Exception:
            return 0.0

    incidents = sorted(incidents, key=mtime_of_inc, reverse=True)

    md = render_analyze_md(latest_logs=latest_logs, incidents=incidents, meta=meta)
    write_text(ANALYZE_INDEX, md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

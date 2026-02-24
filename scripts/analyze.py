#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
RTS Analyze (Stable)

Generate analyze/index.md from:
- memory/index.md (preferred aggregator, if exists)
- incidents/*.md (fallback + enrichment)
- logs/ (optional, for lightweight counters)

Design:
- Evidence-first: always link to underlying files/URLs when possible
- Minimal assumptions: parse what's there; don't invent
- Stable output for GitHub Pages

Outputs:
- analyze/index.md
"""

from __future__ import annotations

import re
import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ----------------------------
# Paths
# ----------------------------
ROOT = Path(__file__).resolve().parents[1]
LOGS_DIR = ROOT / "logs"
INCIDENTS_DIR = ROOT / "incidents"
MEMORY_DIR = ROOT / "memory"
MEMORY_INDEX = MEMORY_DIR / "index.md"

OUTPUT_DIR = ROOT / "analyze"
OUTPUT_FILE = OUTPUT_DIR / "index.md"

JST = timezone(timedelta(hours=9))

# ----------------------------
# Helpers
# ----------------------------
def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def jst_now_iso() -> str:
    return datetime.now(JST).replace(microsecond=0).isoformat()

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except Exception:
        return str(path)

def safe_md(s: str) -> str:
    return s.replace("\r\n", "\n").replace("\r", "\n")

def md_link(text: str, path_or_url: str) -> str:
    return f"[{text}]({path_or_url})"

# ----------------------------
# Parsing
# ----------------------------
KV_LINE = re.compile(r"^\s*([A-Za-z0-9_\-]+)\s*:\s*(.*?)\s*$")
INC_ID_RE = re.compile(r"\bINC_\d{8}_\d{4}\b")
ISO_TS_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+\-]\d{2}:\d{2})\b")

def extract_first(pattern: re.Pattern, text: str) -> Optional[str]:
    m = pattern.search(text)
    return m.group(0) if m else None

def parse_front_kv(text: str) -> Dict[str, str]:
    """
    Lightweight parser:
    - reads lines, collects 'key: value'
    - stops if too deep into body? (we keep scanning but only store first occurrence)
    """
    out: Dict[str, str] = {}
    for line in safe_md(text).split("\n"):
        m = KV_LINE.match(line)
        if m:
            k = m.group(1).strip()
            v = m.group(2).strip()
            if k not in out and v:
                out[k] = v
    return out

def extract_urls(text: str) -> List[str]:
    # very permissive
    urls = re.findall(r"https?://[^\s)>\]]+", text)
    # de-dup preserve order
    seen = set()
    out = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out

@dataclass
class Incident:
    path: Path
    incident_id: str
    created_at: Optional[str]
    severity: Optional[str]
    status: Optional[str]
    operator: Optional[str]
    evidence_urls: List[str]
    file_hash_sha256: str

def parse_incident_file(path: Path) -> Incident:
    text = path.read_text(encoding="utf-8", errors="replace")
    kv = parse_front_kv(text)

    incident_id = kv.get("incident_id") or kv.get("incident-id") or extract_first(INC_ID_RE, text) or path.stem
    created_at = kv.get("created_at") or kv.get("created-at") or kv.get("created") or extract_first(ISO_TS_RE, text)
    severity = kv.get("severity")
    status = kv.get("status")
    operator = kv.get("operator")

    urls = extract_urls(text)

    # If evidence is mentioned but no URL, still keep empty list (no invention)
    file_hash = sha256_file(path)

    return Incident(
        path=path,
        incident_id=incident_id,
        created_at=created_at,
        severity=severity,
        status=status,
        operator=operator,
        evidence_urls=urls,
        file_hash_sha256=file_hash,
    )

# ----------------------------
# Collectors
# ----------------------------
def collect_incidents() -> List[Incident]:
    if not INCIDENTS_DIR.exists():
        return []
    items: List[Incident] = []
    for p in sorted(INCIDENTS_DIR.glob("INC_*.md")):
        try:
            items.append(parse_incident_file(p))
        except Exception:
            # skip broken file rather than failing whole build
            continue

    # Newest first if we can parse created_at, else by filename
    def sort_key(it: Incident):
        ts = it.created_at or ""
        return (ts, it.incident_id)
    items.sort(key=sort_key, reverse=True)
    return items

def count_logs() -> Dict[str, int]:
    """
    Optional lightweight counters:
    counts files in logs/ by extension and total lines
    """
    out = {
        "files": 0,
        "lines": 0,
    }
    if not LOGS_DIR.exists():
        return out

    for p in LOGS_DIR.rglob("*"):
        if p.is_file():
            out["files"] += 1
            try:
                # count lines cheaply
                out["lines"] += sum(1 for _ in p.open("r", encoding="utf-8", errors="ignore"))
            except Exception:
                continue
    return out

def read_memory_index_excerpt(max_lines: int = 120) -> Tuple[bool, str]:
    if not MEMORY_INDEX.exists():
        return (False, "")
    try:
        lines = MEMORY_INDEX.read_text(encoding="utf-8", errors="replace").splitlines()
        excerpt = "\n".join(lines[:max_lines]).strip()
        return (True, excerpt)
    except Exception:
        return (False, "")

# ----------------------------
# Rendering
# ----------------------------
def render_header() -> str:
    return "\n".join([
        "# RTS Analyze Index",
        "",
        "- generated_at_utc: " + utc_now_iso(),
        "- generated_at_jst: " + jst_now_iso(),
        "",
        "RTS generates evidence-first operational memory.",
        "",
        "---",
        "",
    ])

def render_memory_section() -> str:
    exists, excerpt = read_memory_index_excerpt()
    if not exists:
        return "\n".join([
            "## Memory Index",
            "",
            "- status: missing (memory/index.md not found)",
            "",
            "---",
            "",
        ])

    return "\n".join([
        "## Memory Index",
        "",
        f"- file: {md_link(rel(MEMORY_INDEX), rel(MEMORY_INDEX))}",
        f"- sha256: `{sha256_file(MEMORY_INDEX)}`",
        "",
        "### Excerpt",
        "",
        "```text",
        excerpt,
        "```",
        "",
        "---",
        "",
    ])

def render_logs_section() -> str:
    c = count_logs()
    if c["files"] == 0:
        return "\n".join([
            "## Logs (Lightweight)",
            "",
            "- status: empty or missing",
            "",
            "---",
            "",
        ])
    return "\n".join([
        "## Logs (Lightweight)",
        "",
        f"- dir: {md_link(rel(LOGS_DIR), rel(LOGS_DIR))}",
        f"- files: {c['files']}",
        f"- lines: {c['lines']}",
        "",
        "---",
        "",
    ])

def render_incidents_section(incidents: List[Incident], limit: int = 50) -> str:
    lines: List[str] = []
    lines.extend([
        "## Incidents",
        "",
        f"- count: {len(incidents)}",
        f"- dir: {md_link(rel(INCIDENTS_DIR), rel(INCIDENTS_DIR))}",
        "",
    ])

    if not incidents:
        lines.extend([
            "_No incident files found._",
            "",
            "---",
            "",
        ])
        return "\n".join(lines)

    lines.append("### Latest")
    lines.append("")
    for it in incidents[:limit]:
        lines.append(f"#### {it.incident_id}")
        lines.append("")
        lines.append(f"- file: {md_link(rel(it.path), rel(it.path))}")
        if it.created_at:
            lines.append(f"- created_at: `{it.created_at}`")
        if it.severity:
            lines.append(f"- severity: `{it.severity}`")
        if it.status:
            lines.append(f"- status: `{it.status}`")
        if it.operator:
            lines.append(f"- operator: `{it.operator}`")
        lines.append(f"- file_sha256: `{it.file_hash_sha256}`")

        if it.evidence_urls:
            lines.append("- evidence_urls:")
            for u in it.evidence_urls[:10]:
                lines.append(f"  - {u}")
            if len(it.evidence_urls) > 10:
                lines.append(f"  - ... ({len(it.evidence_urls) - 10} more)")
        else:
            lines.append("- evidence_urls: (none detected)")

        lines.append("")
    lines.extend([
        "---",
        "",
    ])
    return "\n".join(lines)

def render_footer() -> str:
    return "\n".join([
        "## Notes",
        "",
        "- This report is evidence-first. It does not infer causes beyond what is recorded.",
        "- If you need stronger auditability: add immutable snapshots + hash-of-snapshot.",
        "",
    ])

# ----------------------------
# Main
# ----------------------------
def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    incidents = collect_incidents()

    out_parts = [
        render_header(),
        render_memory_section(),
        render_logs_section(),
        render_incidents_section(incidents),
        render_footer(),
    ]
    content = "\n".join(out_parts).strip() + "\n"

    OUTPUT_FILE.write_text(content, encoding="utf-8")
    print(f"[OK] wrote {rel(OUTPUT_FILE)} (incidents={len(incidents)})")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

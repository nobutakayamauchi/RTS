#!/usr/bin/env python3
# memory_index.py
# RTS Memory Index (complete): summary + latest + tags + searchable HTML
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Iterable

ROOT = Path(".")
LOGS_DIR = ROOT / "logs"
INCIDENTS_DIR = ROOT / "incidents"
MEMORY_DIR = ROOT / "memory"
INDEX_MD = MEMORY_DIR / "index.md"
INDEX_HTML = MEMORY_DIR / "index.html"

UTC = timezone.utc


def now_utc_iso() -> str:
    return datetime.now(UTC).isoformat()


def safe_read_text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except Exception:
        try:
            return p.read_text()
        except Exception:
            return ""


def first_match(pattern: str, text: str) -> Optional[str]:
    m = re.search(pattern, text, flags=re.MULTILINE)
    return m.group(1).strip() if m else None


def extract_urls(text: str) -> list[str]:
    # keep simple, works for https://... and http://...
    urls = re.findall(r"https?://[^\s)>\"]+", text)
    # unique preserve order
    out: list[str] = []
    seen = set()
    for u in urls:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def guess_event_tag(text: str, fallback: str = "LOG") -> str:
    """
    Try to detect event tag from common patterns in RTS logs.
    """
    candidates = []

    # Explicit "Event:" lines
    ev = first_match(r"^Event:\s*(.+)$", text)
    if ev:
        candidates.append(ev)

    # Headings like "## RTS INCIDENT REPORT"
    if re.search(r"INCIDENT", text, flags=re.IGNORECASE):
        candidates.append("INCIDENT")

    if re.search(r"\bRESET\b", text, flags=re.IGNORECASE):
        candidates.append("RESET")

    if re.search(r"\bGENESIS\b", text, flags=re.IGNORECASE):
        candidates.append("GENESIS")

    if re.search(r"\bAUDIT\b", text, flags=re.IGNORECASE):
        candidates.append("AUDIT")

    if re.search(r"\bKERNEL\b", text, flags=re.IGNORECASE):
        candidates.append("KERNEL")

    if re.search(r"\bRADAR\b", text, flags=re.IGNORECASE):
        candidates.append("RADAR")

    # normalize and pick first meaningful
    for c in candidates:
        c = c.upper()
        # short normalize common "RTS execution cycle..." -> KERNEL
        if "EXECUTION" in c and "CYCLE" in c:
            return "KERNEL"
        if "INCIDENT" in c:
            return "INCIDENT"
        if "RESET" in c:
            return "RESET"
        if "GENESIS" in c:
            return "GENESIS"
        if "AUDIT" in c:
            return "AUDIT"
        if "RADAR" in c:
            return "RADAR"
        if "KERNEL" in c:
            return "KERNEL"

    return fallback


def parse_time_any(text: str) -> Optional[str]:
    """
    Best-effort extraction for display.
    We keep it as a string (JST/UTC mixed) to avoid breaking existing logs.
    """
    t = first_match(r"^Time:\s*(.+)$", text)
    if t:
        return t
    t = first_match(r"^time:\s*(.+)$", text)
    if t:
        return t
    # sometimes "Date:" is used
    d = first_match(r"^Date:\s*(.+)$", text)
    if d:
        return d
    return None


def parse_integrity(text: str) -> str:
    integ = first_match(r"^Integrity:\s*(.+)$", text)
    if integ:
        return integ.upper()
    # fallback guess
    if re.search(r"\bVERIFIED\b", text):
        return "VERIFIED"
    return "UNKNOWN"


def file_mtime_iso(p: Path) -> str:
    try:
        dt = datetime.fromtimestamp(p.stat().st_mtime, tz=UTC)
        return dt.isoformat()
    except Exception:
        return ""


@dataclass
class Doc:
    kind: str  # "log" or "incident"
    path: Path
    title: str
    tag: str
    time_str: Optional[str]
    integrity: str
    snippet: str
    urls: list[str]
    mtime_utc: str


def make_title_from_path(p: Path) -> str:
    name = p.name
    # nicer for markdown
    return name


def make_snippet(text: str, max_len: int = 240) -> str:
    s = re.sub(r"\s+", " ", text).strip()
    if len(s) <= max_len:
        return s
    return s[: max_len - 1] + "…"


def collect_docs(dir_path: Path, kind: str) -> list[Doc]:
    docs: list[Doc] = []
    if not dir_path.exists():
        return docs

    for p in sorted(dir_path.rglob("*.md")):
        text = safe_read_text(p)
        if not text.strip():
            continue

        tag = guess_event_tag(text, fallback=("INCIDENT" if kind == "incident" else "LOG"))
        time_str = parse_time_any(text)
        integrity = parse_integrity(text)
        urls = extract_urls(text)
        title = make_title_from_path(p)
        snippet = make_snippet(text)
        docs.append(
            Doc(
                kind=kind,
                path=p,
                title=title,
                tag=tag,
                time_str=time_str,
                integrity=integrity,
                snippet=snippet,
                urls=urls,
                mtime_utc=file_mtime_iso(p),
            )
        )

    # newest first by mtime
    docs.sort(key=lambda d: d.mtime_utc, reverse=True)
    return docs


def pick_last_execution(logs: list[Doc]) -> Optional[Doc]:
    # Prefer kernel-ish logs if present
    for d in logs:
        if d.tag in ("KERNEL", "AUDIT", "RESET"):
            return d
    return logs[0] if logs else None


def md_link(text: str, rel_path: str) -> str:
    return f"[{text}]({rel_path})"


def rel(p: Path) -> str:
    return p.as_posix()


def render_index_md(
    generated_utc: str,
    logs: list[Doc],
    incidents: list[Doc],
    latest_n: int = 5,
) -> str:
    last_exec = pick_last_execution(logs)
    integrity = "VERIFIED" if (last_exec and last_exec.integrity == "VERIFIED") else (last_exec.integrity if last_exec else "UNKNOWN")

    total_blocks = len(logs)
    total_incidents = len(incidents)

    lines: list[str] = []
    lines.append("# RTS MEMORY INDEX")
    lines.append("")
    lines.append("## STATUS")
    lines.append("")
    lines.append(f"- generated_utc: `{generated_utc}`")
    lines.append(f"- total_blocks: **{total_blocks}**")
    lines.append(f"- total_incidents: **{total_incidents}**")
    if last_exec:
        lines.append(f"- last_execution: {md_link(last_exec.title, rel(last_exec.path))}")
        if last_exec.time_str:
            lines.append(f"- last_execution_time: `{last_exec.time_str}`")
    lines.append(f"- integrity: **{integrity}**")
    lines.append("")

    # Latest Logs
    lines.append("## Latest Logs")
    lines.append("")
    for d in logs[:latest_n]:
        lines.append(f"- {md_link(d.title, rel(d.path))}")
        lines.append(f"  - tag: `{d.tag}`  integrity: `{d.integrity}`")
        if d.time_str:
            lines.append(f"  - time: `{d.time_str}`")
        if d.urls:
            # show only first to keep short
            lines.append(f"  - url: {d.urls[0]}")
        lines.append(f"  - snippet: {d.snippet}")
    if not logs:
        lines.append("- (no logs found)")
    lines.append("")

    # Latest Incidents
    lines.append("## Latest Incidents")
    lines.append("")
    for d in incidents[:latest_n]:
        lines.append(f"- {md_link(d.title, rel(d.path))}")
        lines.append(f"  - tag: `{d.tag}`  integrity: `{d.integrity}`")
        if d.time_str:
            lines.append(f"  - time: `{d.time_str}`")
        if d.urls:
            lines.append(f"  - url: {d.urls[0]}")
        lines.append(f"  - snippet: {d.snippet}")
    if not incidents:
        lines.append("- (no incidents found)")
    lines.append("")

    # Tag index (quick)
    lines.append("## Tags")
    lines.append("")
    tag_counts: dict[str, int] = {}
    for d in logs + incidents:
        tag_counts[d.tag] = tag_counts.get(d.tag, 0) + 1
    for tag, cnt in sorted(tag_counts.items(), key=lambda x: (-x[1], x[0])):
        lines.append(f"- `{tag}`: {cnt}")
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("Generated by `memory_index.py`.")
    lines.append("")
    return "\n".join(lines)


def render_index_html(
    generated_utc: str,
    logs: list[Doc],
    incidents: list[Doc],
    latest_n: int = 5,
) -> str:
    # Minimal standalone HTML with client-side search/filter (no libs).
    # Put all docs as JSON in page.
    docs = []
    for d in (logs + incidents):
        docs.append(
            {
                "kind": d.kind,
                "path": rel(d.path),
                "title": d.title,
                "tag": d.tag,
                "time": d.time_str or "",
                "integrity": d.integrity,
                "snippet": d.snippet,
                "url": d.urls[0] if d.urls else "",
                "mtime_utc": d.mtime_utc,
            }
        )

    last_exec = pick_last_execution(logs)
    integrity = "VERIFIED" if (last_exec and last_exec.integrity == "VERIFIED") else (last_exec.integrity if last_exec else "UNKNOWN")

    payload = json.dumps(docs, ensure_ascii=False)

    def li(d: Doc) -> str:
        url_html = f'<div class="meta"><a href="{d.urls[0]}" target="_blank" rel="noreferrer">{d.urls[0]}</a></div>' if d.urls else ""
        time_html = f'<div class="meta">time: {escape_html(d.time_str)}</div>' if d.time_str else ""
        return f"""
        <li class="card" data-kind="{d.kind}" data-tag="{d.tag}" data-text="{escape_html((d.title + ' ' + d.snippet + ' ' + d.tag).lower())}">
          <div class="title"><a href="../{rel(d.path)}">{escape_html(d.title)}</a></div>
          <div class="meta">tag: <b>{escape_html(d.tag)}</b> · integrity: <b>{escape_html(d.integrity)}</b></div>
          {time_html}
          {url_html}
          <div class="snippet">{escape_html(d.snippet)}</div>
        </li>
        """

    latest_logs_html = "\n".join(li(d) for d in logs[:latest_n]) if logs else "<li class='card'>(no logs)</li>"
    latest_inc_html = "\n".join(li(d) for d in incidents[:latest_n]) if incidents else "<li class='card'>(no incidents)</li>"

    tags = sorted({d.tag for d in (logs + incidents)})
    tag_options = '<option value="">ALL</option>' + "".join(f'<option value="{t}">{t}</option>' for t in tags)

    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>RTS MEMORY INDEX</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; margin: 16px; line-height: 1.35; }}
  h1 {{ margin: 0 0 8px; }}
  .muted {{ color: #666; }}
  .grid {{ display: grid; grid-template-columns: 1fr; gap: 14px; }}
  @media (min-width: 900px) {{ .grid {{ grid-template-columns: 1fr 1fr; }} }}
  .panel {{ border: 1px solid #ddd; border-radius: 10px; padding: 12px; }}
  .controls {{ display:flex; gap: 8px; flex-wrap: wrap; margin: 10px 0 0; }}
  input, select {{ padding: 10px; border: 1px solid #ccc; border-radius: 10px; font-size: 16px; }}
  ul {{ list-style: none; padding: 0; margin: 10px 0 0; }}
  .card {{ border: 1px solid #eee; border-radius: 10px; padding: 10px; margin: 10px 0; }}
  .title a {{ text-decoration: none; }}
  .meta {{ font-size: 13px; color: #444; margin-top: 4px; overflow-wrap:anywhere; }}
  .snippet {{ font-size: 14px; color: #222; margin-top: 6px; }}
  .status {{ display:flex; gap: 14px; flex-wrap: wrap; }}
  .status b {{ font-size: 16px; }}
  .pill {{ border: 1px solid #ddd; border-radius: 999px; padding: 6px 10px; font-size: 14px; }}
</style>
</head>
<body>
<h1>RTS MEMORY INDEX</h1>
<div class="muted">generated_utc: {escape_html(generated_utc)}</div>

<div class="panel" style="margin-top:12px;">
  <h2 style="margin:0 0 8px;">STATUS</h2>
  <div class="status">
    <div class="pill">total_blocks: <b>{len(logs)}</b></div>
    <div class="pill">total_incidents: <b>{len(incidents)}</b></div>
    <div class="pill">integrity: <b>{escape_html(integrity)}</b></div>
    <div class="pill">last_execution: <b>{escape_html(last_exec.title if last_exec else "N/A")}</b></div>
  </div>

  <div class="controls">
    <input id="q" placeholder="Search (title / snippet / tag)" style="flex:1; min-width: 220px;" />
    <select id="kind">
      <option value="">ALL</option>
      <option value="log">log</option>
      <option value="incident">incident</option>
    </select>
    <select id="tag">{tag_options}</select>
  </div>
  <div class="muted" style="margin-top:8px;">Search filters apply to the full dataset below.</div>
</div>

<div class="grid" style="margin-top:14px;">
  <div class="panel">
    <h2 style="margin:0;">Latest Logs</h2>
    <ul id="latest-logs">{latest_logs_html}</ul>
  </div>
  <div class="panel">
    <h2 style="margin:0;">Latest Incidents</h2>
    <ul id="latest-incidents">{latest_inc_html}</ul>
  </div>
</div>

<div class="panel" style="margin-top:14px;">
  <h2 style="margin:0;">All Documents</h2>
  <div class="muted" style="margin-top:6px;">Filtered view</div>
  <ul id="all"></ul>
</div>

<script>
const DATA = {payload};

function el(id) {{ return document.getElementById(id); }}
const q = el("q");
const kind = el("kind");
const tag = el("tag");
const all = el("all");

function escapeHtml(s) {{
  return (s||"").replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;");
}}

function card(d) {{
  const url = d.url ? `<div class="meta"><a href="${{d.url}}" target="_blank" rel="noreferrer">${{escapeHtml(d.url)}}</a></div>` : "";
  const time = d.time ? `<div class="meta">time: ${{escapeHtml(d.time)}}</div>` : "";
  return `
  <li class="card">
    <div class="title"><a href="../${{d.path}}">${{escapeHtml(d.title)}}</a></div>
    <div class="meta">kind: <b>${{escapeHtml(d.kind)}}</b> · tag: <b>${{escapeHtml(d.tag)}}</b> · integrity: <b>${{escapeHtml(d.integrity)}}</b></div>
    ${{time}}
    ${{url}}
    <div class="snippet">${{escapeHtml(d.snippet)}}</div>
  </li>`;
}}

function apply() {{
  const qq = (q.value || "").toLowerCase().trim();
  const kk = kind.value;
  const tt = tag.value;

  const filtered = DATA.filter(d => {{
    if (kk && d.kind !== kk) return false;
    if (tt && d.tag !== tt) return false;
    if (!qq) return true;
    const hay = (d.title + " " + d.snippet + " " + d.tag).toLowerCase();
    return hay.includes(qq);
  }});

  all.innerHTML = filtered.slice(0, 300).map(card).join("");
}}

q.addEventListener("input", apply);
kind.addEventListener("change", apply);
tag.addEventListener("change", apply);
apply();
</script>
</body>
</html>
"""
    return html


def escape_html(s: Optional[str]) -> str:
    if s is None:
        return ""
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def main() -> None:
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)

    generated_utc = now_utc_iso()
    logs = collect_docs(LOGS_DIR, "log")
    incidents = collect_docs(INCIDENTS_DIR, "incident")

    md = render_index_md(generated_utc, logs, incidents, latest_n=5)
    INDEX_MD.write_text(md, encoding="utf-8")

    html = render_index_html(generated_utc, logs, incidents, latest_n=5)
    INDEX_HTML.write_text(html, encoding="utf-8")

    print(f"[OK] wrote: {INDEX_MD}")
    print(f"[OK] wrote: {INDEX_HTML}")
    print(f"[OK] docs: logs={len(logs)} incidents={len(incidents)}")


if __name__ == "__main__":
    main()

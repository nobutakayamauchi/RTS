#!/usr/bin/env python3
# radar_analysis.py
# RTS Radar Analysis Engine (minimal, reliable)
# - incidents/ と logs/ を走査して、要点を radar/analysis.md + radar/analysis.json に出す
# - できるだけ壊れない設計（ファイル欠損・文字化け耐性）

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

JST = timezone(timedelta(hours=9))

INCIDENTS_DIR = Path("incidents")
LOGS_DIR = Path("logs")
RADAR_DIR = Path("radar")
RADAR_DIR.mkdir(parents=True, exist_ok=True)

OUT_MD = RADAR_DIR / "ANALYSIS.md"
OUT_JSON = RADAR_DIR / "analysis.json"

# どれだけ深掘りするか（重くなったら絞る）
MAX_FILES_PER_BUCKET = 60
MAX_SNIPPET_CHARS = 300

SEVERITY_RE = re.compile(r"\b(S[0-3]|critical|high|medium|low)\b", re.IGNORECASE)
ID_RE = re.compile(r"\bINC_\d{8}_\d{4}(?:_[A-Za-z0-9]+)*\b")


@dataclass
class Doc:
    path: str
    kind: str  # "incident" | "log"
    mtime_utc: str
    title: str
    severity: str | None
    incident_id: str | None
    url: str | None
    snippet: str


def _read_text(p: Path) -> str:
    # GitHub Actions / Windows改行 / 文字化けでも落ちないように
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        try:
            return p.read_text(errors="replace")
        except Exception:
            return ""


def _mtime_utc_iso(p: Path) -> str:
    try:
        ts = p.stat().st_mtime
        return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
    except Exception:
        return datetime.now(timezone.utc).isoformat()


def _first_nonempty_line(text: str) -> str:
    for line in text.splitlines():
        s = line.strip()
        if s:
            return s
    return ""


def _extract_title(text: str, fallback: str) -> str:
    # 先頭の Markdown H1 を優先
    for line in text.splitlines()[:30]:
        if line.lstrip().startswith("#"):
            t = line.lstrip("#").strip()
            if t:
                return t
    # 次点：最初の非空行
    line = _first_nonempty_line(text)
    if line:
        return line[:120]
    return fallback[:120]


def _extract_url(text: str) -> str | None:
    # 先頭3000文字からURLっぽいものを拾う（X, GitHub等）
    head = text[:3000]
    m = re.search(r"https?://[^\s)>\]]+", head)
    return m.group(0) if m else None


def _extract_severity(text: str) -> str | None:
    # "Severity: S2" みたいなのを拾う / ざっくりでもOK
    head = text[:4000]
    # よくある形
    m = re.search(r"Severity\s*:\s*(S[0-3]|critical|high|medium|low)", head, re.IGNORECASE)
    if m:
        return m.group(1).upper()
    # ざっくり単語検出
    m2 = SEVERITY_RE.search(head)
    if m2:
        return m2.group(1).upper()
    return None


def _extract_incident_id(text: str) -> str | None:
    head = text[:6000]
    m = ID_RE.search(head)
    return m.group(0) if m else None


def _snippet(text: str) -> str:
    # 改行を潰して短く
    s = " ".join([ln.strip() for ln in text.splitlines() if ln.strip()])
    s = re.sub(r"\s+", " ", s).strip()
    if len(s) > MAX_SNIPPET_CHARS:
        return s[:MAX_SNIPPET_CHARS] + "…"
    return s


def _collect_docs() -> list[Doc]:
    docs: list[Doc] = []

    # incidents
    if INCIDENTS_DIR.exists():
        incident_files = sorted(INCIDENTS_DIR.rglob("*.md"), key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True)
        for p in incident_files[:MAX_FILES_PER_BUCKET]:
            text = _read_text(p)
            docs.append(
                Doc(
                    path=str(p),
                    kind="incident",
                    mtime_utc=_mtime_utc_iso(p),
                    title=_extract_title(text, fallback=p.name),
                    severity=_extract_severity(text),
                    incident_id=_extract_incident_id(text),
                    url=_extract_url(text),
                    snippet=_snippet(text),
                )
            )

    # logs
    if LOGS_DIR.exists():
        log_files = sorted(LOGS_DIR.rglob("*.md"), key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True)
        for p in log_files[:MAX_FILES_PER_BUCKET]:
            text = _read_text(p)
            docs.append(
                Doc(
                    path=str(p),
                    kind="log",
                    mtime_utc=_mtime_utc_iso(p),
                    title=_extract_title(text, fallback=p.name),
                    severity=None,
                    incident_id=_extract_incident_id(text),
                    url=_extract_url(text),
                    snippet=_snippet(text),
                )
            )

    # 新しい順に
    docs.sort(key=lambda d: d.mtime_utc, reverse=True)
    return docs


def _severity_rank(sev: str | None) -> int:
    if not sev:
        return 99
    s = sev.upper()
    if s.startswith("S0"):
        return 0
    if s.startswith("S1") or s == "CRITICAL":
        return 1
    if s.startswith("S2") or s == "HIGH":
        return 2
    if s.startswith("S3") or s == "MEDIUM":
        return 3
    if s == "LOW":
        return 4
    return 98


def _group_incidents(docs: list[Doc]) -> dict[str, Any]:
    incidents = [d for d in docs if d.kind == "incident"]
    # severity優先 + 新しい順
    incidents.sort(key=lambda d: (_severity_rank(d.severity), d.mtime_utc), reverse=False)

    by_sev: dict[str, list[Doc]] = {}
    for d in incidents:
        key = d.severity or "UNSPECIFIED"
        by_sev.setdefault(key, []).append(d)

    # ざっくり統計
    stats = {
        "total": len(incidents),
        "by_severity": {k: len(v) for k, v in by_sev.items()},
    }

    return {"stats": stats, "by_severity": by_sev}


def _to_json_payload(docs: list[Doc]) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    grouped = _group_incidents(docs)

    return {
        "generated_utc": now,
        "counts": {
            "docs": len(docs),
            "incidents": sum(1 for d in docs if d.kind == "incident"),
            "logs": sum(1 for d in docs if d.kind == "log"),
        },
        "incident_stats": grouped["stats"],
        "docs": [
            {
                "path": d.path,
                "kind": d.kind,
                "mtime_utc": d.mtime_utc,
                "title": d.title,
                "severity": d.severity,
                "incident_id": d.incident_id,
                "url": d.url,
                "snippet": d.snippet,
            }
            for d in docs
        ],
    }


def _render_md(payload: dict[str, Any]) -> str:
    gen_utc = payload["generated_utc"]
    counts = payload["counts"]
    incident_stats = payload["incident_stats"]
    docs = payload["docs"]

    # 最近のログ上位
    latest_logs = [d for d in docs if d["kind"] == "log"][:10]
    # 重要インシデント（severity順）
    incidents = [d for d in docs if d["kind"] == "incident"]
    incidents.sort(key=lambda d: (_severity_rank(d.get("severity")), d.get("mtime_utc", "")))
    top_incidents = incidents[:12]

    lines: list[str] = []
    lines.append("# RTS RADAR ANALYSIS\n")
    lines.append(f"- generated_utc: `{gen_utc}`")
    lines.append(f"- docs: **{counts['docs']}** / incidents: **{counts['incidents']}** / logs: **{counts['logs']}**\n")

    lines.append("## Incident Stats\n")
    lines.append(f"- total: **{incident_stats.get('total', 0)}**")
    by_sev = incident_stats.get("by_severity", {})
    if by_sev:
        lines.append("- by_severity:")
        for k, v in sorted(by_sev.items(), key=lambda kv: _severity_rank(kv[0])):
            lines.append(f"  - **{k}**: {v}")
    lines.append("")

    lines.append("## Top Incidents (severity-first)\n")
    if not top_incidents:
        lines.append("- (none)\n")
    else:
        for d in top_incidents:
            sev = d.get("severity") or "UNSPECIFIED"
            title = d.get("title") or "(no title)"
            path = d.get("path")
            url = d.get("url")
            iid = d.get("incident_id")
            meta = []
            meta.append(f"**{sev}**")
            if iid:
                meta.append(iid)
            meta_str = " / ".join(meta)

            lines.append(f"- {meta_str} — **{title}**")
            lines.append(f"  - file: `{path}`")
            if url:
                lines.append(f"  - url: {url}")
            sn = d.get("snippet", "")
            if sn:
                lines.append(f"  - snippet: {sn}")
    lines.append("")

    lines.append("## Latest Logs\n")
    if not latest_logs:
        lines.append("- (none)\n")
    else:
        for d in latest_logs:
            title = d.get("title") or "(no title)"
            path = d.get("path")
            url = d.get("url")
            lines.append(f"- **{title}**")
            lines.append(f"  - file: `{path}`")
            if url:
                lines.append(f"  - url: {url}")
    lines.append("")

    lines.append("## Notes\n")
    lines.append("- This file is generated by `radar_analysis.py`.")
    lines.append("- It summarizes `incidents/` and `logs/` for quick operator review.\n")

    return "\n".join(lines)


def main() -> None:
    docs = _collect_docs()
    payload = _to_json_payload(docs)

    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_MD.write_text(_render_md(payload), encoding="utf-8")

    print(f"[OK] radar analysis written: {OUT_MD} / {OUT_JSON}")


if __name__ == "__main__":
    main()

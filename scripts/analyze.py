from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional


ROOT = Path(__file__).resolve().parents[1]

LOGS_DIR = ROOT / "logs"
INCIDENTS_DIR = ROOT / "incidents"
MEMORY_INDEX = ROOT / "memory" / "index.md"

OUTPUT = ROOT / "analyze" / "index.md"

# Phase-3: operator-defined risk topics (evidence-only scan)
RISK_TOPICS: Dict[str, List[str]] = {
    "context loss": ["context loss", "lost context", "context collapse"],
    "workflow interruption": ["workflow interruption", "workflow broken", "actions failed", "workflow failed"],
    "server error": ["internal server error", "server error", "http 500", "status 500", "500"],
    "session reset": ["session reset", "reset", "conversation reset"],
    "error": ["error", "exception", "traceback"],
    "failure": ["failure", "failed", "collapse"],
    "auth": ["auth", "authentication", "permission denied", "unauthorized"],
    "timeout": ["timeout", "timed out"],
    "token": ["token", "rate limit", "quota"],
    "github mobile": ["github mobile", "iphone", "ios"],
    "deleted workflow": ["deleted workflow", "workflow deletion", "deleted action"],
}


# Phase-3: cascade definition (co-occurrence in same doc; evidence-only)
CASCADE_RULES: List[Tuple[str, List[str]]] = [
    ("cascade: error + workflow interruption", ["error", "workflow interruption"]),
    ("cascade: server error + error", ["server error", "error"]),
    ("cascade: session reset + context loss", ["session reset", "context loss"]),
    ("cascade: error + session reset", ["error", "session reset"]),
    ("cascade: workflow interruption + session reset", ["workflow interruption", "session reset"]),
]


@dataclass
class Doc:
    file_path: Path
    rel_path: str
    content: str
    mtime_utc: datetime

    def sha8(self) -> str:
        h = hashlib.sha256(self.content.encode("utf-8", errors="ignore")).hexdigest()
        return h[:8]


def read_text_safe(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="ignore")


def utc_from_ts(ts: float) -> datetime:
    return datetime.fromtimestamp(ts, tz=timezone.utc)


def load_docs(folder: Path) -> List[Doc]:
    docs: List[Doc] = []
    if not folder.exists():
        return docs

    for f in sorted(folder.glob("*.md")):
        try:
            content = read_text_safe(f)
            rel = str(f.relative_to(ROOT))
            mtime = utc_from_ts(f.stat().st_mtime)
            docs.append(Doc(file_path=f, rel_path=rel, content=content, mtime_utc=mtime))
        except Exception:
            continue
    return docs


def first_h1_or_first_line(content: str, fallback: str) -> str:
    for line in content.splitlines():
        s = line.strip()
        if s.startswith("# "):
            t = s[2:].strip()
            if t:
                return t
    for line in content.splitlines():
        s = line.strip()
        if s:
            return s[:120]
    return fallback


def normalize_title(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s[:160]


def dedup_by_title_fingerprint(docs: List[Doc]) -> Tuple[List[Doc], int]:
    seen: Dict[str, Doc] = {}
    dup = 0

    for d in docs:
        title = first_h1_or_first_line(d.content, "unknown")
        fp = hashlib.sha256(normalize_title(title).encode("utf-8", errors="ignore")).hexdigest()
        if fp in seen:
            dup += 1
            continue
        seen[fp] = d

    return list(seen.values()), dup


def count_topic_hits(docs: List[Doc], topics: Dict[str, List[str]]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for topic, words in topics.items():
        c = 0
        for d in docs:
            lower = d.content.lower()
            for w in words:
                c += lower.count(w.lower())
        counts[topic] = c
    return counts


def evidence_hits_top(docs: List[Doc], topics: Dict[str, List[str]], per_topic: int = 6) -> Dict[str, List[str]]:
    out: Dict[str, List[str]] = {}
    for topic, words in topics.items():
        hits: List[str] = []
        for d in sorted(docs, key=lambda x: x.mtime_utc, reverse=True):
            lower = d.content.lower()
            found = False
            for w in words:
                if w.lower() in lower:
                    found = True
                    break
            if found:
                hits.append(f"{d.rel_path}#sha:{d.sha8()}")
            if len(hits) >= per_topic:
                break
        out[topic] = hits
    return out


def recent_window(docs: List[Doc], days: int) -> List[Doc]:
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=days)
    return [d for d in docs if d.mtime_utc >= cutoff]


def detect_cascades(docs: List[Doc]) -> Dict[str, List[str]]:
    """
    Evidence-only: if a doc contains at least one keyword from each required topic group,
    we list it as a cascade hit (no inference beyond co-occurrence).
    """
    # Build topic -> compiled word list lower
    topic_words_lower: Dict[str, List[str]] = {k: [w.lower() for w in v] for k, v in RISK_TOPICS.items()}

    results: Dict[str, List[str]] = {}
    for rule_name, required_topics in CASCADE_RULES:
        hits: List[str] = []
        for d in sorted(docs, key=lambda x: x.mtime_utc, reverse=True):
            lower = d.content.lower()
            ok = True
            for t in required_topics:
                words = topic_words_lower.get(t, [])
                if not words:
                    ok = False
                    break
                if not any(w in lower for w in words):
                    ok = False
                    break
            if ok:
                hits.append(f"{d.rel_path}#sha:{d.sha8()}")
            if len(hits) >= 8:
                break
        results[rule_name] = hits
    return results


def parse_previous_metrics(prev_text: str) -> Optional[Dict[str, int]]:
    """
    Phase-3 drift detection:
    Parse 'Risk Topic Ranking' section lines like: '- error: 12'
    If not found, return None.
    """
    lines = prev_text.splitlines()
    in_rank = False
    metrics: Dict[str, int] = {}

    for line in lines:
        s = line.strip()
        if s.lower() == "## risk topic ranking":
            in_rank = True
            continue
        if in_rank and s.startswith("## "):
            break
        if in_rank and s.startswith("- "):
            # - topic: 12
            m = re.match(r"^- (.+?):\s*([0-9]+)\s*$", s)
            if m:
                k = m.group(1).strip().lower()
                v = int(m.group(2))
                metrics[k] = v

    if not metrics:
        return None
    return metrics


def drift_compare(current: Dict[str, int], previous: Optional[Dict[str, int]]) -> Dict[str, int]:
    """
    Returns delta = current - previous for keys present in either.
    If previous is None -> empty dict.
    """
    if previous is None:
        return {}

    keys = set(current.keys()) | set(previous.keys())
    delta: Dict[str, int] = {}
    for k in keys:
        delta[k] = int(current.get(k, 0)) - int(previous.get(k, 0))
    return delta


def md_link(rel_path: str) -> str:
    # Repository-relative link for GitHub Pages markdown rendering.
    return f"[{rel_path}]({rel_path})"


def write_report(
    generated_utc: datetime,
    incidents_raw: List[Doc],
    incidents_dedup: List[Doc],
    logs_all: List[Doc],
    dup_count: int,
    topic_counts: Dict[str, int],
    evidence: Dict[str, List[str]],
    cascades_recent: Dict[str, List[str]],
    cascades_all: Dict[str, List[str]],
    drift_delta: Dict[str, int],
    drift_available: bool,
) -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    def fmt_dt(dt: datetime) -> str:
        return dt.strftime("%Y-%m-%d %H:%M UTC")

    report: List[str] = []
    report.append("# RTS Sentinel Analyze")
    report.append("")
    report.append(f"Generated: {fmt_dt(generated_utc)}")
    report.append("")

    # Inputs
    report.append("## Inputs")
    report.append("")
    report.append(f"- memory/index.md (priority): {md_link('memory/index.md') if MEMORY_INDEX.exists() else 'missing'}")
    report.append(f"- incidents/*.md: {md_link('incidents')}")
    report.append(f"- logs/*.md: {md_link('logs')}")
    report.append("")

    # Incident trend
    report.append("## Incident Trend")
    report.append("")
    report.append(f"- Incidents observed (raw): {len(incidents_raw)}")
    report.append(f"- Incidents observed (deduplicated): {len(incidents_dedup)}")
    report.append(f"- Duplicate pairs detected: {dup_count}")
    if incidents_dedup:
        latest_inc = max(d.mtime_utc for d in incidents_dedup)
        report.append(f"- Latest incident mtime: {fmt_dt(latest_inc)}")
    report.append("")

    # Latest incidents
    report.append("## Latest Incidents (deduplicated)")
    report.append("")
    for d in sorted(incidents_dedup, key=lambda x: x.mtime_utc, reverse=True)[:12]:
        title = first_h1_or_first_line(d.content, d.rel_path)
        report.append(f"- {title} ({md_link(d.rel_path)}) (mtime: {fmt_dt(d.mtime_utc)}, sha:{d.sha8()})")
    report.append("")

    # Execution stability (logs)
    report.append("## Execution Stability")
    report.append("")
    report.append(f"- Logs observed: {len(logs_all)}")
    if logs_all:
        latest_log = max(d.mtime_utc for d in logs_all)
        report.append(f"- Latest log mtime: {fmt_dt(latest_log)}")
    report.append("")

    report.append("## Latest Logs")
    report.append("")
    for d in sorted(logs_all, key=lambda x: x.mtime_utc, reverse=True)[:10]:
        title = first_h1_or_first_line(d.content, d.rel_path)
        report.append(f"- {title} ({md_link(d.rel_path)}) (mtime: {fmt_dt(d.mtime_utc)}, sha:{d.sha8()})")
    report.append("")

    # Risk patterns
    report.append("## Observed Risk Patterns")
    report.append("")
    report.append("Evidence-first keyword scan across incidents + logs. No inference beyond evidence hits.")
    report.append("")
    report.append("### Risk Topic Ranking")
    report.append("")
    for k, v in sorted(topic_counts.items(), key=lambda x: (-x[1], x[0])):
        report.append(f"- {k}: {v}")
    report.append("")

    report.append("### Evidence Hits (top per topic)")
    report.append("")
    for k, links in sorted(evidence.items(), key=lambda x: x[0]):
        report.append(f"#### {k}")
        if not links:
            report.append("- none")
            report.append("")
            continue
        for link in links:
            # link is "path#sha:xxxx"
            path = link.split("#", 1)[0]
            report.append(f"- {md_link(path)} ({link})")
        report.append("")

    # Phase-3: Cascade detection
    report.append("---")
    report.append("")
    report.append("## Sentinel Phase-3")
    report.append("")
    report.append("### Failure Cascade Detection")
    report.append("")
    report.append("Co-occurrence-based detection (same doc contains multiple risk topics). Evidence-only.")
    report.append("")
    report.append("#### Recent Cascade Hits (last 7 days)")
    report.append("")
    any_recent = False
    for rule_name, hits in cascades_recent.items():
        report.append(f"##### {rule_name}")
        if not hits:
            report.append("- none")
        else:
            any_recent = True
            for h in hits:
                p = h.split("#", 1)[0]
                report.append(f"- {md_link(p)} ({h})")
        report.append("")
    if not any_recent:
        report.append("_No recent cascade evidence detected._")
        report.append("")

    report.append("#### Cascade Hits (all time, top)")
    report.append("")
    for rule_name, hits in cascades_all.items():
        report.append(f"##### {rule_name}")
        if not hits:
            report.append("- none")
        else:
            for h in hits[:8]:
                p = h.split("#", 1)[0]
                report.append(f"- {md_link(p)} ({h})")
        report.append("")

    # Phase-3: Drift detection
    report.append("### Drift Detection")
    report.append("")
    if not drift_available:
        report.append("- baseline: not found (previous analyze/index.md missing or unparsable)")
    else:
        report.append("- baseline: previous analyze/index.md parsed")
    report.append("")
    if drift_delta:
        report.append("#### Topic Delta (current - previous)")
        report.append("")
        # show only non-zero deltas, sorted by magnitude desc
        nonzero = [(k, v) for k, v in drift_delta.items() if v != 0]
        if not nonzero:
            report.append("- no changes detected")
        else:
            for k, v in sorted(nonzero, key=lambda x: (-abs(x[1]), x[0])):
                sign = "+" if v > 0 else ""
                report.append(f"- {k}: {sign}{v}")
        report.append("")
    else:
        report.append("- delta: unavailable")
        report.append("")

    # Phase-3: Self-awareness ledger
    report.append("### Self Awareness Ledger")
    report.append("")
    report.append("- This section records measurable generation conditions (no inference).")
    report.append("")
    report.append(f"- generated_utc: {generated_utc.isoformat()}")
    report.append(f"- inputs: incidents_raw={len(incidents_raw)}, incidents_dedup={len(incidents_dedup)}, logs={len(logs_all)}")
    report.append(f"- dedup: duplicate_pairs={dup_count}")
    report.append(f"- drift_baseline_available: {str(drift_available).lower()}")
    report.append("")

    # Provenance
    report.append("---")
    report.append("")
    report.append("## Provenance")
    report.append("")
    report.append("- This report is generated by `scripts/analyze.py`.")
    report.append("- Sources are not modified. Only parsed.")
    report.append("- Evidence links point to repository paths.")
    report.append("")

    OUTPUT.write_text("\n".join(report), encoding="utf-8")


def main() -> None:
    generated_utc = datetime.now(timezone.utc)

    incidents_raw = load_docs(INCIDENTS_DIR)
    logs_all = load_docs(LOGS_DIR)

    incidents_dedup, dup_count = dedup_by_title_fingerprint(incidents_raw)

    combined = incidents_dedup + logs_all

    # Phase-3: risk scan
    topic_counts = count_topic_hits(combined, RISK_TOPICS)
    evidence = evidence_hits_top(combined, RISK_TOPICS, per_topic=6)

    # Phase-3: cascade scan (recent + all)
    combined_recent = recent_window(combined, days=7)
    cascades_recent = detect_cascades(combined_recent)
    cascades_all = detect_cascades(combined)

    # Phase-3: drift detection vs previous analyze/index.md
    prev_metrics: Optional[Dict[str, int]] = None
    drift_available = False
    if OUTPUT.exists():
        try:
            prev_text = read_text_safe(OUTPUT)
            prev_metrics = parse_previous_metrics(prev_text)
            drift_available = prev_metrics is not None
        except Exception:
            prev_metrics = None
            drift_available = False

    # Current metrics must match the markdown "Risk Topic Ranking" keys.
    current_metrics = {k.lower(): int(v) for k, v in topic_counts.items()}
    drift_delta = drift_compare(current_metrics, prev_metrics)

    write_report(
        generated_utc=generated_utc,
        incidents_raw=incidents_raw,
        incidents_dedup=incidents_dedup,
        logs_all=logs_all,
        dup_count=dup_count,
        topic_counts=topic_counts,
        evidence=evidence,
        cascades_recent=cascades_recent,
        cascades_all=cascades_all,
        drift_delta=drift_delta,
        drift_available=drift_available,
    )


if __name__ == "__main__":
    main()

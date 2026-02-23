from __future__ import annotations

import re
import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Iterable, List, Dict, Tuple


ROOT = Path(__file__).resolve().parents[1]

LOGS_DIR = ROOT / "logs"
INCIDENTS_DIR = ROOT / "incidents"
MEMORY_INDEX = ROOT / "memory" / "index.md"

OUTPUT = ROOT / "analyze" / "index.md"

# Operator-defined priority topics (from handover)
RISK_TOPICS = [
    "context loss",
    "workflow interruption",
    "server error",
    "session reset",
]

# Deterministic expansions (still evidence-based: keyword scans only)
EXTRA_RISK_TOPICS = [
    "rate limit",
    "timeout",
    "permission",
    "auth",
    "token",
    "merge conflict",
    "rebase",
    "force push",
    "deleted workflow",
    "github mobile",
    "ios",
    "shortcut",
    "automation",
    "downtime",
    "failure",
    "error",
    "exception",
    "traceback",
]

GOVERNANCE_KEYWORDS = [
    "verification",
    "verify",
    "operator",
    "human",
    "backup",
    "last resort",
    "deletion",
    "authority",
    "governance",
    "policy",
    "provenance",
    "evidence",
]


@dataclass(frozen=True)
class EvidenceHit:
    topic: str
    file_rel: str
    line_no: int
    line: str


@dataclass(frozen=True)
class Doc:
    file_path: Path
    rel_path: str
    content: str
    mtime_utc: datetime

    @property
    def sha8(self) -> str:
        h = hashlib.sha256(self.content.encode("utf-8", errors="ignore")).hexdigest()
        return h[:8]


def utc_dt_from_ts(ts: float) -> datetime:
    return datetime.fromtimestamp(ts, tz=timezone.utc)


def read_text_safe(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="ignore")


def load_docs(folder: Path) -> List[Doc]:
    docs: List[Doc] = []
    if not folder.exists():
        return docs

    for f in sorted(folder.glob("*.md")):
        try:
            content = read_text_safe(f)
            rel = f.relative_to(ROOT).as_posix()
            mtime = utc_dt_from_ts(f.stat().st_mtime)
            docs.append(Doc(file_path=f, rel_path=rel, content=content, mtime_utc=mtime))
        except Exception:
            continue
    return docs


def normalize_title(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"[`*_>#$begin:math:display$$end:math:display$$begin:math:text$$end:math:text$]", "", s)
    return s[:120]


def extract_doc_title(content: str, fallback: str) -> str:
    # Prefer first markdown H1
    for line in content.splitlines():
        if line.strip().startswith("# "):
            t = line.strip()[2:].strip()
            if t:
                return t
    # Else first non-empty line
    for line in content.splitlines():
        if line.strip():
            return line.strip()[:120]
    return fallback


def dedup_docs_by_fingerprint(docs: List[Doc]) -> Tuple[List[Doc], List[Tuple[Doc, Doc]]]:
    """
    Deterministic dedup:
    - fingerprint = hash(normalized title + normalized head(<=400 chars))
    Returns:
      - unique docs (sorted by mtime desc)
      - duplicate pairs (kept, dup)
    """
    seen: Dict[str, Doc] = {}
    dups: List[Tuple[Doc, Doc]] = []

    for d in docs:
        title = extract_doc_title(d.content, d.file_path.name)
        head = normalize_title(d.content[:400])
        fp = hashlib.sha256((normalize_title(title) + "|" + head).encode("utf-8")).hexdigest()

        if fp in seen:
            dups.append((seen[fp], d))
        else:
            seen[fp] = d

    unique = list(seen.values())
    unique.sort(key=lambda x: x.mtime_utc, reverse=True)
    return unique, dups


def find_hits(docs: Iterable[Doc], topics: List[str]) -> Tuple[Dict[str, int], List[EvidenceHit]]:
    counts = {t: 0 for t in topics}
    hits: List[EvidenceHit] = []

    for d in docs:
        for i, raw in enumerate(d.content.splitlines(), start=1):
            line = raw.strip()
            if not line:
                continue
            lower = line.lower()
            for t in topics:
                if t in lower:
                    counts[t] += 1
                    clipped = (line[:240] + "…") if len(line) > 240 else line
                    hits.append(EvidenceHit(topic=t, file_rel=d.rel_path, line_no=i, line=clipped))

    return counts, hits


def top_hits_by_topic(hits: List[EvidenceHit], topic: str, limit: int = 5) -> List[EvidenceHit]:
    out = [h for h in hits if h.topic == topic]
    out.sort(key=lambda h: (h.file_rel, h.line_no))
    return out[:limit]


def md_link_to_repo(rel_path: str) -> str:
    # Works in GitHub and GitHub Pages Markdown render.
    return f"[{rel_path}]({rel_path})"


def fmt_dt(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def main() -> None:
    incidents_all = load_docs(INCIDENTS_DIR)
    logs_all = load_docs(LOGS_DIR)

    incidents, incident_dups = dedup_docs_by_fingerprint(incidents_all)

    topics = RISK_TOPICS + [t for t in EXTRA_RISK_TOPICS if t not in RISK_TOPICS]

    risk_counts_inc, risk_hits_inc = find_hits(incidents, topics)
    risk_counts_log, risk_hits_log = find_hits(logs_all, topics)

    risk_counts = {t: risk_counts_inc.get(t, 0) + risk_counts_log.get(t, 0) for t in topics}
    all_hits = risk_hits_inc + risk_hits_log

    gov_counts, gov_hits = find_hits(list(incidents) + list(logs_all), GOVERNANCE_KEYWORDS)

    memory_exists = MEMORY_INDEX.exists()
    memory_rel = MEMORY_INDEX.relative_to(ROOT).as_posix() if memory_exists else None

    now = datetime.now(timezone.utc)

    ranked_topics = sorted(topics, key=lambda t: (-risk_counts[t], t))
    ranked_gov = sorted(GOVERNANCE_KEYWORDS, key=lambda k: (-gov_counts[k], k))

    latest_inc = incidents[0].mtime_utc if incidents else None
    latest_log = max((d.mtime_utc for d in logs_all), default=None)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    report: List[str] = []
    report.append("# RTS Analyze")
    report.append("")
    report.append(f"Generated: {fmt_dt(now)}")
    report.append("")
    report.append("---")
    report.append("")
    report.append("## Inputs")
    report.append("")
    if memory_exists and memory_rel:
        report.append(f"- memory/index.md (priority): {md_link_to_repo(memory_rel)}")
    else:
        report.append("- memory/index.md (priority): **MISSING**")
    report.append(f"- incidents/*.md: {INCIDENTS_DIR.relative_to(ROOT).as_posix()}/")
    report.append(f"- logs/*.md: {LOGS_DIR.relative_to(ROOT).as_posix()}/")
    report.append("")
    report.append("---")
    report.append("")
    report.append("## Incident Trend")
    report.append("")
    report.append(f"- Incidents observed (raw): {len(incidents_all)}")
    report.append(f"- Incidents observed (deduplicated): {len(incidents)}")
    report.append(f"- Duplicate pairs detected: {len(incident_dups)}")
    if latest_inc:
        report.append(f"- Latest incident mtime: {fmt_dt(latest_inc)}")
    report.append("")
    report.append("### Latest Incidents (deduplicated)")
    report.append("")
    if incidents:
        for d in incidents[:10]:
            title = extract_doc_title(d.content, d.file_path.name)
            report.append(
                f"- **{title}** — {md_link_to_repo(d.rel_path)} (mtime: {fmt_dt(d.mtime_utc)}, sha:{d.sha8})"
            )
    else:
        report.append("- (none)")
    report.append("")
    if incident_dups:
        report.append("### Duplicate Evidence (dedup provenance)")
        report.append("")
        for kept, dup in incident_dups[:10]:
            report.append(f"- kept: {md_link_to_repo(kept.rel_path)} ← dup: {md_link_to_repo(dup.rel_path)}")
        if len(incident_dups) > 10:
            report.append(f"- … and {len(incident_dups) - 10} more")
        report.append("")

    report.append("---")
    report.append("")
    report.append("## Execution Stability")
    report.append("")
    report.append(f"- Logs observed: {len(logs_all)}")
    if latest_log:
        report.append(f"- Latest log mtime: {fmt_dt(latest_log)}")
    report.append("")
    report.append("### Latest Logs")
    report.append("")
    if logs_all:
        logs_sorted = sorted(logs_all, key=lambda x: x.mtime_utc, reverse=True)
        for d in logs_sorted[:10]:
            title = extract_doc_title(d.content, d.file_path.name)
            report.append(
                f"- **{title}** — {md_link_to_repo(d.rel_path)} (mtime: {fmt_dt(d.mtime_utc)}, sha:{d.sha8})"
            )
    else:
        report.append("- (none)")
    report.append("")

    report.append("---")
    report.append("")
    report.append("## Observed Risk Patterns")
    report.append("")
    report.append("Evidence-first keyword signals across incidents + logs. No inference beyond evidence hits.")
    report.append("")
    report.append("### Risk Topic Ranking")
    report.append("")
    for t in ranked_topics[:20]:
        report.append(f"- **{t}**: {risk_counts[t]}")
    report.append("")
    report.append("### Evidence Hits (top per topic)")
    report.append("")
    for t in ranked_topics[:12]:
        if risk_counts[t] == 0:
            continue
        report.append(f"#### {t}")
        report.append("")
        for h in top_hits_by_topic(all_hits, t, limit=5):
            report.append(f"- {md_link_to_repo(h.file_rel)}#L{h.line_no} — `{h.line}`")
        report.append("")

    report.append("---")
    report.append("")
    report.append("## Governance Signals")
    report.append("")
    report.append("Deterministic governance keyword scan (evidence-only).")
    report.append("")
    for k in ranked_gov:
        report.append(f"- **{k}**: {gov_counts[k]}")
    report.append("")
    report.append("### Governance Evidence")
    report.append("")
    any_g = False
    for k in ranked_gov[:10]:
        if gov_counts[k] == 0:
            continue
        any_g = True
        report.append(f"#### {k}")
        report.append("")
        for h in top_hits_by_topic(gov_hits, k, limit=5):
            report.append(f"- {md_link_to_repo(h.file_rel)}#L{h.line_no} — `{h.line}`")
        report.append("")
    if not any_g:
        report.append("- (no governance keywords detected)")
        report.append("")

    # ----------------------------
    # SECOND FORM
    # High Risk Incident Ranking
    # ----------------------------
    report.append("---")
    report.append("")
    report.append("## High Risk Incidents")
    report.append("")
    report.append("Deterministic keyword risk scoring (evidence-only).")
    report.append("")

    risk_score_words = [
        "context loss",
        "workflow interruption",
        "server error",
        "session reset",
        "deleted workflow",
        "downtime",
        "failure",
        "reset",
        "error",
        "exception",
        "traceback",
        "permission",
        "auth",
        "token",
        "rate limit",
        "timeout",
        "github mobile",
        "ios",
        "shortcut",
        "automation",
    ]

    scored: List[Tuple[int, Doc]] = []
    for d in incidents:
        lower = d.content.lower()
        score = 0
        for w in risk_score_words:
            score += lower.count(w)
        if score > 0:
            scored.append((score, d))

    scored.sort(key=lambda x: (-x[0], x[1].rel_path))

    if scored:
        for score, d in scored[:10]:
            title = extract_doc_title(d.content, d.file_path.name)
            report.append(
                f"- Risk Score **{score}** — **{title}** — {md_link_to_repo(d.rel_path)} (mtime: {fmt_dt(d.mtime_utc)}, sha:{d.sha8})"
            )
    else:
        report.append("- No high risk incidents detected.")
    report.append("")
    # ----------------------------
    # THIRD FORM
    # Governance Score
    # ----------------------------

    report.append("---")
    report.append("")
    report.append("## Governance Score")
    report.append("")

    gov_words = {
        "backup": ["backup"],
        "provenance": ["provenance", "evidence"],
        "deletion": ["deletion", "deleted workflow"],
        "human": ["operator", "verify", "authority"],
        "automation": ["automation", "workflow"],
    }

    gov_score = {}

    combined_docs = incidents + logs_all

    for key, words in gov_words.items():

        count = 0

        for d in combined_docs:

            lower = d.content.lower()

            for w in words:

                count += lower.count(w)

        gov_score[key] = count

    total_score = sum(gov_score.values())

    report.append(f"Governance Score: **{total_score}**")
    report.append("")

    for k, v in gov_score.items():

        report.append(f"- {k}: {v}")
    # ----------------------------
    # FOURTH FORM
    # Future Risk Radar (deterministic)
    # ----------------------------

    report.append("---")
    report.append("")
    report.append("## Future Risk Radar")
    report.append("")
    report.append("Deterministic forecast based on recent evidence frequency (no ML, no inference beyond counts).")
    report.append("")

    # Window settings
    recent_days = 7
    recent_cutoff = now - timedelta(days=recent_days)

    # Use the same topic list already used in Observed Risk Patterns
    radar_topics = topics

    # Recent-only docs
    recent_incidents = [d for d in incidents if d.mtime_utc >= recent_cutoff]
    recent_logs = [d for d in logs_all if d.mtime_utc >= recent_cutoff]

    def count_topic_in_docs(t: str, docs_list: List[Doc]) -> int:
        c = 0
        for dd in docs_list:
            c += dd.content.lower().count(t)
        return c

    radar_rows = []
    for t in radar_topics:
        recent_i = count_topic_in_docs(t, recent_incidents)
        recent_l = count_topic_in_docs(t, recent_logs)
        total_i = count_topic_in_docs(t, incidents)
        total_l = count_topic_in_docs(t, logs_all)

        recent_total = recent_i + recent_l
        overall_total = total_i + total_l

        # Trend score: recent is weighted higher than historical (deterministic)
        # + incidents weight 2, logs weight 1
        trend_score = (recent_i * 2 + recent_l * 1)

        # Simple classification
        if recent_total >= 4:
            level = "RISING"
        elif recent_total >= 1:
            level = "STABLE"
        else:
            level = "QUIET"

        radar_rows.append((level, -trend_score, -recent_total, t, recent_i, recent_l, overall_total))

    # Sort: RISING first, then by trend_score, then recent_total
    level_order = {"RISING": 0, "STABLE": 1, "QUIET": 2}
    radar_rows.sort(key=lambda x: (level_order[x[0]], x[1], x[2], x[3]))

    report.append(f"### Window")
    report.append("")
    report.append(f"- Recent window: last **{recent_days} days** (cutoff: {fmt_dt(recent_cutoff)})")
    report.append(f"- Recent incidents: {len(recent_incidents)} / Recent logs: {len(recent_logs)}")
    report.append("")

    report.append("### Predicted Next Risk Areas (top 10)")
    report.append("")
    report.append("| Level | Topic | Recent Incidents | Recent Logs | Recent Total | Overall Total |")
    report.append("|---|---:|---:|---:|---:|---:|")
    for lvl, _ts, _rt, t, ri, rl, overall in radar_rows[:10]:
        report.append(f"| {lvl} | **{t}** | {ri} | {rl} | {ri+rl} | {overall} |")
    report.append("")

    # Hotspot rules based on Governance Score components (evidence-only)
    # If governance signals are weak, elevate related operational risk.
    report.append("### Operational Hotspots (rule-based)")
    report.append("")
    hotspots = []

    # gov_score exists in THIRD FORM; if not, fallback safely.
    try:
        b = gov_score.get("backup", 0)
        dlt = gov_score.get("deletion", 0)
        aut = gov_score.get("automation", 0)
        prv = gov_score.get("provenance", 0)
        hum = gov_score.get("human", 0)
    except Exception:
        b = dlt = aut = prv = hum = 0

    if b == 0:
        hotspots.append("- **Backup Culture is weak (backup=0)** → elevated recovery risk if workflow/session breaks.")
    if dlt > 0:
        hotspots.append("- **Deletion signals detected** → elevated risk of accidental removal / workflow interruption.")
    if aut > 0 and (count_topic_in_docs("workflow interruption", recent_incidents) + count_topic_in_docs("workflow interruption", recent_logs)) > 0:
        hotspots.append("- **Automation + workflow interruption evidence** → prioritize workflow hardening.")
    if prv == 0:
        hotspots.append("- **Provenance signals weak** → elevated auditability risk (harder to trace regressions).")
    if hum == 0:
        hotspots.append("- **Human governance signals weak** → elevated risk of unsafe automated change.")

    if hotspots:
        report.extend(hotspots)
    else:
        report.append("- No governance-derived hotspots detected in current evidence window.")
    report.append("")

    # Deterministic "Failure Pressure" number (not probability; just an index)
    # Uses only recent evidence counts.
    recent_failure = count_topic_in_docs("failure", recent_incidents) + count_topic_in_docs("failure", recent_logs)
    recent_error = count_topic_in_docs("error", recent_incidents) + count_topic_in_docs("error", recent_logs)
    recent_server = count_topic_in_docs("server error", recent_incidents) + count_topic_in_docs("server error", recent_logs)
    recent_reset = count_topic_in_docs("session reset", recent_incidents) + count_topic_in_docs("session reset", recent_logs)
    recent_wf = count_topic_in_docs("workflow interruption", recent_incidents) + count_topic_in_docs("workflow interruption", recent_logs)

    failure_pressure = (
        recent_failure * 5
        + recent_error * 2
        + recent_server * 4
        + recent_reset * 3
        + recent_wf * 4
        + len(recent_incidents) * 2
        + len(recent_logs) * 1
    )

    report.append("### Failure Pressure Index (deterministic)")
    report.append("")
    report.append(f"- Failure Pressure Index: **{failure_pressure}**")
    report.append("- Definition: weighted sum of recent evidence hits (failure/error/server/session/workflow) + recent volume.")
    report.append("")
    report.append("")
    report.append("---")
    report.append("")
    report.append("## Provenance")
    report.append("")
    report.append("- This report is generated by `scripts/analyze.py`.")
    report.append("- Sources are not modified. Only parsed.")
    report.append("- Evidence links point to repository paths.")
    report.append("")

    OUTPUT.write_text("\n".join(report), encoding="utf-8")


if __name__ == "__main__":
    main()

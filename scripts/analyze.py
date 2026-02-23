from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Dict, Tuple


# ============================================================
# RTS Sentinel Final Form
# Deterministic / evidence-based repository monitoring report
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

LOGS_DIR = ROOT / "logs"
INCIDENTS_DIR = ROOT / "incidents"
MEMORY_INDEX = ROOT / "memory" / "index.md"

OUTPUT = ROOT / "analyze" / "index.md"
OUTPUT.parent.mkdir(exist_ok=True)


# -----------------------------
# Operator-defined keywords
# -----------------------------

RISK_TOPICS: Dict[str, List[str]] = {
    # core risks
    "failure": ["failure", "failed"],
    "error": ["error", "exception", "traceback"],
    "server error": ["internal server error", "server error"],
    "workflow interruption": ["workflow interruption", "workflow", "actions", "github actions"],
    "session reset": ["session reset", "reset"],

    # environment / ops
    "github mobile": ["github mobile", "iphone"],
    "timeout": ["timeout", "timed out"],
    "token": ["token"],
    "auth": ["author", "auth"],
    "context loss": ["context loss", "lost context", "context"],

    # governance / safety signals
    "deletion": ["deletion", "deleted"],
    "verify": ["verify", "verification", "verified"],
    "backup": ["backup"],
    "policy": ["policy"],
    "provenance": ["provenance"],
    "human": ["human", "operator"],
}

GOV_KEYWORDS: Dict[str, List[str]] = {
    "operator": ["operator"],
    "evidence": ["evidence"],
    "verification": ["verification", "verified", "verify"],
    "deletion": ["deletion", "deleted"],
    "governance": ["governance"],
    "human": ["human"],
    "policy": ["policy"],
    "provenance": ["provenance"],
    "authority": ["authority"],
    "backup": ["backup"],
    "last resort": ["last resort"],
}


# -----------------------------
# Data Model
# -----------------------------

@dataclass
class Doc:
    file_path: Path
    rel: str
    content: str
    mtime: datetime

    def sha8(self) -> str:
        return hashlib.sha256(self.content.encode("utf-8", errors="ignore")).hexdigest()[:8]


# -----------------------------
# Utilities
# -----------------------------

def read_text_safe(p: Path) -> str:
    # UTF-8 only, ignore invalid bytes, deterministic behavior.
    try:
        return p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def utc_dt_from_ts(ts: float) -> datetime:
    return datetime.fromtimestamp(ts, tz=timezone.utc)


def load_docs(folder: Path) -> List[Doc]:
    docs: List[Doc] = []
    if not folder.exists():
        return docs

    for f in sorted(folder.glob("*.md")):
        content = read_text_safe(f)
        mtime = utc_dt_from_ts(f.stat().st_mtime)
        docs.append(
            Doc(
                file_path=f,
                rel=str(f.relative_to(ROOT)),
                content=content,
                mtime=mtime,
            )
        )
    return docs


def count_hits(text: str, needles: List[str]) -> int:
    t = text.lower()
    c = 0
    for n in needles:
        c += t.count(n.lower())
    return c


def count_hits_docs(docs: List[Doc], needles: List[str]) -> int:
    total = 0
    for d in docs:
        total += count_hits(d.content, needles)
    return total


def md_link(rel_path: str) -> str:
    # Keep evidence links as repository paths (works in GitHub + Pages rendering)
    return f"[{rel_path}]({rel_path})"


# -----------------------------
# Sentinel Report Sections
# -----------------------------

def build_inputs_section(report: List[str]) -> None:
    report.append("## Inputs")
    report.append("")
    report.append(f"- memory/index.md (priority): {md_link('memory/index.md')}")
    report.append(f"- incidents/*.md: {md_link('incidents/')}")
    report.append(f"- logs/*.md: {md_link('logs/')}")
    report.append("")
    report.append("---")
    report.append("")


def build_incident_trend(report: List[str], incidents: List[Doc]) -> None:
    report.append("## Incident Trend")
    report.append("")
    report.append(f"- incidents observed: {len(incidents)}")

    if incidents:
        latest = max(d.mtime for d in incidents)
        report.append(f"- latest incident: {latest.strftime('%Y-%m-%d %H:%M UTC')}")
    report.append("")
    report.append("---")
    report.append("")


def build_risk_topic_ranking(report: List[str], combined: List[Doc]) -> List[Tuple[str, int]]:
    report.append("## Risk Topic Ranking")
    report.append("")

    ranking: List[Tuple[str, int]] = []
    for topic, needles in RISK_TOPICS.items():
        ranking.append((topic, count_hits_docs(combined, needles)))

    ranking.sort(key=lambda x: x[1], reverse=True)

    for topic, score in ranking:
        report.append(f"- {topic}: {score}")

    report.append("")
    report.append("---")
    report.append("")
    return ranking


def build_governance_score(report: List[str], combined: List[Doc]) -> Dict[str, int]:
    report.append("## Governance Score")
    report.append("")
    scores: Dict[str, int] = {}
    for k, needles in GOV_KEYWORDS.items():
        scores[k] = count_hits_docs(combined, needles)

    total = sum(scores.values())
    report.append(f"- Governance Score: {total}")
    report.append("")

    for k, v in sorted(scores.items(), key=lambda x: x[1], reverse=True):
        report.append(f"- {k}: {v}")

    report.append("")
    report.append("---")
    report.append("")
    return scores


# -------------------------------------------------
# SENTINEL FORM (Forecast + Pressure + Recovery)
# Deterministic evidence-based monitoring only.
# -------------------------------------------------

def build_future_risk_radar(
    report: List[str],
    recent_incidents: List[Doc],
) -> Dict[str, int]:
    report.append("## Future Risk Radar")
    report.append("")

    recent_fail = count_hits_docs(recent_incidents, ["failure", "failed"])
    recent_err = count_hits_docs(recent_incidents, ["error", "exception", "traceback"])
    recent_wf = count_hits_docs(recent_incidents, ["workflow interruption", "workflow", "actions", "github actions"])

    metrics = {
        "recent failures": recent_fail,
        "recent errors": recent_err,
        "workflow interruptions": recent_wf,
    }

    for k, v in metrics.items():
        report.append(f"- {k}: {v}")

    report.append("")
    return metrics


def build_failure_pressure_index(
    report: List[str],
    radar: Dict[str, int],
    recent_incidents: List[Doc],
    recent_logs: List[Doc],
) -> int:
    # Weighted deterministic index (no ML inference).
    pressure = (
        radar["recent failures"] * 4
        + radar["recent errors"] * 3
        + radar["workflow interruptions"] * 2
        + len(recent_incidents) * 2
        + len(recent_logs) * 1
    )

    report.append("## Failure Pressure Index")
    report.append("")
    report.append(f"- Failure Pressure Index: {pressure}")
    report.append("")
    report.append("---")
    report.append("")
    return pressure


def build_recovery_health(report: List[str], logs_all: List[Doc]) -> Tuple[int, str]:
    report.append("## Recovery Health")
    report.append("")

    recoveries = 0
    for d in logs_all:
        t = d.content.lower()
        if ("recovery" in t) or ("reconstruct" in t) or ("rebuild" in t) or ("restore" in t):
            recoveries += 1

    capability = "HIGH" if recoveries >= 3 else "LOW"
    report.append(f"- recovery evidence: {recoveries}")
    report.append(f"- recovery capability: {capability}")
    report.append("")
    report.append("---")
    report.append("")
    return recoveries, capability


def build_provenance(report: List[str]) -> None:
    report.append("## Provenance")
    report.append("")
    report.append("- This report is generated by `scripts/analyze.py`.")
    report.append("- Sources are not modified. Only parsed.")
    report.append("- Evidence links point to repository paths.")
    report.append("")


# -----------------------------
# Main
# -----------------------------

def main() -> None:
    now = datetime.now(timezone.utc)

    incidents = load_docs(INCIDENTS_DIR)
    logs_all = load_docs(LOGS_DIR)

    combined = incidents + logs_all

    # Recent window (Sentinel horizon)
    recent_days = 7
    recent_cutoff = now - timedelta(days=recent_days)

    recent_incidents = [d for d in incidents if d.mtime >= recent_cutoff]
    recent_logs = [d for d in logs_all if d.mtime >= recent_cutoff]

    report: List[str] = []

    # Title (Sentinel naming unified)
    report.append("# RTS Sentinel Analysis")
    report.append("")
    report.append(f"Generated: {now.strftime('%Y-%m-%d %H:%M UTC')}")
    report.append("")
    report.append("---")
    report.append("")

    build_inputs_section(report)
    build_incident_trend(report, incidents)
    build_risk_topic_ranking(report, combined)
    build_governance_score(report, combined)

    # Sentinel Form block
    radar = build_future_risk_radar(report, recent_incidents)
    build_failure_pressure_index(report, radar, recent_incidents, recent_logs)
    build_recovery_health(report, logs_all)

    build_provenance(report)

    OUTPUT.write_text("\n".join(report), encoding="utf-8")


if __name__ == "__main__":
    main()

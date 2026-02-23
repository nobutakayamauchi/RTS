from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List

# -----------------------------
# PATHS
# -----------------------------

ROOT = Path(__file__).resolve().parents[1]

LOGS_DIR = ROOT / "logs"
INCIDENTS_DIR = ROOT / "incidents"

OUTPUT = ROOT / "analyze" / "index.md"
OUTPUT.parent.mkdir(exist_ok=True)

# -----------------------------
# DATA MODEL
# -----------------------------


@dataclass
class Doc:
    file_path: Path
    rel: str
    content: str
    mtime: datetime

    def sha8(self) -> str:
        h = hashlib.sha256(self.content.encode()).hexdigest()
        return h[:8]


# -----------------------------
# LOAD DOCS
# -----------------------------


def read_text_safe(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def load_docs(folder: Path) -> List[Doc]:

    docs: List[Doc] = []

    if not folder.exists():
        return docs

    for f in sorted(folder.glob("*.md")):

        content = read_text_safe(f)

        mtime = datetime.fromtimestamp(
            f.stat().st_mtime,
            tz=timezone.utc,
        )

        docs.append(
            Doc(
                file_path=f,
                rel=str(f.relative_to(ROOT)),
                content=content,
                mtime=mtime,
            )
        )

    return docs


# -----------------------------
# COUNT KEYWORDS
# -----------------------------


def count_keyword(docs: List[Doc], words: List[str]) -> int:

    total = 0

    for d in docs:
        lower = d.content.lower()

        for w in words:
            total += lower.count(w)

    return total


# -----------------------------
# MAIN
# -----------------------------


def main():

    incidents = load_docs(INCIDENTS_DIR)
    logs_all = load_docs(LOGS_DIR)

    now = datetime.now(timezone.utc)

    # Recent window
    recent_days = 7
    recent_cutoff = now - timedelta(days=recent_days)

    recent_incidents = [
        d for d in incidents if d.mtime >= recent_cutoff
    ]

    recent_logs = [
        d for d in logs_all if d.mtime >= recent_cutoff
    ]

    combined = incidents + logs_all

    report: list[str] = []

    # -------------------------------------------------
    # HEADER
    # -------------------------------------------------

    report.append("# RTS Analyze")
    report.append("")
    report.append(
        f"Generated: {now.strftime('%Y-%m-%d %H:%M UTC')}"
    )
    report.append("")
    report.append("---")
    report.append("")

    # -------------------------------------------------
    # INCIDENT TREND
    # -------------------------------------------------

    report.append("## Incident Trend")
    report.append("")

    report.append(
        f"- incidents observed: {len(incidents)}"
    )

    if incidents:
        latest = max(i.mtime for i in incidents)
        report.append(
            f"- latest incident: {latest.strftime('%Y-%m-%d %H:%M UTC')}"
        )

    report.append("")
    report.append("---")
    report.append("")

    # -------------------------------------------------
    # RISK TOPICS
    # -------------------------------------------------

    risk_topics = {
        "failure": ["failure"],
        "error": ["error"],
        "server error": ["internal server error"],
        "workflow interruption": ["workflow interruption"],
        "auth": ["author"],
        "token": ["token"],
    }

    report.append("## Risk Topic Ranking")
    report.append("")

    ranking = []

    for k, words in risk_topics.items():
        score = count_keyword(combined, words)
        ranking.append((score, k))

    ranking.sort(reverse=True)

    for score, name in ranking:
        report.append(f"- {name}: {score}")

    report.append("")
    report.append("---")
    report.append("")

    # -------------------------------------------------
    # GOVERNANCE SCORE
    # -------------------------------------------------

    gov_words = {
        "operator": ["operator"],
        "verification": ["verification"],
        "evidence": ["evidence"],
        "policy": ["policy"],
        "human": ["human"],
        "deletion": ["deletion"],
    }

    gov_score = {}

    for key, words in gov_words.items():
        gov_score[key] = count_keyword(
            combined,
            words,
        )

    report.append("## Governance Score")
    report.append("")

    total = sum(gov_score.values())

    report.append(f"- Governance Score: {total}")
    report.append("")

    for k, v in gov_score.items():
        report.append(f"- {k}: {v}")

    report.append("")
    report.append("---")
    report.append("")

    # -------------------------------------------------
    # FINAL FORM
    # -------------------------------------------------

    report.append("## Future Risk Radar")
    report.append("")

    failure_hits = count_keyword(
        recent_incidents,
        ["failure"],
    )

    error_hits = count_keyword(
        recent_incidents,
        ["error"],
    )

    wf_hits = count_keyword(
        recent_incidents,
        ["workflow"],
    )

    report.append(
        f"- recent failures: {failure_hits}"
    )

    report.append(
        f"- recent errors: {error_hits}"
    )

    report.append(
        f"- workflow interruptions: {wf_hits}"
    )

    report.append("")

    pressure = (
        failure_hits * 4
        + error_hits * 3
        + wf_hits * 2
        + len(recent_incidents) * 2
        + len(recent_logs)
    )

    report.append("### Failure Pressure Index")
    report.append("")
    report.append(
        f"- Failure Pressure Index: {pressure}"
    )

    report.append("")
    report.append("---")
    report.append("")

    # -------------------------------------------------
    # RECOVERY HEALTH
    # -------------------------------------------------

    report.append("## Recovery Health")
    report.append("")

    recoveries = 0

    for d in logs_all:

        lower = d.content.lower()

        if "recovery" in lower or "reconstruct" in lower:
            recoveries += 1

    report.append(
        f"- recovery evidence: {recoveries}"
    )

    capability = "HIGH" if recoveries >= 3 else "LOW"

    report.append(
        f"- recovery capability: {capability}"
    )

    report.append("")
    report.append("---")
    report.append("")

    # -------------------------------------------------
    # PROVENANCE
    # -------------------------------------------------

    report.append("## Provenance")
    report.append("")

    report.append(
        "- This report is generated by `scripts/analyze.py`."
    )

    report.append(
        "- Sources are not modified. Only parsed."
    )

    report.append(
        "- Evidence links point to repository paths."
    )

    report.append("")

    OUTPUT.write_text(
        "\n".join(report),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()

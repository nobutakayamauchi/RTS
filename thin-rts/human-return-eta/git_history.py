#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
import subprocess


class GitHistoryError(RuntimeError):
    pass


def git_commits(repo: Path, max_count: int) -> list[dict]:
    if max_count < 2:
        raise GitHistoryError("max_count must be at least 2")
    cp = subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "log",
            f"--max-count={max_count}",
            "--reverse",
            "--format=%H%x09%cI%x09%s",
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if cp.returncode != 0:
        raise GitHistoryError(cp.stderr.strip() or "git log failed")
    rows = []
    for raw in cp.stdout.splitlines():
        parts = raw.split("\t", 2)
        if len(parts) != 3:
            continue
        sha, timestamp, subject = parts
        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except ValueError as e:
            raise GitHistoryError(f"invalid git timestamp: {timestamp!r}") from e
        if dt.tzinfo is None or dt.utcoffset() is None:
            raise GitHistoryError("git timestamp must be timezone-aware")
        rows.append({"sha": sha, "timestamp": dt, "subject": subject})
    return rows


def adjacent_weak_history(
    commits: list[dict],
    *,
    task_class: str,
    max_gap_minutes: float,
    weighted_chunks: float | None = None,
) -> list[dict]:
    if max_gap_minutes <= 0:
        raise GitHistoryError("max_gap_minutes must be positive")
    if weighted_chunks is not None and weighted_chunks <= 0:
        raise GitHistoryError("weighted_chunks must be positive when present")
    records = []
    for previous, current in zip(commits, commits[1:]):
        seconds = (current["timestamp"] - previous["timestamp"]).total_seconds()
        if seconds <= 0:
            continue
        minutes = seconds / 60.0
        if minutes > max_gap_minutes:
            continue
        record = {
            "task_class": task_class,
            "started_at": previous["timestamp"].isoformat(),
            "human_hinge_at": current["timestamp"].isoformat(),
            "terminal": "GIT_COMMIT",
            "evidence_strength": "WEAK",
            "source": f"git-adjacent:{previous['sha'][:12]}..{current['sha'][:12]}",
        }
        if weighted_chunks is not None:
            record["weighted_chunks"] = weighted_chunks
        records.append(record)
    return records


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Export adjacent Git commit intervals as WEAK Human Return ETA history. "
            "Adjacent timestamps are approximation evidence, not proof of active work duration."
        )
    )
    parser.add_argument("--repo", required=True)
    parser.add_argument("--task-class", required=True)
    parser.add_argument("--max-count", type=int, default=100)
    parser.add_argument("--max-gap-minutes", type=float, default=30.0)
    parser.add_argument("--weighted-chunks", type=float)
    args = parser.parse_args()

    try:
        commits = git_commits(Path(args.repo), args.max_count)
        records = adjacent_weak_history(
            commits,
            task_class=args.task_class,
            max_gap_minutes=args.max_gap_minutes,
            weighted_chunks=args.weighted_chunks,
        )
    except GitHistoryError as e:
        print(json.dumps({"goal": "ERROR", "error": str(e)}, ensure_ascii=False))
        return 2

    for record in records:
        print(json.dumps(record, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

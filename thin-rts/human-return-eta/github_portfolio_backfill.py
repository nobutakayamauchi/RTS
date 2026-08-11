#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request


class BackfillError(RuntimeError):
    pass


def stable_repo_key(full_name: str) -> str:
    value = full_name.strip().lower()
    if not value or "/" not in value:
        raise BackfillError("repository full name must be owner/name")
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:20]


def parse_github_time(value: str) -> datetime:
    text = str(value).strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(text)
    except ValueError as e:
        raise BackfillError(f"invalid GitHub timestamp: {value!r}") from e
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise BackfillError("GitHub timestamp must be timezone-aware")
    return dt


def sessionize_commits(
    commits: list[dict],
    *,
    repo_full_name: str,
    max_gap_minutes: float = 30.0,
) -> list[dict]:
    if max_gap_minutes <= 0:
        raise BackfillError("max_gap_minutes must be positive")
    repo_key = stable_repo_key(repo_full_name)
    normalized = []
    for item in commits:
        if not isinstance(item, dict):
            continue
        sha = str(item.get("sha", "")).strip()
        stamp = item.get("timestamp")
        if not sha or not stamp:
            continue
        normalized.append((parse_github_time(stamp), sha))
    normalized.sort(key=lambda pair: pair[0])
    if len(normalized) < 2:
        return []

    sessions: list[list[tuple[datetime, str]]] = []
    current = [normalized[0]]
    for item in normalized[1:]:
        gap = (item[0] - current[-1][0]).total_seconds() / 60.0
        if gap <= 0:
            continue
        if gap <= max_gap_minutes:
            current.append(item)
        else:
            if len(current) >= 2:
                sessions.append(current)
            current = [item]
    if len(current) >= 2:
        sessions.append(current)

    out = []
    for session in sessions:
        start = session[0][0]
        end = session[-1][0]
        if end <= start:
            continue
        out.append({
            "task_class": f"github_repo_session::{repo_key}",
            "started_at": start.isoformat(),
            "human_hinge_at": end.isoformat(),
            "terminal": "GIT_SESSION_END",
            "evidence_strength": "WEAK",
            "source": (
                f"github-portfolio:{repo_key}:"
                f"{session[0][1][:12]}..{session[-1][1][:12]}"
            ),
        })
    return out


def github_get_json(url: str, token: str | None) -> object:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "thin-rts-human-return-eta-backfill",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as e:
        raise BackfillError(f"GitHub API HTTP {e.code} for {url}") from e
    except urllib.error.URLError as e:
        raise BackfillError(f"GitHub API connection failed for {url}: {e.reason}") from e


def list_owned_repositories(token: str, owner: str) -> list[dict]:
    repos = []
    page = 1
    while True:
        query = urllib.parse.urlencode({
            "affiliation": "owner",
            "per_page": 100,
            "page": page,
            "sort": "full_name",
        })
        payload = github_get_json(f"https://api.github.com/user/repos?{query}", token)
        if not isinstance(payload, list):
            raise BackfillError("unexpected repository list response")
        matched = [r for r in payload if isinstance(r, dict) and r.get("owner", {}).get("login") == owner]
        repos.extend(matched)
        if len(payload) < 100:
            break
        page += 1
    return repos


def list_repo_commits(
    token: str | None,
    full_name: str,
    *,
    max_commits: int,
    since: str | None = None,
) -> list[dict]:
    if max_commits < 2:
        raise BackfillError("max_commits must be at least 2")
    commits = []
    page = 1
    while len(commits) < max_commits:
        remaining = min(100, max_commits - len(commits))
        params = {"per_page": remaining, "page": page}
        if since:
            params["since"] = since
        encoded = urllib.parse.urlencode(params)
        payload = github_get_json(
            f"https://api.github.com/repos/{full_name}/commits?{encoded}", token
        )
        if not isinstance(payload, list):
            raise BackfillError(f"unexpected commit list response for {full_name}")
        for item in payload:
            if not isinstance(item, dict):
                continue
            commit = item.get("commit") or {}
            committer = commit.get("committer") or {}
            author = commit.get("author") or {}
            stamp = committer.get("date") or author.get("date")
            sha = item.get("sha")
            if stamp and sha:
                commits.append({"sha": str(sha), "timestamp": str(stamp)})
        if len(payload) < remaining:
            break
        page += 1
    return commits[:max_commits]


def backfill_owner(
    *,
    owner: str,
    token: str,
    max_commits_per_repo: int,
    max_gap_minutes: float,
    since: str | None,
) -> tuple[list[dict], dict]:
    repos = list_owned_repositories(token, owner)
    records: list[dict] = []
    skipped = 0
    for repo in repos:
        full_name = str(repo.get("full_name", "")).strip()
        if not full_name:
            skipped += 1
            continue
        try:
            commits = list_repo_commits(
                token,
                full_name,
                max_commits=max_commits_per_repo,
                since=since,
            )
            records.extend(sessionize_commits(
                commits,
                repo_full_name=full_name,
                max_gap_minutes=max_gap_minutes,
            ))
        except BackfillError:
            skipped += 1
    summary = {
        "owner": owner,
        "repositories_seen": len(repos),
        "repositories_skipped": skipped,
        "weak_sessions_emitted": len(records),
        "privacy": "repository names and commit messages are not emitted",
        "evidence_strength": "WEAK",
    }
    return records, summary


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Backfill GitHub commit-session timing as privacy-minimized WEAK ETA evidence. "
            "This is calibration evidence, not proof of continuous active work."
        )
    )
    parser.add_argument("--owner", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--max-commits-per-repo", type=int, default=1000)
    parser.add_argument("--max-gap-minutes", type=float, default=30.0)
    parser.add_argument("--since")
    parser.add_argument("--token-env", default="GITHUB_TOKEN")
    args = parser.parse_args()

    token = os.environ.get(args.token_env)
    if not token:
        print(json.dumps({
            "goal": "APPROVAL_REQUIRED",
            "reason": f"set {args.token_env} in the private runtime to read the authenticated GitHub portfolio",
        }, ensure_ascii=False))
        return 3

    try:
        records, summary = backfill_owner(
            owner=args.owner,
            token=token,
            max_commits_per_repo=args.max_commits_per_repo,
            max_gap_minutes=args.max_gap_minutes,
            since=args.since,
        )
        output = Path(args.output).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("w", encoding="utf-8") as f:
            for record in records:
                f.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    except (BackfillError, OSError) as e:
        print(json.dumps({"goal": "ERROR", "error": str(e)}, ensure_ascii=False))
        return 2

    print(json.dumps({"goal": "BACKFILL_READY", **summary, "output": str(output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

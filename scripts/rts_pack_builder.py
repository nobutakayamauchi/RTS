import os
import json
import hashlib
import urllib.request
from datetime import datetime, timezone, timedelta

JST = timezone(timedelta(hours=9))


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def jst_now_iso() -> str:
    return datetime.now(JST).replace(microsecond=0).isoformat()


def http_get_json(url: str, token: str) -> dict:
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    with urllib.request.urlopen(req) as resp:
        data = resp.read()
    return json.loads(data.decode("utf-8"))


def stable_sha256(obj: dict) -> str:
    s = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def safe_filename(s: str) -> str:
    if not s:
        return "unknown"
    s = s.strip().replace(" ", "_")
    out = []
    for ch in s:
        if ch.isalnum() or ch in ["_", "-", "."]:
            out.append(ch)
        else:
            out.append("_")
    return "".join(out)[:120] or "unknown"


def parse_int(v: str | None, default: int) -> int:
    try:
        return int(str(v).strip())
    except Exception:
        return default


def main() -> None:
    token = os.environ.get("GITHUB_TOKEN", "")
    repo = os.environ.get("REPO", "")
    target_workflow = os.environ.get("TARGET_WORKFLOW", "")
    run_id = os.environ.get("TARGET_RUN_ID", "")
    run_attempt = os.environ.get("TARGET_RUN_ATTEMPT", "1")
    head_sha = os.environ.get("TARGET_HEAD_SHA", "")
    branch = os.environ.get("TARGET_BRANCH", "")
    actor = os.environ.get("TARGET_ACTOR", "")
    conclusion = os.environ.get("TARGET_CONCLUSION", "")

    # Escalation knobs
    window_n = parse_int(os.environ.get("WINDOW_N"), 12)
    fail_threshold_last_n = parse_int(os.environ.get("FAIL_THRESHOLD_LAST_N"), 1)
    burst_minutes = parse_int(os.environ.get("BURST_MINUTES"), 30)
    burst_fail_threshold = parse_int(os.environ.get("BURST_FAIL_THRESHOLD"), 2)

    if not token:
        raise SystemExit("Missing GITHUB_TOKEN")
    if not repo:
        raise SystemExit("Missing REPO")
    if not target_workflow:
        raise SystemExit("Missing TARGET_WORKFLOW")
    if not run_id:
        raise SystemExit("Missing TARGET_RUN_ID")

    owner, name = repo.split("/", 1)

    # 1) workflow list -> workflow_id
    workflows_json = http_get_json(
        f"https://api.github.com/repos/{owner}/{name}/actions/workflows",
        token,
    )
    workflows = workflows_json.get("workflows", [])
    wf_id = None
    for wf in workflows:
        if wf.get("name") == target_workflow or wf.get("path", "").endswith(target_workflow):
            wf_id = wf.get("id")
            break

    # 2) recent runs for this workflow
    recent_runs = []
    if wf_id is not None:
        runs_json = http_get_json(
            f"https://api.github.com/repos/{owner}/{name}/actions/workflows/{wf_id}/runs?per_page=50",
            token,
        )
        recent_runs = runs_json.get("workflow_runs", [])
    else:
        # fallback: try repo runs
        runs_json = http_get_json(
            f"https://api.github.com/repos/{owner}/{name}/actions/runs?per_page=50",
            token,
        )
        recent_runs = runs_json.get("workflow_runs", [])

    # 3) compute stats
    fail_like = {"failure", "cancelled", "timed_out", "action_required"}
    now_utc = datetime.now(timezone.utc)
    burst_cutoff = now_utc - timedelta(minutes=burst_minutes)

    last_n = recent_runs[:window_n]
    last_n_conclusions = [str(r.get("conclusion") or "").lower() for r in last_n]

    fail_count_last_n = sum(1 for c in last_n_conclusions if c in fail_like)

    burst_fail = 0
    for r in recent_runs[: max(20, window_n)]:
        c = str(r.get("conclusion") or "").lower()
        updated_at = r.get("updated_at") or r.get("run_started_at") or ""
        if not updated_at:
            continue
        try:
            # GitHub returns Z, python accepts +00:00
            s = updated_at.replace("Z", "+00:00")
            dt = datetime.fromisoformat(s)
        except Exception:
            continue
        if dt >= burst_cutoff and c in fail_like:
            burst_fail += 1

    escalated = (fail_count_last_n >= fail_threshold_last_n) or (burst_fail >= burst_fail_threshold)

    # 4) run detail snapshot (Level 2)
    run_detail = {}
    try:
        run_detail = http_get_json(
            f"https://api.github.com/repos/{owner}/{name}/actions/runs/{run_id}",
            token,
        )
    except Exception as e:
        run_detail = {"error": f"failed_to_fetch_run_detail: {e!r}"}

    # Snapshot payload: evidence-only (facts), no inference
    snapshot_payload = {
        "repo": repo,
        "workflow": target_workflow,
        "run_id": run_id,
        "run_attempt": str(run_attempt),
        "actor": actor,
        "branch": branch,
        "head_sha": head_sha,
        "conclusion": conclusion,
        "generated_at_utc": utc_now_iso(),
        "generated_at_jst": jst_now_iso(),
        "stats": {
            "window_n": window_n,
            "fail_threshold_last_n": fail_threshold_last_n,
            "burst_minutes": burst_minutes,
            "burst_fail_threshold": burst_fail_threshold,
            "fail_count_last_n": fail_count_last_n,
            "burst_fail": burst_fail,
            "last_n_conclusions": last_n_conclusions,
        },
        "recent_runs_slice": [
            {
                "id": r.get("id"),
                "run_number": r.get("run_number"),
                "conclusion": r.get("conclusion"),
                "updated_at": r.get("updated_at"),
                "html_url": r.get("html_url"),
            }
            for r in recent_runs[: min(12, len(recent_runs))]
        ],
        "run_detail_excerpt": {
            "name": run_detail.get("name"),
            "status": run_detail.get("status"),
            "conclusion": run_detail.get("conclusion"),
            "created_at": run_detail.get("created_at"),
            "updated_at": run_detail.get("updated_at"),
            "run_number": run_detail.get("run_number"),
            "run_attempt": run_detail.get("run_attempt"),
            "html_url": run_detail.get("html_url"),
            "event": run_detail.get("event"),
            "head_branch": run_detail.get("head_branch"),
            "head_sha": run_detail.get("head_sha"),
        },
        "provenance": {
            "source": "GitHub Actions API",
            "note": "evidence-only; analysis separated in pack markdown",
        },
    }

    snapshot_hash = stable_sha256(snapshot_payload)

    # 5) write snapshot file (JSON) + evidence pack (MD)
    os.makedirs("incidents/evidence_snapshots", exist_ok=True)
    os.makedirs("incidents/evidence_packs", exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    safe_wf = safe_filename(target_workflow)
    snap_name = f"SNAP_{ts}_{safe_wf}_run{run_id}_a{run_attempt}.json"
    snap_path = os.path.join("incidents/evidence_snapshots", snap_name)

    with open(snap_path, "w", encoding="utf-8") as f:
        json.dump(snapshot_payload, f, ensure_ascii=False, indent=2)

    run_url = f"https://github.com/{repo}/actions/runs/{run_id}"

    # Evidence Level:
    # - Level 0: counters only
    # - Level 1: external reference URL
    # - Level 2: archived snapshot + hash  (we are here)
    evidence_level = 2

    ep_name = f"EP_{ts}_{safe_wf}.md"
    ep_path = os.path.join("incidents/evidence_packs", ep_name)

    # Analysis must NOT add facts, only interpretation of the evidence already in Evidence.
    analysis_lines = [
        f"- Rule: fail_count_last_n >= {fail_threshold_last_n}  -> {fail_count_last_n} >= {fail_threshold_last_n}",
        f"- Rule: burst_fail >= {burst_fail_threshold} (within {burst_minutes}m) -> {burst_fail} >= {burst_fail_threshold}",
        "- Interpretation: repeated failures/cancellations increase operational risk (no root-cause assumed).",
    ]

    conclusion_lines = []
    if escalated:
        conclusion_lines.append("- Decision: ESCALATE = YES")
        conclusion_lines.append("- Next: open or link an Incident Issue; attach this Evidence Pack + Snapshot.")
        conclusion_lines.append("- Next: run Sentinel Analyze (if not already) to collect broader context.")
    else:
        conclusion_lines.append("- Decision: ESCALATE = NO (monitor)")
        conclusion_lines.append("- Next: keep collecting evidence; escalate when thresholds are met.")

    with open(ep_path, "w", encoding="utf-8") as f:
        f.write("# RTS Evidence Pack\n\n")

        f.write("## Evidence (Facts Only)\n")
        f.write(f"- repo: {repo}\n")
        f.write(f"- workflow: {target_workflow}\n")
        f.write(f"- run_id: {run_id}\n")
        f.write(f"- run_attempt: {run_attempt}\n")
        f.write(f"- run_url: {run_url}\n")
        f.write(f"- actor: {actor}\n")
        f.write(f"- branch: {branch}\n")
        f.write(f"- head_sha: {head_sha}\n")
        f.write(f"- conclusion: {conclusion}\n")
        f.write(f"- generated_at_utc: {snapshot_payload['generated_at_utc']}\n")
        f.write(f"- generated_at_jst: {snapshot_payload['generated_at_jst']}\n")
        f.write(f"- evidence_level: Level {evidence_level}\n")
        f.write("\n")

        f.write("### Escalation Rule (Parameters)\n")
        f.write(f"- window_n: {window_n}\n")
        f.write(f"- fail_threshold_last_n: {fail_threshold_last_n}\n")
        f.write(f"- burst_minutes: {burst_minutes}\n")
        f.write(f"- burst_fail_threshold: {burst_fail_threshold}\n")
        f.write("\n")

        f.write("### Stats (Measured)\n")
        f.write(f"- fail_count_last_n: {fail_count_last_n}\n")
        f.write(f"- burst_fail: {burst_fail}\n")
        f.write(f"- last_n_conclusions: {last_n_conclusions}\n")
        f.write("\n")

        f.write("### Snapshot (Archived)\n")
        f.write(f"- snapshot_path: {snap_path}\n")
        f.write(f"- snapshot_hash_sha256: {snapshot_hash}\n")
        f.write("\n")

        f.write("## Analysis (Interpretation Only)\n")
        for line in analysis_lines:
            f.write(f"{line}\n")
        f.write("\n")

        f.write("## Conclusion (Decision)\n")
        for line in conclusion_lines:
            f.write(f"{line}\n")
        f.write("\n")

        f.write("## Notes\n")
        f.write("- Evidence / Analysis / Conclusion are intentionally separated.\n")
        f.write("- No root cause is asserted without separate verification.\n")

    print(f"[ok] snapshot: {snap_path}")
    print(f"[ok] evidence_pack: {ep_path}")
    print(f"[ok] evidence_level: {evidence_level}")
    print(f"[ok] escalated: {escalated}")


if __name__ == "__main__":
    main()

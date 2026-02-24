import os
import json
import hashlib
import urllib.request
from datetime import datetime, timezone, timedelta

JST_OFFSET = timedelta(hours=9)

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def jst_now_iso() -> str:
    dt = datetime.now(timezone.utc) + JST_OFFSET
    # keep as +09:00
    return dt.replace(microsecond=0).isoformat() + "+09:00"

def http_get_json(url: str, token: str) -> dict:
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def stable_sha256(obj: dict) -> str:
    s = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def parse_bool(s: str, default=False) -> bool:
    if s is None:
        return default
    return s.strip().lower() in ("1", "true", "yes", "y", "on")

def main() -> None:
    token = os.environ.get("GITHUB_TOKEN", "")
    repo = os.environ.get("REPO", "")
    if not token or not repo:
        raise SystemExit("Missing GITHUB_TOKEN or REPO env.")

    target_workflow = os.environ.get("TARGET_WORKFLOW_NAME", "")
    run_id = os.environ.get("TARGET_RUN_ID", "")
    run_attempt = os.environ.get("TARGET_RUN_ATTEMPT", "")
    head_sha = os.environ.get("TARGET_HEAD_SHA", "")
    branch = os.environ.get("TARGET_BRANCH", "")
    conclusion = os.environ.get("TARGET_CONCLUSION", "")
    actor = os.environ.get("TARGET_ACTOR", "")

    window_n = int(os.environ.get("WINDOW_LAST_N", "5"))
    fail_threshold_last_n = int(os.environ.get("FAIL_THRESHOLD_IN_LAST_N", "3"))
    burst_minutes = int(os.environ.get("BURST_MINUTES", "10"))
    burst_fail_threshold = int(os.environ.get("BURST_FAIL_THRESHOLD", "2"))

    important_only = parse_bool(os.environ.get("IMPORTANT_ONLY", "false"))
    important_list_raw = os.environ.get("IMPORTANT_WORKFLOWS", "")
    important_workflows = [x.strip() for x in important_list_raw.split(",") if x.strip()]

    # Optional: ignore non-important workflows to reduce noise
    if important_only and target_workflow and target_workflow not in important_workflows:
        print(f"[skip] workflow '{target_workflow}' not in IMPORTANT_WORKFLOWS")
        return

    # Fetch recent runs for the same workflow (by workflow name -> find workflow id)
    owner, name = repo.split("/", 1)

    # List workflows to resolve workflow_id by name
    wf_list = http_get_json(f"https://api.github.com/repos/{repo}/actions/workflows", token)
    workflows = wf_list.get("workflows", [])
    wf_id = None
    for wf in workflows:
        if wf.get("name") == target_workflow:
            wf_id = wf.get("id")
            break

    # If not found (some events may have unusual names), fallback: record minimal pack without history
    if wf_id is None:
        print("[warn] workflow id not found; creating evidence pack with minimal data")
        recent_runs = []
    else:
        runs_json = http_get_json(
            f"https://api.github.com/repos/{repo}/actions/workflows/{wf_id}/runs?per_page={max(10, window_n)}",
            token
        )
        recent_runs = runs_json.get("workflow_runs", [])

    # Compute failure stats
    now_utc = datetime.now(timezone.utc)
    burst_cutoff = now_utc - timedelta(minutes=burst_minutes)

    last_n = recent_runs[:window_n]
    last_n_conclusions = [(r.get("id"), r.get("conclusion"), r.get("updated_at")) for r in last_n]

    fail_like = {"failure", "cancelled", "timed_out"}
    fail_count_last_n = sum(1 for _, c, __ in last_n_conclusions if (c in fail_like))

    burst_fail = 0
    for r in recent_runs[:max(20, window_n)]:
        c = r.get("conclusion")
        updated_at = r.get("updated_at")
        if not updated_at:
            continue
        try:
            dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
        except Exception:
            continue
        if dt >= burst_cutoff and c in fail_like:
            burst_fail += 1

    escalated = (fail_count_last_n >= fail_threshold_last_n) or (burst_fail >= burst_fail_threshold)

    print(f"[stats] workflow='{target_workflow}' last_n_fail={fail_count_last_n}/{len(last_n)} burst_fail={burst_fail} in {burst_minutes}m escalated={escalated}")

    if not escalated:
        # Not "obvious incident" yet -> do nothing heavy
        return

    # Build Evidence Pack
    pack_dir = os.path.join("incidents", "evidence_packs")
    os.makedirs(pack_dir, exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")
    safe_wf = "".join(ch if ch.isalnum() else "_" for ch in (target_workflow or "workflow"))[:40]
    filename = f"EP_{ts}_run-{run_id}_{safe_wf}.md"
    path = os.path.join(pack_dir, filename)

    # Run URL
    run_url = f"https://github.com/{repo}/actions/runs/{run_id}"

    payload_for_hash = {
        "repo": repo,
        "workflow": target_workflow,
        "run_id": run_id,
        "run_attempt": run_attempt,
        "head_sha": head_sha,
        "branch": branch,
        "conclusion": conclusion,
        "actor": actor,
        "window_last_n": window_n,
        "fail_threshold_last_n": fail_threshold_last_n,
        "burst_minutes": burst_minutes,
        "burst_fail_threshold": burst_fail_threshold,
        "stats": {
            "fail_count_last_n": fail_count_last_n,
            "burst_fail": burst_fail,
            "last_n": last_n_conclusions,
        },
        "generated_at_utc": utc_now_iso(),
    }
    content_hash = stable_sha256(payload_for_hash)

    # Try fetching run details (helps with "what job failed")
    run_detail = {}
    try:
        run_detail = http_get_json(f"https://api.github.com/repos/{repo}/actions/runs/{run_id}", token)
    except Exception as e:
        run_detail = {"error": f"failed to fetch run detail: {e}"}

    # Write pack (lightweight but audit-grade)
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# RTS Evidence Pack (Escalated)\n\n")
        f.write(f"generated_at_utc: {utc_now_iso()}\n")
        f.write(f"generated_at_jst: {jst_now_iso()}\n\n")

        f.write("## Trigger\n")
        f.write(f"- workflow: `{target_workflow}`\n")
        f.write(f"- conclusion: `{conclusion}`\n")
        f.write(f"- run_id: `{run_id}` (attempt `{run_attempt}`)\n")
        f.write(f"- run_url: {run_url}\n")
        f.write(f"- actor: `{actor}`\n")
        f.write(f"- head_sha: `{head_sha}`\n")
        f.write(f"- branch: `{branch}`\n\n")

        f.write("## Escalation Rule\n")
        f.write(f"- last {window_n} runs failures >= {fail_threshold_last_n}\n")
        f.write(f"- OR failures in last {burst_minutes} min >= {burst_fail_threshold}\n\n")

        f.write("## Stats\n")
        f.write(f"- fail_count_last_n: {fail_count_last_n}/{len(last_n)}\n")
        f.write(f"- burst_fail: {burst_fail}\n\n")

        f.write("### last_n (id, conclusion, updated_at)\n")
        for rid, conc, upd in last_n_conclusions:
            f.write(f"- {rid} | {conc} | {upd}\n")
        f.write("\n")

        f.write("## Provenance\n")
        f.write(f"- repo: `{repo}`\n")
        f.write(f"- workflow_run event source\n\n")

        f.write("## Integrity\n")
        f.write(f"- content_hash_sha256: `{content_hash}`\n\n")

        f.write("## Run Detail (JSON excerpt)\n")
        # Keep it bounded (avoid huge)
        excerpt = {
            "name": run_detail.get("name"),
            "status": run_detail.get("status"),
            "conclusion": run_detail.get("conclusion"),
            "created_at": run_detail.get("created_at"),
            "updated_at": run_detail.get("updated_at"),
            "run_started_at": run_detail.get("run_started_at"),
            "html_url": run_detail.get("html_url"),
            "event": run_detail.get("event"),
            "head_branch": run_detail.get("head_branch"),
            "head_sha": run_detail.get("head_sha"),
        }
        f.write("```json\n")
        f.write(json.dumps(excerpt, ensure_ascii=False, indent=2))
        f.write("\n```\n")

    print(f"[ok] Evidence pack created: {path}")

if __name__ == "__main__":
    main()

import os
import json
import hashlib
import urllib.request
from datetime import datetime, timezone, timedelta


# Timezones
JST = timezone(timedelta(hours=9))


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def jst_now_iso() -> str:
    return datetime.now(JST).replace(microsecond=0).isoformat()


def parse_bool(s: str | None, default: bool = False) -> bool:
    if s is None:
        return default
    return str(s).strip().lower() in ("1", "true", "yes", "y", "on")


def stable_sha256(obj: dict) -> str:
    """Stable JSON -> sha256 hex"""
    s = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def http_get_json(url: str, token: str) -> dict:
    req = urllib.request.Request(url, method="GET")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    with urllib.request.urlopen(req) as resp:
        data = resp.read()
    return json.loads(data.decode("utf-8"))


def safe_filename(s: str) -> str:
    s = s.strip().replace(" ", "_")
    out = []
    for ch in s:
        if ch.isalnum() or ch in ("_", "-", ".", "@"):
            out.append(ch)
        else:
            out.append("_")
    return "".join(out)[:120] if out else "unknown"


def iso_to_dt(s: str) -> datetime | None:
    """
    GitHub returns ISO8601 like '2026-02-24T00:44:29Z'
    Python fromisoformat needs '+00:00'
    """
    if not s:
        return None
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        return datetime.fromisoformat(s)
    except Exception:
        return None


def main() -> None:
    # --- Required envs (set by workflow) ---
    token = os.environ.get("GITHUB_TOKEN", "")
    repo = os.environ.get("REPO", "")  # owner/name

    target_workflow = os.environ.get("TARGET_WORKFLOW", "")  # workflow name (not file)
    run_id = os.environ.get("TARGET_RUN_ID", "")
    run_attempt = os.environ.get("TARGET_RUN_ATTEMPT", "1")
    head_sha = os.environ.get("TARGET_SHA", "")
    branch = os.environ.get("TARGET_BRANCH", "")
    conclusion = os.environ.get("TARGET_CONCLUSION", "")
    actor = os.environ.get("TARGET_ACTOR", "")

    if not token:
        raise SystemExit("Missing GITHUB_TOKEN")
    if not repo:
        raise SystemExit("Missing REPO (owner/name)")
    if not target_workflow:
        raise SystemExit("Missing TARGET_WORKFLOW")
    if not run_id:
        raise SystemExit("Missing TARGET_RUN_ID")

    # --- Escalation knobs (safe defaults) ---
    window_n = int(os.environ.get("WINDOW_N", "6"))
    fail_threshold_last_n = int(os.environ.get("FAIL_THRESHOLD_LAST_N", "3"))
    burst_minutes = int(os.environ.get("BURST_MINUTES", "30"))
    burst_fail_threshold = int(os.environ.get("BURST_FAIL_THRESHOLD", "2"))

    important_only = parse_bool(os.environ.get("IMPORTANT_ONLY"), default=False)
    important_list_raw = os.environ.get("IMPORTANT_WORKFLOWS", "").strip()
    important_workflows = [x.strip() for x in important_list_raw.split(",") if x.strip()]

    if important_only and important_workflows and target_workflow not in important_workflows:
        print(f"[skip] workflow not in IMPORTANT_WORKFLOWS: {target_workflow}")
        return

    owner, name = repo.split("/", 1)

    # 1) Resolve workflow id by name
    wf_id = None
    workflows_json = http_get_json(f"https://api.github.com/repos/{owner}/{name}/actions/workflows", token)
    for wf in workflows_json.get("workflows", []):
        if wf.get("name") == target_workflow:
            wf_id = wf.get("id")
            break

    # 2) Fetch recent runs for that workflow (if we have wf_id)
    recent_runs = []
    if wf_id is None:
        print(f"[warn] workflow id not found by name='{target_workflow}'. escalation calc may be weaker.")
    else:
        runs_json = http_get_json(
            f"https://api.github.com/repos/{owner}/{name}/actions/workflows/{wf_id}/runs?per_page=50",
            token,
        )
        recent_runs = runs_json.get("workflow_runs", []) or []

    # 3) Compute failure stats
    fail_like = {"failure", "cancelled", "timed_out", "startup_failure"}
    now_utc = datetime.now(timezone.utc)
    burst_cutoff = now_utc - timedelta(minutes=burst_minutes)

    last_n = recent_runs[:max(1, window_n)]
    last_n_conclusions = [r.get("conclusion") for r in last_n]
    fail_count_last_n = sum(1 for c in last_n_conclusions if c in fail_like)

    burst_fail = 0
    for r in recent_runs[:max(20, window_n)]:
        c = r.get("conclusion")
        updated_at = r.get("updated_at") or r.get("run_started_at") or r.get("created_at")
        dt = iso_to_dt(updated_at)
        if dt is None:
            continue
        if dt >= burst_cutoff and c in fail_like:
            burst_fail += 1

    escalated = (fail_count_last_n >= fail_threshold_last_n) or (burst_fail >= burst_fail_threshold)

    print(f"[stats] workflow='{target_workflow}' run_id={run_id} attempt={run_attempt} conclusion={conclusion}")
    print(f"[stats] window_n={window_n} fail_count_last_n={fail_count_last_n} threshold={fail_threshold_last_n}")
    print(f"[stats] burst_minutes={burst_minutes} burst_fail={burst_fail} threshold={burst_fail_threshold}")
    print(f"[decision] escalated={escalated}")

    if not escalated:
        return

    # 4) Fetch run detail (best effort)
    run_detail = {}
    try:
        run_detail = http_get_json(f"https://api.github.com/repos/{owner}/{name}/actions/runs/{run_id}", token)
    except Exception as e:
        run_detail = {"error": f"run detail fetch failed: {e}"}
        print(f"[warn] run detail fetch failed: {e}")

    run_url = f"https://github.com/{repo}/actions/runs/{run_id}"

    # 5) Build evidence pack payload -> hash
    payload_for_hash = {
        "repo": repo,
        "workflow": target_workflow,
        "run_id": run_id,
        "run_attempt": run_attempt,
        "head_sha": head_sha,
        "branch": branch,
        "conclusion": conclusion,
        "actor": actor,
        "window": {
            "n": window_n,
            "fail_threshold_last_n": fail_threshold_last_n,
            "burst_minutes": burst_minutes,
            "burst_fail_threshold": burst_fail_threshold,
        },
        "stats": {
            "fail_count_last_n": fail_count_last_n,
            "burst_fail": burst_fail,
            "last_n_conclusions": last_n_conclusions,
        },
        "generated_at_utc": utc_now_iso(),
        "generated_at_jst": jst_now_iso(),
        "run_url": run_url,
    }
    content_hash = stable_sha256(payload_for_hash)

    # 6) Write evidence markdown into incidents/evidence_snapshots/
    pack_dir = os.path.join("incidents", "evidence_snapshots")
    os.makedirs(pack_dir, exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    safe_wf = safe_filename(target_workflow)
    filename = f"ESC_{ts}_{safe_wf}_run{run_id}_a{run_attempt}.md"
    path = os.path.join(pack_dir, filename)

    # keep file size reasonable
    excerpt = {
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
    }
    # keep only a small slice of recent runs (for audit)
    recent_slice = []
    for r in recent_runs[:max(10, window_n)]:
        recent_slice.append(
            {
                "id": r.get("id"),
                "run_number": r.get("run_number"),
                "conclusion": r.get("conclusion"),
                "updated_at": r.get("updated_at"),
                "html_url": r.get("html_url"),
            }
        )

    with open(path, "w", encoding="utf-8") as f:
        f.write("# RTS Evidence Pack (Escalation)\n\n")
        f.write(f"- generated_at_utc: {payload_for_hash['generated_at_utc']}\n")
        f.write(f"- generated_at_jst: {payload_for_hash['generated_at_jst']}\n")
        f.write(f"- repo: {repo}\n")
        f.write(f"- workflow: {target_workflow}\n")
        f.write(f"- run_id: {run_id}\n")
        f.write(f"- run_attempt: {run_attempt}\n")
        f.write(f"- run_url: {run_url}\n")
        f.write(f"- actor: {actor}\n")
        f.write(f"- branch: {branch}\n")
        f.write(f"- conclusion: {conclusion}\n")
        f.write(f"- head_sha: {head_sha}\n")
        f.write("\n---\n\n")

        f.write("## Escalation Rule\n")
        f.write(f"- window_n: {window_n}\n")
        f.write(f"- fail_threshold_last_n: {fail_threshold_last_n}\n")
        f.write(f"- burst_minutes: {burst_minutes}\n")
        f.write(f"- burst_fail_threshold: {burst_fail_threshold}\n")
        f.write("\n")

        f.write("## Stats\n")
        f.write(f"- fail_count_last_n: {fail_count_last_n}\n")
        f.write(f"- burst_fail: {burst_fail}\n")
        f.write(f"- last_n_conclusions: {last_n_conclusions}\n")
        f.write("\n")

        f.write("## Integrity\n")
        f.write(f"- content_hash_sha256: {content_hash}\n")
        f.write("\n")

        f.write("## Recent Runs (slice)\n")
        for r in recent_slice:
            f.write(f"- {r.get('updated_at')} | #{r.get('run_number')} | {r.get('conclusion')} | {r.get('html_url')}\n")
        f.write("\n")

        f.write("## Run Detail (excerpt)\n")
        f.write("```json\n")
        f.write(json.dumps(excerpt, ensure_ascii=False, indent=2))
        f.write("\n```\n\n")

        f.write("## Provenance\n")
        f.write("- source: GitHub Actions API\n")
        f.write("- note: evidence-only; no inference beyond counters\n")

    print(f"[ok] Escalation evidence written: {path}")


if __name__ == "__main__":
    main()

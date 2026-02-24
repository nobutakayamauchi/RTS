import os
import json
import hashlib
import urllib.request
from datetime import datetime, timezone, timedelta

# ---- Timezones ----
JST = timezone(timedelta(hours=9))

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def jst_now_iso() -> str:
    return datetime.now(JST).replace(microsecond=0).isoformat()

def parse_bool(s: str | None, default: bool = False) -> bool:
    if s is None:
        return default
    return str(s).strip().lower() in ("1", "true", "yes", "y", "on")

def stable_sha256(obj: dict) -> str:
    # canonical json -> sha256
    b = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(b).hexdigest()

def http_get_json(url: str, token: str) -> dict:
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = resp.read().decode("utf-8")
    return json.loads(data)

def safe_filename(s: str) -> str:
    # keep it simple and filesystem safe
    s = (s or "").strip().replace(" ", "_")
    out = []
    for ch in s:
        if ch.isalnum() or ch in ("-", "_", "."):
            out.append(ch)
        else:
            out.append("_")
    return "".join(out)[:120] if out else "unknown"

def main() -> None:
    # ---- Required env (set by workflow) ----
    token = os.environ.get("GITHUB_TOKEN", "")
    repo = os.environ.get("REPO", "")  # owner/name
    target_workflow = os.environ.get("TARGET_WORKFLOW", "")
    run_id = os.environ.get("TARGET_RUN_ID", "")
    run_attempt = os.environ.get("TARGET_RUN_ATTEMPT", "")
    head_sha = os.environ.get("TARGET_HEAD_SHA", "")
    branch = os.environ.get("TARGET_BRANCH", "")
    conclusion = os.environ.get("TARGET_CONCLUSION", "")
    actor = os.environ.get("TARGET_ACTOR", "")

    # Escalation knobs
    window_n = int(os.environ.get("WINDOW_N", "12"))
    fail_threshold_last_n = int(os.environ.get("FAIL_THRESHOLD_LAST_N", "3"))
    burst_minutes = int(os.environ.get("BURST_MINUTES", "30"))
    burst_fail_threshold = int(os.environ.get("BURST_FAIL_THRESHOLD", "3"))

    # Optional allowlist
    important_only = parse_bool(os.environ.get("IMPORTANT_ONLY", "false"), default=False)
    important_list_raw = os.environ.get("IMPORTANT_WORKFLOWS", "")
    important_workflows = [x.strip() for x in important_list_raw.split(",") if x.strip()]

    if not token:
        raise SystemExit("Missing GITHUB_TOKEN")
    if not repo:
        raise SystemExit("Missing REPO")
    if not target_workflow:
        raise SystemExit("Missing TARGET_WORKFLOW")
    if not run_id:
        raise SystemExit("Missing TARGET_RUN_ID")

    if important_only and important_workflows and (target_workflow not in important_workflows):
        print(f"[skip] workflow not in important list: {target_workflow}")
        return

    owner, name = repo.split("/", 1)

    # ---- 1) Resolve workflow_id by name ----
    workflows_json = http_get_json(f"https://api.github.com/repos/{owner}/{name}/actions/workflows", token)
    wf_id = None
    for wf in workflows_json.get("workflows", []):
        if wf.get("name") == target_workflow:
            wf_id = wf.get("id")
            break

    # ---- 2) Fetch recent runs for that workflow (or fallback) ----
    recent_runs = []
    if wf_id is not None:
        runs_json = http_get_json(
            f"https://api.github.com/repos/{owner}/{name}/actions/workflows/{wf_id}/runs?per_page=50",
            token,
        )
        recent_runs = runs_json.get("workflow_runs", [])
    else:
        # fallback: list runs for repo (less precise)
        runs_json = http_get_json(
            f"https://api.github.com/repos/{owner}/{name}/actions/runs?per_page=50",
            token,
        )
        recent_runs = runs_json.get("workflow_runs", [])

    # ---- 3) Compute failure stats ----
    fail_like = {"failure", "cancelled", "timed_out", "action_required"}
    now_utc = datetime.now(timezone.utc)
    burst_cutoff = now_utc - timedelta(minutes=burst_minutes)

    last_n = recent_runs[:max(1, window_n)]
    last_n_conclusions = []
    burst_fail = 0

    def parse_dt(s: str | None) -> datetime | None:
        if not s:
            return None
        try:
            # GitHub gives ISO8601 (often endswith Z)
            if s.endswith("Z"):
                s = s[:-1] + "+00:00"
            return datetime.fromisoformat(s)
        except Exception:
            return None

    for r in last_n:
        c = (r.get("conclusion") or r.get("status") or "unknown")
        last_n_conclusions.append(str(c))
    fail_count_last_n = sum(1 for c in last_n_conclusions if c in fail_like)

    # burst fail count: look at first 50 runs and count failures updated within window
    for r in recent_runs[:50]:
        c = (r.get("conclusion") or r.get("status") or "unknown")
        dt = parse_dt(r.get("updated_at")) or parse_dt(r.get("created_at"))
        if dt and dt >= burst_cutoff and c in fail_like:
            burst_fail += 1

    escalated = (fail_count_last_n >= fail_threshold_last_n) or (burst_fail >= burst_fail_threshold)

    print(f"[stats] workflow='{target_workflow}' wf_id={wf_id}")
    print(f"[stats] last_n={window_n} fail_count_last_n={fail_count_last_n} threshold={fail_threshold_last_n}")
    print(f"[stats] burst_minutes={burst_minutes} burst_fail={burst_fail} threshold={burst_fail_threshold}")
    print(f"[decision] escalated={escalated}")

    if not escalated:
        return

    # ---- 4) Snapshot Freeze (Level2) ----
    # Fetch run detail + jobs detail and save as immutable snapshot
    run_url = f"https://github.com/{owner}/{name}/actions/runs/{run_id}"

    run_detail = {}
    jobs_detail = {}
    try:
        run_detail = http_get_json(f"https://api.github.com/repos/{owner}/{name}/actions/runs/{run_id}", token)
    except Exception as e:
        run_detail = {"error": f"run_detail_fetch_failed: {e!r}", "run_id": run_id}

    try:
        jobs_detail = http_get_json(
            f"https://api.github.com/repos/{owner}/{name}/actions/runs/{run_id}/jobs?per_page=100",
            token,
        )
    except Exception as e:
        jobs_detail = {"error": f"jobs_fetch_failed: {e!r}", "run_id": run_id}

    snapshot_payload = {
        "schema": "RTS_SNAPSHOT_V1",
        "generated_at_utc": utc_now_iso(),
        "generated_at_jst": jst_now_iso(),
        "repo": repo,
        "workflow": target_workflow,
        "run_id": str(run_id),
        "run_attempt": str(run_attempt),
        "run_url": run_url,
        "actor": actor,
        "branch": branch,
        "head_sha": head_sha,
        "conclusion": conclusion,
        "rule": {
            "window_n": window_n,
            "fail_threshold_last_n": fail_threshold_last_n,
            "burst_minutes": burst_minutes,
            "burst_fail_threshold": burst_fail_threshold,
            "important_only": important_only,
            "important_workflows": important_workflows,
        },
        "stats": {
            "fail_count_last_n": fail_count_last_n,
            "burst_fail": burst_fail,
            "last_n_conclusions": last_n_conclusions,
        },
        "run_detail": run_detail,
        "jobs_detail": jobs_detail,
    }

    snapshot_hash = stable_sha256(snapshot_payload)

    # Paths
    ts = datetime.now(JST).strftime("%Y%m%d_%H%M%S")
    wf_safe = safe_filename(target_workflow)
    snap_dir = os.path.join("incidents", "evidence_snapshots")
    pack_dir = os.path.join("incidents", "evidence_packs")
    os.makedirs(snap_dir, exist_ok=True)
    os.makedirs(pack_dir, exist_ok=True)

    snap_filename = f"SNAP_{ts}_{wf_safe}_run{run_id}_a{run_attempt}_L2.json"
    snap_path = os.path.join(snap_dir, snap_filename)

    with open(snap_path, "w", encoding="utf-8") as f:
        json.dump(snapshot_payload, f, ensure_ascii=False, indent=2, sort_keys=True)

    # ---- 5) Evidence Pack (human-readable index) ----
    pack_filename = f"EP_{ts}.md"
    pack_path = os.path.join(pack_dir, pack_filename)

    # small recent slice for quick glance (kept small on purpose)
    recent_slice = []
    for r in recent_runs[:min(12, len(recent_runs))]:
        recent_slice.append(
            {
                "created_at": r.get("created_at"),
                "updated_at": r.get("updated_at"),
                "run_number": r.get("run_number"),
                "conclusion": r.get("conclusion"),
                "html_url": r.get("html_url"),
            }
        )

    with open(pack_path, "w", encoding="utf-8") as f:
        f.write("# RTS Evidence Pack (Escalation)\n\n")
        f.write("## Evidence Level\n")
        f.write("- level: 2  (archived snapshot + hash)\n\n")

        f.write("## Evidence (Frozen)\n")
        f.write(f"- run_url: {run_url}\n")
        f.write(f"- snapshot_path: {snap_path}\n")
        f.write(f"- snapshot_hash_sha256: {snapshot_hash}\n\n")

        f.write("## Trigger\n")
        f.write(f"- workflow: {target_workflow}\n")
        f.write(f"- conclusion: {conclusion}\n")
        f.write(f"- actor: {actor}\n")
        f.write(f"- branch: {branch}\n")
        f.write(f"- head_sha: {head_sha}\n")
        f.write(f"- run_id: {run_id}\n")
        f.write(f"- run_attempt: {run_attempt}\n\n")

        f.write("## Escalation Rule\n")
        f.write(f"- window_n: {window_n}\n")
        f.write(f"- fail_threshold_last_n: {fail_threshold_last_n}\n")
        f.write(f"- burst_minutes: {burst_minutes}\n")
        f.write(f"- burst_fail_threshold: {burst_fail_threshold}\n\n")

        f.write("## Stats\n")
        f.write(f"- fail_count_last_n: {fail_count_last_n}\n")
        f.write(f"- burst_fail: {burst_fail}\n")
        f.write(f"- last_n_conclusions: {last_n_conclusions}\n\n")

        f.write("## Recent Runs (slice)\n")
        for r in recent_slice:
            f.write(
                f"- {r.get('created_at')} | #{r.get('run_number')} | {r.get('conclusion')} | {r.get('html_url')}\n"
            )
        f.write("\n")

        f.write("## Inference Separation\n")
        f.write("- Evidence: frozen snapshot + hash (above)\n")
        f.write("- Analysis: (human/agent writes later)\n")
        f.write("- Conclusion: (human/agent writes later)\n\n")

        f.write("## Provenance\n")
        f.write("- source: GitHub Actions API\n")
        f.write("- note: snapshot is evidence-only; do not infer beyond counters without separate analysis\n")

    print(f"[ok] snapshot saved: {snap_path}")
    print(f"[ok] evidence pack saved: {pack_path}")

if __name__ == "__main__":
    main()

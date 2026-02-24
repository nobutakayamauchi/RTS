import os
import json
import hashlib
import urllib.request
from datetime import datetime, timezone, timedelta

JST = timezone(timedelta(hours=9))

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def jst_now_iso() -> str:
    return datetime.now(JST).replace(microsecond=0).isoformat()

def http_get_json(url: str, token: str) -> dict:
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def stable_sha256(obj: dict) -> str:
    s = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def parse_bool(s: str | None, default: bool = False) -> bool:
    if s is None:
        return default
    return str(s).strip().lower() in ("1", "true", "yes", "y", "on")

def main() -> None:
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    repo = os.environ.get("REPO", "").strip()
    target_workflow = os.environ.get("TARGET_WORKFLOW", "").strip()
    run_id = os.environ.get("TARGET_RUN_ID", "").strip()
    run_attempt = os.environ.get("TARGET_RUN_ATTEMPT", "").strip()
    head_sha = os.environ.get("TARGET_HEAD_SHA", "").strip()
    branch = os.environ.get("TARGET_BRANCH", "").strip()
    conclusion = os.environ.get("TARGET_CONCLUSION", "").strip()
    actor = os.environ.get("TARGET_ACTOR", "").strip()

    # Escalation knobs
    window_n = int(os.environ.get("WINDOW_N", "10"))
    fail_threshold_last_n = int(os.environ.get("FAIL_THRESHOLD_LAST_N", "4"))
    burst_minutes = int(os.environ.get("BURST_MINUTES", "30"))
    burst_fail_threshold = int(os.environ.get("BURST_FAIL_THRESHOLD", "3"))
    important_only = parse_bool(os.environ.get("IMPORTANT_ONLY"), default=False)
    important_list_raw = os.environ.get("IMPORTANT_WORKFLOWS", "").strip()

    if not token:
        raise SystemExit("Missing GITHUB_TOKEN")
    if not repo:
        raise SystemExit("Missing REPO (owner/name)")
    if not target_workflow:
        raise SystemExit("Missing TARGET_WORKFLOW")
    if not run_id:
        raise SystemExit("Missing TARGET_RUN_ID")

    important_workflows = []
    if important_list_raw:
        important_workflows = [x.strip() for x in important_list_raw.split(",") if x.strip()]

    if important_only and important_workflows and target_workflow not in important_workflows:
        print(f"[skip] workflow not in IMPORTANT_WORKFLOWS: {target_workflow}")
        return

    owner, name = repo.split("/", 1)

    # 1) workflow一覧から workflow_id を解決
    workflows = http_get_json(f"https://api.github.com/repos/{owner}/{name}/actions/workflows", token).get("workflows", [])
    wf_id = None
    for wf in workflows:
        if wf.get("name") == target_workflow or wf.get("path", "").endswith(f"/{target_workflow}"):
            wf_id = wf.get("id")
            break
    if wf_id is None:
        # 名前が取れないケースがあるので、runのworkflow_urlから取るのが理想だが、まずは安全にログを出して継続
        print(f"[warn] workflow_id not resolved for '{target_workflow}'. Escalation check degraded.")
        recent_runs = []
    else:
        runs_json = http_get_json(
            f"https://api.github.com/repos/{owner}/{name}/actions/workflows/{wf_id}/runs?per_page=50",
            token,
        )
        recent_runs = runs_json.get("workflow_runs", [])

    # 2) failure計測
    fail_like = {"failure", "cancelled", "timed_out"}
    now_utc = datetime.now(timezone.utc)
    burst_cutoff = now_utc - timedelta(minutes=burst_minutes)

    last_n = recent_runs[:window_n]
    last_n_conclusions = [r.get("conclusion") for r in last_n]
    fail_count_last_n = sum(1 for c in last_n_conclusions if c in fail_like)

    burst_fail = 0
    for r in recent_runs[:max(20, window_n)]:
        c = r.get("conclusion")
        updated_at = r.get("updated_at")
        if not updated_at:
            continue
        try:
            dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
        except Exception as e:
            print(f"[warn] time parse failed: {updated_at} err={e}")
            continue
        if dt >= burst_cutoff and c in fail_like:
            burst_fail += 1

    escalated = (fail_count_last_n >= fail_threshold_last_n) or (burst_fail >= burst_fail_threshold)

    print(f"[stats] workflow='{target_workflow}' run_id={run_id} attempt={run_attempt} branch='{branch}' conclusion='{conclusion}'")
    print(f"[stats] last_n={window_n} fail_count_last_n={fail_count_last_n} threshold={fail_threshold_last_n}")
    print(f"[stats] burst_minutes={burst_minutes} burst_fail={burst_fail} threshold={burst_fail_threshold}")
    print(f"[decision] escalated={escalated}")

    if not escalated:
        return

    # 3) Evidence Pack 作成
    pack_dir = os.path.join("incidents", "escalations")
    os.makedirs(pack_dir, exist_ok=True)

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

    # run詳細（取れたら）
    run_detail = {}
    try:
        run_detail = http_get_json(f"https://api.github.com/repos/{owner}/{name}/actions/runs/{run_id}", token)
    except Exception as e:
        print(f"[warn] run detail fetch failed: {e}")
        run_detail = {"error": f"run detail fetch failed: {e}"}

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    safe_wf = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in target_workflow)[:40]
    filename = f"REP_{ts}_{safe_wf}_run{run_id}.md"
    path = os.path.join(pack_dir, filename)

    with open(path, "w", encoding="utf-8") as f:
        f.write("# RTS Evidence Pack\n\n")
        f.write(f"- generated_at_utc: {payload_for_hash['generated_at_utc']}\n")
        f.write(f"- generated_at_jst: {payload_for_hash['generated_at_jst']}\n")
        f.write(f"- repo: {repo}\n")
        f.write(f"- workflow: {target_workflow}\n")
        f.write(f"- run_id: {run_id}\n")
        f.write(f"- run_attempt: {run_attempt}\n")
        f.write(f"- branch: {branch}\n")
        f.write(f"- actor: {actor}\n")
        f.write(f"- conclusion: {conclusion}\n")
        f.write(f"- run_url: {run_url}\n")
        f.write(f"- content_hash_sha256: {content_hash}\n\n")

        f.write("## Escalation Rule\n\n")
        f.write(f"- last_n={window_n}, fail_threshold_last_n={fail_threshold_last_n}\n")
        f.write(f"- burst_minutes={burst_minutes}, burst_fail_threshold={burst_fail_threshold}\n\n")

        f.write("## Stats\n\n")
        f.write(f"- fail_count_last_n: {fail_count_last_n}\n")
        f.write(f"- burst_fail: {burst_fail}\n\n")
        f.write("### last_n (index | conclusion)\n\n")
        for idx, c in enumerate(last_n_conclusions):
            f.write(f"- {idx+1} | {c}\n")
        f.write("\n")

        f.write("## Run Detail (JSON excerpt)\n\n")
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
        f.write("```json\n")
        f.write(json.dumps(excerpt, ensure_ascii=False, indent=2))
        f.write("\n```\n")

    print(f"[ok] Escalation evidence pack created: {path}")

if __name__ == "__main__":
    main()

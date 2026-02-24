import os
import json
import hashlib
import urllib.request
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional, Tuple

JST = timezone(timedelta(hours=9))


# -------------------------
# Time helpers
# -------------------------
def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def jst_now_iso() -> str:
    return datetime.now(JST).replace(microsecond=0).isoformat()

def parse_iso_to_dt(s: str) -> Optional[datetime]:
    if not s:
        return None
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        return datetime.fromisoformat(s)
    except Exception:
        return None


# -------------------------
# Small utils
# -------------------------
def parse_bool(s: Optional[str], default: bool = False) -> bool:
    if s is None:
        return default
    return str(s).strip().lower() in ("1", "true", "yes", "y", "on")

def safe_filename(s: str, max_len: int = 120) -> str:
    s = (s or "").strip().replace(" ", "_")
    out = []
    for ch in s:
        if ch.isalnum() or ch in ("-", "_", "."):
            out.append(ch)
        else:
            out.append("_")
    t = "".join(out)
    return t[:max_len] if len(t) > max_len else t

def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def stable_json_dumps(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2)

def http_get(url: str, token: str, accept: str = "application/vnd.github+json") -> bytes:
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", accept)
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    with urllib.request.urlopen(req) as resp:
        return resp.read()

def http_get_json(url: str, token: str) -> Dict[str, Any]:
    raw = http_get(url, token, accept="application/vnd.github+json")
    return json.loads(raw.decode("utf-8"))


# -------------------------
# GitHub API helpers
# -------------------------
def split_repo(repo: str) -> Tuple[str, str]:
    if "/" not in repo:
        raise SystemExit(f"Invalid REPO='{repo}' (expected owner/name)")
    owner, name = repo.split("/", 1)
    return owner, name

def resolve_workflow_id_by_name(owner: str, name: str, token: str, workflow_name: str) -> Optional[int]:
    data = http_get_json(f"https://api.github.com/repos/{owner}/{name}/actions/workflows", token)
    for wf in data.get("workflows", []):
        if wf.get("name") == workflow_name:
            return wf.get("id")
    return None

def list_recent_runs(owner: str, name: str, token: str, workflow_id: int, branch: str) -> Dict[str, Any]:
    # per_page up to 100
    url = f"https://api.github.com/repos/{owner}/{name}/actions/workflows/{workflow_id}/runs?branch={branch}&per_page=50"
    return http_get_json(url, token)

def get_run(owner: str, name: str, token: str, run_id: str) -> Dict[str, Any]:
    return http_get_json(f"https://api.github.com/repos/{owner}/{name}/actions/runs/{run_id}", token)

def get_jobs(owner: str, name: str, token: str, run_id: str) -> Dict[str, Any]:
    # includes steps (but not full logs)
    return http_get_json(f"https://api.github.com/repos/{owner}/{name}/actions/runs/{run_id}/jobs?per_page=100", token)

def get_commit_json(owner: str, name: str, token: str, sha: str) -> Dict[str, Any]:
    return http_get_json(f"https://api.github.com/repos/{owner}/{name}/commits/{sha}", token)

def get_commit_diff(owner: str, name: str, token: str, sha: str) -> bytes:
    # GitHub diff
    url = f"https://api.github.com/repos/{owner}/{name}/commits/{sha}"
    return http_get(url, token, accept="application/vnd.github.v3.diff")


# -------------------------
# Evidence Level
# -------------------------
def compute_evidence_level(snapshot_saved: bool, extra_urls: Optional[str]) -> str:
    """
    Level 0: internal counters only (no snapshot, no external)
    Level 1: external reference URL (run_url etc) but no snapshot
    Level 2: archived snapshot + hash
    Level 3: multi-source corroborated (snapshot + >=1 extra reference URL)
    """
    urls = [u.strip() for u in (extra_urls or "").splitlines() if u.strip()]
    if snapshot_saved and len(urls) >= 1:
        return "L3"
    if snapshot_saved:
        return "L2"
    if len(urls) >= 1:
        return "L1"
    return "L0"


# -------------------------
# Main
# -------------------------
def main() -> None:
    token = os.environ.get("GITHUB_TOKEN", "")
    repo = os.environ.get("REPO", "")
    target_workflow = os.environ.get("TARGET_WORKFLOW", "")
    branch = os.environ.get("TARGET_BRANCH", "main")
    run_id = os.environ.get("TARGET_RUN_ID", "")
    run_attempt = os.environ.get("TARGET_RUN_ATTEMPT", "")
    head_sha = os.environ.get("TARGET_HEAD_SHA", "")
    conclusion = os.environ.get("TARGET_CONCLUSION", "")
    actor = os.environ.get("TARGET_ACTOR", "")
    extra_urls = os.environ.get("EXTRA_REFERENCE_URLS", "")  # optional multi-source

    # Escalation knobs
    window_n = int(os.environ.get("WINDOW_N", "12"))
    fail_threshold_last_n = int(os.environ.get("FAIL_THRESHOLD_LAST_N", "1"))
    burst_minutes = int(os.environ.get("BURST_MINUTES", "30"))
    burst_fail_threshold = int(os.environ.get("BURST_FAIL_THRESHOLD", "2"))
    important_only = parse_bool(os.environ.get("IMPORTANT_ONLY", "true"), default=True)
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

    if important_only and important_workflows and target_workflow not in important_workflows:
        print(f"[skip] workflow '{target_workflow}' not in IMPORTANT_WORKFLOWS")
        return

    owner, name = split_repo(repo)

    # Resolve workflow_id
    wf_id = resolve_workflow_id_by_name(owner, name, token, target_workflow)
    if wf_id is None:
        # If not found, proceed with minimal evidence (still snapshot run)
        print(f"[warn] workflow id not found for '{target_workflow}'")
        recent_runs = []
    else:
        runs_json = list_recent_runs(owner, name, token, wf_id, branch)
        recent_runs = runs_json.get("workflow_runs", [])

    # Fetch run detail of target
    run_detail = get_run(owner, name, token, run_id)

    # Compute failure stats
    fail_like = {"failure", "cancelled", "timed_out", "action_required", "stale", "skipped"}
    now_utc = datetime.now(timezone.utc)
    burst_cutoff = now_utc - timedelta(minutes=burst_minutes)

    last_n = recent_runs[:window_n] if recent_runs else []
    last_n_conclusions = []
    for r in last_n:
        last_n_conclusions.append(r.get("conclusion") or r.get("status") or "unknown")

    fail_count_last_n = sum(1 for c in last_n_conclusions if (c or "").lower() in fail_like)

    burst_fail = 0
    # scan up to first 50
    for r in (recent_runs[:50] if recent_runs else []):
        c = (r.get("conclusion") or "").lower()
        updated_at = r.get("updated_at") or r.get("run_started_at") or r.get("created_at")
        dt = parse_iso_to_dt(updated_at or "")
        if not dt:
            continue
        if dt >= burst_cutoff and c in fail_like:
            burst_fail += 1

    escalated = (fail_count_last_n >= fail_threshold_last_n) or (burst_fail >= burst_fail_threshold)

    print(f"[stats] workflow='{target_workflow}' branch='{branch}'")
    print(f"[stats] window_n={window_n} fail_threshold_last_n={fail_threshold_last_n}")
    print(f"[stats] fail_count_last_n={fail_count_last_n} burst_minutes={burst_minutes} burst_fail={burst_fail} burst_fail_threshold={burst_fail_threshold}")
    print(f"[decision] escalated={escalated}")

    if not escalated:
        return

    # -------------------------
    # Evidence Freeze (Snapshot Bundle)
    # -------------------------
    ensure_dir("incidents/evidence_snapshots")

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    safe_wf = safe_filename(target_workflow)
    safe_branch = safe_filename(branch)
    safe_actor = safe_filename(actor or "unknown")

    bundle_id = f"ESC_{ts}_{safe_wf}_run{run_id}_a{run_attempt or '1'}"
    bundle_dir = os.path.join("incidents/evidence_snapshots", bundle_id)
    ensure_dir(bundle_dir)

    # Save run.json
    run_json_path = os.path.join(bundle_dir, "run.json")
    with open(run_json_path, "w", encoding="utf-8") as f:
        f.write(stable_json_dumps(run_detail) + "\n")

    # Save jobs.json (best-effort)
    jobs_detail = {}
    try:
        jobs_detail = get_jobs(owner, name, token, run_id)
    except Exception as e:
        jobs_detail = {"error": f"failed to fetch jobs: {e!r}"}
    jobs_json_path = os.path.join(bundle_dir, "jobs.json")
    with open(jobs_json_path, "w", encoding="utf-8") as f:
        f.write(stable_json_dumps(jobs_detail) + "\n")

    # Save commit.json + diff.patch (best-effort)
    commit_json = {}
    diff_bytes = b""
    if head_sha:
        try:
            commit_json = get_commit_json(owner, name, token, head_sha)
        except Exception as e:
            commit_json = {"error": f"failed to fetch commit: {e!r}"}
        try:
            diff_bytes = get_commit_diff(owner, name, token, head_sha)
        except Exception as e:
            diff_bytes = f"failed to fetch diff: {e!r}\n".encode("utf-8")

    commit_json_path = os.path.join(bundle_dir, "commit.json")
    with open(commit_json_path, "w", encoding="utf-8") as f:
        f.write(stable_json_dumps(commit_json) + "\n")

    diff_path = os.path.join(bundle_dir, "commit.diff.patch")
    with open(diff_path, "wb") as f:
        f.write(diff_bytes)

    # Save recent_runs.json (slice)
    slice_obj = {
        "window_n": window_n,
        "recent_runs_slice": [
            {
                "id": r.get("id"),
                "run_number": r.get("run_number"),
                "status": r.get("status"),
                "conclusion": r.get("conclusion"),
                "created_at": r.get("created_at"),
                "updated_at": r.get("updated_at"),
                "html_url": r.get("html_url"),
            }
            for r in (recent_runs[:max(window_n, 20)] if recent_runs else [])
        ],
        "generated_at_utc": utc_now_iso(),
    }
    recent_runs_path = os.path.join(bundle_dir, "recent_runs.json")
    with open(recent_runs_path, "w", encoding="utf-8") as f:
        f.write(stable_json_dumps(slice_obj) + "\n")

    # Compute bundle manifest + bundle_hash (hash of hashes)
    files = ["run.json", "jobs.json", "commit.json", "commit.diff.patch", "recent_runs.json"]
    manifest = {
        "bundle_id": bundle_id,
        "repo": repo,
        "workflow": target_workflow,
        "branch": branch,
        "run_id": run_id,
        "run_attempt": run_attempt or "1",
        "generated_at_utc": utc_now_iso(),
        "generated_at_jst": jst_now_iso(),
        "files": {},
    }
    for fn in files:
        p = os.path.join(bundle_dir, fn)
        manifest["files"][fn] = sha256_file(p)

    manifest_bytes = stable_json_dumps(manifest).encode("utf-8")
    bundle_hash = sha256_bytes(manifest_bytes)

    manifest["bundle_hash_sha256"] = bundle_hash

    manifest_path = os.path.join(bundle_dir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        f.write(stable_json_dumps(manifest) + "\n")

    # Evidence Level
    evidence_level = compute_evidence_level(snapshot_saved=True, extra_urls=extra_urls)

    # Evidence.md (facts only)
    run_url = run_detail.get("html_url") or f"https://github.com/{repo}/actions/runs/{run_id}"
    created_at = run_detail.get("created_at") or ""
    updated_at = run_detail.get("updated_at") or ""

    evidence_md = []
    evidence_md.append("# RTS Evidence Pack (Escalation)")
    evidence_md.append("")
    evidence_md.append("## Evidence (Facts Only)")
    evidence_md.append(f"- repo: {repo}")
    evidence_md.append(f"- workflow: {target_workflow}")
    evidence_md.append(f"- branch: {branch}")
    evidence_md.append(f"- actor: {actor or 'unknown'}")
    evidence_md.append(f"- run_id: {run_id}")
    evidence_md.append(f"- run_attempt: {run_attempt or '1'}")
    evidence_md.append(f"- run_url: {run_url}")
    evidence_md.append(f"- conclusion: {conclusion or (run_detail.get('conclusion') or 'unknown')}")
    evidence_md.append(f"- created_at: {created_at}")
    evidence_md.append(f"- updated_at: {updated_at}")
    evidence_md.append(f"- generated_at_utc: {utc_now_iso()}")
    evidence_md.append(f"- generated_at_jst: {jst_now_iso()}")
    evidence_md.append("")
    evidence_md.append("## Evidence Level")
    evidence_md.append(f"- evidence_level: {evidence_level}")
    if extra_urls.strip():
        evidence_md.append("- extra_reference_urls:")
        for u in [x.strip() for x in extra_urls.splitlines() if x.strip()]:
            evidence_md.append(f"  - {u}")
    evidence_md.append("")
    evidence_md.append("## Escalation Rule (Counters)")
    evidence_md.append(f"- window_n: {window_n}")
    evidence_md.append(f"- fail_threshold_last_n: {fail_threshold_last_n}")
    evidence_md.append(f"- burst_minutes: {burst_minutes}")
    evidence_md.append(f"- burst_fail_threshold: {burst_fail_threshold}")
    evidence_md.append("")
    evidence_md.append("## Stats (Counters)")
    evidence_md.append(f"- fail_count_last_n: {fail_count_last_n}")
    evidence_md.append(f"- burst_fail: {burst_fail}")
    evidence_md.append(f"- last_n_conclusions: {last_n_conclusions}")
    evidence_md.append("")
    evidence_md.append("## Snapshot Bundle (Frozen)")
    evidence_md.append(f"- bundle_dir: incidents/evidence_snapshots/{bundle_id}/")
    evidence_md.append(f"- manifest: incidents/evidence_snapshots/{bundle_id}/manifest.json")
    evidence_md.append(f"- bundle_hash_sha256: {bundle_hash}")
    evidence_md.append("")
    evidence_md.append("## Inference Separation")
    evidence_md.append("- This file contains **evidence only** (facts/counters/snapshots).")
    evidence_md.append("- Analysis and conclusion should live in separate files (generated as stubs below).")
    evidence_md.append("")

    evidence_md_path = os.path.join(bundle_dir, "evidence.md")
    with open(evidence_md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(evidence_md) + "\n")

    # -------------------------
    # Separation stubs
    # -------------------------
    ensure_dir("analysis")
    ensure_dir("incidents")

    analysis_stub_name = f"ANL_{ts}_{safe_wf}_run{run_id}.md"
    analysis_stub_path = os.path.join("analysis", analysis_stub_name)

    analysis_stub = []
    analysis_stub.append("# RTS Analysis Draft")
    analysis_stub.append("")
    analysis_stub.append("## Inputs (Evidence)")
    analysis_stub.append(f"- evidence_pack: incidents/evidence_snapshots/{bundle_id}/evidence.md")
    analysis_stub.append(f"- manifest: incidents/evidence_snapshots/{bundle_id}/manifest.json")
    analysis_stub.append("")
    analysis_stub.append("## Hypotheses (Write your best guess)")
    analysis_stub.append("- H1:")
    analysis_stub.append("- H2:")
    analysis_stub.append("")
    analysis_stub.append("## Validation Plan (How to prove/deny)")
    analysis_stub.append("- Step 1:")
    analysis_stub.append("- Step 2:")
    analysis_stub.append("")
    analysis_stub.append("## Notes")
    analysis_stub.append("- Keep speculation here. Do NOT edit evidence pack.")
    analysis_stub.append("")

    with open(analysis_stub_path, "w", encoding="utf-8") as f:
        f.write("\n".join(analysis_stub) + "\n")

    incident_stub_name = f"INC_{ts}_{safe_wf}_run{run_id}_DRAFT.md"
    incident_stub_path = os.path.join("incidents", incident_stub_name)

    incident_stub = []
    incident_stub.append("# RTS Incident Draft (From Escalation)")
    incident_stub.append("")
    incident_stub.append("## Evidence (Links)")
    incident_stub.append(f"- evidence_pack: incidents/evidence_snapshots/{bundle_id}/evidence.md")
    incident_stub.append(f"- run_url: {run_url}")
    incident_stub.append("")
    incident_stub.append("## Analysis (Link)")
    incident_stub.append(f"- analysis_draft: analysis/{analysis_stub_name}")
    incident_stub.append("")
    incident_stub.append("## Conclusion (Fill later)")
    incident_stub.append("- status: INVESTIGATING")
    incident_stub.append("- root_cause: TBD")
    incident_stub.append("- fix: TBD")
    incident_stub.append("- prevention: TBD")
    incident_stub.append("")

    with open(incident_stub_path, "w", encoding="utf-8") as f:
        f.write("\n".join(incident_stub) + "\n")

    print(f"[ok] evidence bundle created: {bundle_dir}")
    print(f"[ok] evidence.md: {evidence_md_path}")
    print(f"[ok] analysis stub: {analysis_stub_path}")
    print(f"[ok] incident draft: {incident_stub_path}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
RTS Sessions rollup (FULL REPLACE)
- Read sessions/<YYYY-MM>/session_*.jsonl (JSON Lines)
- Validate ledger (parseable JSON, required keys, ts parseable)
- Sort events by timestamp
- Compute:
    * Counts by kind
    * Latest tail (sentinel.run)
    * Transitions (status flip / streak start-end / density spike)
    * Escalation metrics (fail_count_last_n, fail_density, burst_fail, recovery_speed, flip_frequency)
    * Mutation scoring (explainable components + weights)
- Write:
    sessions/<YYYY-MM>/index.json
    sessions/<YYYY-MM>/index.md
    incidents/evidence_snapshots/ESC_<YYYYMMDD>_<RULE>.md  (when breakpoint triggered)

Usage:
  python scripts/session_rollup.py 2026-02
  python scripts/session_rollup.py 2026-02 20260226   # optional day tag for evidence filename
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from glob import glob
from typing import Any, Dict, List, Optional, Tuple


# =========================
# Time / parsing utilities
# =========================

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_ts(ts: str) -> datetime:
    # expects "....Z" or ISO8601
    s = str(ts).strip()
    if s.endswith("Z"):
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    return datetime.fromisoformat(s)


def yyyymmdd_from_ts(ts: str) -> str:
    d = parse_ts(ts).astimezone(timezone.utc)
    return d.strftime("%Y%m%d")


def safe_load_json_line(line: str) -> Optional[Dict[str, Any]]:
    line = line.strip()
    if not line:
        return None
    try:
        obj = json.loads(line)
        if isinstance(obj, dict):
            return obj
        return None
    except Exception:
        return None


# =========================
# Validation / normalization
# =========================

REQUIRED_KEYS = ("ts", "kind")


def normalize_status(e: Dict[str, Any]) -> str:
    # prefer conclusion; fallback status
    v = e.get("conclusion") or e.get("status") or ""
    return str(v).strip().lower()


def is_failure_status(status: str) -> bool:
    # Phase 1 default: everything except "success" counts as failure.
    # Later you can refine (e.g., treat "cancelled" differently) by bumping rule version.
    s = str(status).lower()
    return s != "success"


@dataclass
class LedgerIssue:
    file: str
    line_no: int
    severity: str  # "WARN" or "ERROR"
    message: str


def validate_month_ledgers(month: str, jsonl_paths: List[str]) -> List[LedgerIssue]:
    issues: List[LedgerIssue] = []
    for p in jsonl_paths:
        base = os.path.basename(p)
        with open(p, "r", encoding="utf-8") as f:
            for i, line in enumerate(f, start=1):
                if not line.strip():
                    continue
                obj = safe_load_json_line(line)
                if obj is None:
                    issues.append(LedgerIssue(base, i, "ERROR", "invalid JSON"))
                    continue
                # required keys
                for k in REQUIRED_KEYS:
                    if k not in obj:
                        issues.append(LedgerIssue(base, i, "ERROR", f"missing key: {k}"))
                # ts parseable
                try:
                    parse_ts(str(obj.get("ts", "")))
                except Exception:
                    issues.append(LedgerIssue(base, i, "ERROR", "unparseable ts"))
    return issues


def read_month_events(month: str) -> Tuple[List[Dict[str, Any]], List[str], List[str]]:
    """
    returns: (events, ledger_filenames, ledger_paths)
    """
    month_dir = os.path.join("sessions", month)
    if not os.path.isdir(month_dir):
        return [], [], []

    jsonl_paths = sorted(glob(os.path.join(month_dir, "session_*.jsonl")))
    events: List[Dict[str, Any]] = []

    for p in jsonl_paths:
        with open(p, "r", encoding="utf-8") as f:
            for line in f:
                obj = safe_load_json_line(line)
                if obj is None:
                    continue
                if "ts" not in obj or "kind" not in obj:
                    continue
                events.append(obj)

    # stable sort by timestamp (UTC)
    events.sort(key=lambda e: parse_ts(str(e["ts"])))
    return events, [os.path.basename(p) for p in jsonl_paths], jsonl_paths


def count_by_kind(events: List[Dict[str, Any]]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for e in events:
        k = str(e.get("kind", "unknown"))
        counts[k] = counts.get(k, 0) + 1
    return counts


def tail(items: List[Any], n: int = 12) -> List[Any]:
    return items[-n:] if len(items) > n else items[:]


# =========================
# Transitions + metrics
# =========================

@dataclass
class Transition:
    ts: str
    kind: str
    severity: str
    title: str
    detail: str
    run_id: Optional[str] = None
    commit: Optional[str] = None


@dataclass
class EscalationMetrics:
    window_n: int
    fail_count_last_n: int
    fail_density: float
    burst_window_k: int
    burst_threshold_b: int
    burst_fail: bool
    recovery_speed_runs: Optional[int]
    flip_frequency_last_n: float
    flips_in_last_n: int


@dataclass
class MutationScore:
    rule_version: str
    weights: Dict[str, float]
    components: Dict[str, float]
    mutation_score: float
    breakpoint: bool
    breakpoint_reasons: List[str]


def compute_transitions_and_metrics(
    events: List[Dict[str, Any]],
    rule_version: str = "2026-02",
) -> Tuple[List[Transition], Optional[EscalationMetrics], Optional[MutationScore]]:
    """
    Operates on sentinel.run stream only.
    Returns (latest_transitions, latest_metrics, latest_mutation_score)
    """
    sentinel = [e for e in events if e.get("kind") == "sentinel.run"]
    if not sentinel:
        return [], None, None

    # normalize
    statuses = [normalize_status(e) for e in sentinel]
    times = [str(e["ts"]) for e in sentinel]

    # Params (Phase 2 defaults)
    WINDOW_N = 20
    BURST_K = 5
    BURST_B = 3
    SPIKE_DENSITY_DELTA = 0.20  # density jump threshold vs previous window
    FLIP_WINDOW_N = 20

    # helper: failure flags
    fails = [1 if is_failure_status(s) else 0 for s in statuses]

    # transitions
    transitions: List[Transition] = []

    def mk_detail(e: Dict[str, Any]) -> str:
        wf = str(e.get("workflow") or "RTS Sentinel Analyze").strip()
        rid = str(e.get("run_id") or "").strip()
        commit = str(e.get("commit") or "").strip()
        parts = []
        if wf:
            parts.append(f"workflow={wf}")
        if rid:
            parts.append(f"run={rid}")
        if commit:
            parts.append(f"commit={commit}")
        return " ".join(parts).strip()

    # 1) status flip + record flip count
    flips_idx: List[int] = []
    for i in range(1, len(sentinel)):
        ps, cs = statuses[i - 1], statuses[i]
        if ps != cs:
            flips_idx.append(i)
            sev = "HIGH" if is_failure_status(cs) else "MED"
            transitions.append(
                Transition(
                    ts=times[i],
                    kind="sentinel.run",
                    severity=sev,
                    title=f"status flip: {ps} → {cs}",
                    detail=mk_detail(sentinel[i]),
                    run_id=str(sentinel[i].get("run_id")) if sentinel[i].get("run_id") else None,
                    commit=str(sentinel[i].get("commit")) if sentinel[i].get("commit") else None,
                )
            )

    # 2) failure streak boundaries (start/end)
    for i in range(1, len(statuses)):
        ps, cs = statuses[i - 1], statuses[i]
        prev_fail = is_failure_status(ps)
        cur_fail = is_failure_status(cs)

        if (not prev_fail) and cur_fail:
            transitions.append(
                Transition(
                    ts=times[i],
                    kind="sentinel.run",
                    severity="HIGH",
                    title="failure streak started",
                    detail=mk_detail(sentinel[i]),
                    run_id=str(sentinel[i].get("run_id")) if sentinel[i].get("run_id") else None,
                    commit=str(sentinel[i].get("commit")) if sentinel[i].get("commit") else None,
                )
            )
        if prev_fail and (not cur_fail):
            transitions.append(
                Transition(
                    ts=times[i],
                    kind="sentinel.run",
                    severity="MED",
                    title="failure streak ended (recovery)",
                    detail=mk_detail(sentinel[i]),
                    run_id=str(sentinel[i].get("run_id")) if sentinel[i].get("run_id") else None,
                    commit=str(sentinel[i].get("commit")) if sentinel[i].get("commit") else None,
                )
            )

    # 3) density spike (compare window densities)
    # density_now (last WINDOW_N ending at i) vs density_prev (the window before it)
    def window_density(end_i: int, n: int) -> float:
        start = max(0, end_i - n + 1)
        w = fails[start:end_i + 1]
        if not w:
            return 0.0
        return sum(w) / float(len(w))

    for i in range(len(sentinel)):
        if i < 2:
            continue
        dn = window_density(i, WINDOW_N)
        dp = window_density(i - 1, WINDOW_N)
        if (dn - dp) >= SPIKE_DENSITY_DELTA and is_failure_status(statuses[i]):
            transitions.append(
                Transition(
                    ts=times[i],
                    kind="sentinel.run",
                    severity="HIGH",
                    title="failure density spike",
                    detail=f"fail_density_last_{WINDOW_N}={dn:.3f} (+{(dn-dp):.3f}) {mk_detail(sentinel[i])}".strip(),
                    run_id=str(sentinel[i].get("run_id")) if sentinel[i].get("run_id") else None,
                    commit=str(sentinel[i].get("commit")) if sentinel[i].get("commit") else None,
                )
            )

    # sort transitions by ts, keep latest 12 (human-first)
    transitions.sort(key=lambda t: parse_ts(t.ts))
    latest_transitions = transitions[-12:]

    # ---- Metrics (latest only) ----
    last_i = len(sentinel) - 1
    n_eff = min(WINDOW_N, len(sentinel))
    last_window = fails[-n_eff:]
    fail_count_last_n = sum(last_window)
    fail_density = fail_count_last_n / float(n_eff) if n_eff else 0.0

    # burst
    k_eff = min(BURST_K, len(sentinel))
    burst_window = fails[-k_eff:]
    burst_fail = sum(burst_window) >= BURST_B

    # recovery_speed_runs: compute last failure streak end -> next success runs
    recovery_speed_runs: Optional[int] = None
    # find last index where streak ended (failure -> non-failure)
    last_end: Optional[int] = None
    for i in range(1, len(sentinel)):
        if is_failure_status(statuses[i - 1]) and (not is_failure_status(statuses[i])):
            last_end = i  # recovery moment at i
    # If there is an ongoing failure streak at end, recovery speed is unknown
    if last_end is not None:
        # recovery speed = 0 at the recovery event itself (already success)
        recovery_speed_runs = 0

    # flip frequency in last FLIP_WINDOW_N
    fn_eff = min(FLIP_WINDOW_N, len(sentinel))
    # count flips where index i is within last fn_eff events
    flips_in_last_n = sum(1 for idx in flips_idx if idx >= (len(sentinel) - fn_eff))
    flip_frequency_last_n = flips_in_last_n / float(fn_eff) if fn_eff else 0.0

    metrics = EscalationMetrics(
        window_n=WINDOW_N,
        fail_count_last_n=fail_count_last_n,
        fail_density=float(fail_density),
        burst_window_k=BURST_K,
        burst_threshold_b=BURST_B,
        burst_fail=bool(burst_fail),
        recovery_speed_runs=recovery_speed_runs,
        flip_frequency_last_n=float(flip_frequency_last_n),
        flips_in_last_n=int(flips_in_last_n),
    )

    # ---- Mutation scoring (Phase 3) ----
    # Components (explainable)
    # - fail_density_delta: density_now - density_prev_window (approx: compare last window vs window ending at i-n_eff)
    # - streak_length: ongoing failure streak length (normalized)
    # - burst_spike: 1/0
    # - flip_frequency: as above

    density_now = fail_density
    # density_prev: window ending at (last_i - n_eff) (previous chunk)
    prev_end = last_i - n_eff
    if prev_end >= 0:
        density_prev = window_density(prev_end, WINDOW_N)
    else:
        density_prev = 0.0
    fail_density_delta = max(0.0, density_now - density_prev)

    # ongoing streak length at end
    streak_len = 0
    j = last_i
    while j >= 0 and is_failure_status(statuses[j]):
        streak_len += 1
        j -= 1
    # normalize streak length (cap)
    STREAK_CAP = 10
    streak_norm = min(streak_len, STREAK_CAP) / float(STREAK_CAP)

    burst_spike = 1.0 if burst_fail else 0.0
    flip_freq = flip_frequency_last_n

    # weights (tunable)
    weights = {
        "w1_fail_density_delta": 0.40,
        "w2_streak_length": 0.30,
        "w3_burst_spike": 0.20,
        "w4_flip_frequency": 0.10,
    }

    components = {
        "fail_density_delta": float(fail_density_delta),      # 0..1-ish
        "streak_length": float(streak_norm),                  # 0..1
        "burst_spike": float(burst_spike),                    # 0/1
        "flip_frequency": float(flip_freq),                   # 0..1
    }

    mutation_score = (
        weights["w1_fail_density_delta"] * components["fail_density_delta"]
        + weights["w2_streak_length"] * components["streak_length"]
        + weights["w3_burst_spike"] * components["burst_spike"]
        + weights["w4_flip_frequency"] * components["flip_frequency"]
    )

    # breakpoint rules (OR) — aligns with your "structural breakpoint provisional"
    reasons: List[str] = []
    last_status = statuses[last_i]
    prev_status = statuses[last_i - 1] if last_i >= 1 else ""
    flip_toward_failure = (prev_status != last_status) and is_failure_status(last_status)
    if flip_toward_failure:
        reasons.append("status_flip_toward_failure")

    if streak_len >= 1 and is_failure_status(last_status) and (last_i >= 1) and (not is_failure_status(prev_status)):
        reasons.append("failure_streak_began")

    # density spike rule: compare dn vs dp at end
    dn = window_density(last_i, WINDOW_N)
    dp = window_density(max(0, last_i - 1), WINDOW_N)
    if (dn - dp) >= SPIKE_DENSITY_DELTA and is_failure_status(last_status):
        reasons.append("fail_density_spike")

    # score threshold (secondary)
    SCORE_THRESHOLD = 0.60
    if mutation_score >= SCORE_THRESHOLD:
        reasons.append("mutation_score_threshold")

    breakpoint = len(reasons) > 0

    mutation = MutationScore(
        rule_version=rule_version,
        weights=weights,
        components=components,
        mutation_score=float(mutation_score),
        breakpoint=bool(breakpoint),
        breakpoint_reasons=reasons,
    )

    return latest_transitions, metrics, mutation


# =========================
# Evidence pack writer
# =========================

def write_evidence_pack(
    month: str,
    day_tag: str,
    updated_at_utc: str,
    metrics: EscalationMetrics,
    mutation: MutationScore,
    latest_tail: List[Dict[str, Any]],
) -> Optional[str]:
    """
    Writes incidents/evidence_snapshots/ESC_<YYYYMMDD>_<RULE>.md
    Only called when mutation.breakpoint is True.
    """
    os.makedirs(os.path.join("incidents", "evidence_snapshots"), exist_ok=True)
    rule = mutation.rule_version.replace("-", "")
    path = os.path.join("incidents", "evidence_snapshots", f"ESC_{day_tag}_{rule}.md")

    lines: List[str] = []
    lines.append(f"# Evidence Snapshot — {month} / {day_tag}")
    lines.append("")
    lines.append(f"- updated_at_utc: `{updated_at_utc}`")
    lines.append(f"- rule_version: `{mutation.rule_version}`")
    lines.append("")
    lines.append("## Escalation Metrics (latest)")
    lines.append("")
    lines.append(f"- window_n: `{metrics.window_n}`")
    lines.append(f"- fail_count_last_n: `{metrics.fail_count_last_n}`")
    lines.append(f"- fail_density: `{metrics.fail_density:.3f}`")
    lines.append(f"- burst_fail: `{metrics.burst_fail}` (k={metrics.burst_window_k}, b={metrics.burst_threshold_b})")
    lines.append(f"- recovery_speed_runs: `{metrics.recovery_speed_runs}`")
    lines.append(f"- flips_in_last_n: `{metrics.flips_in_last_n}`")
    lines.append(f"- flip_frequency_last_n: `{metrics.flip_frequency_last_n:.3f}`")
    lines.append("")
    lines.append("## Mutation")
    lines.append("")
    lines.append(f"- breakpoint: `{mutation.breakpoint}`")
    lines.append(f"- reasons: `{', '.join(mutation.breakpoint_reasons) if mutation.breakpoint_reasons else '(none)'}`")
    lines.append(f"- mutation_score: `{mutation.mutation_score:.3f}`")
    lines.append("")
    lines.append("### Components")
    for k in sorted(mutation.components.keys()):
        lines.append(f"- `{k}`: {mutation.components[k]:.6f}")
    lines.append("")
    lines.append("### Weights")
    for k in sorted(mutation.weights.keys()):
        lines.append(f"- `{k}`: {mutation.weights[k]:.6f}")
    lines.append("")
    lines.append("## Last N Conclusions (tail)")
    lines.append("")
    for e in latest_tail:
        ts = str(e.get("ts", ""))
        rid = str(e.get("run_id", ""))
        st = str((e.get("conclusion") or e.get("status") or "")).strip()
        commit = str(e.get("commit", "")).strip()
        lines.append(f"- `{ts}` run={rid} status={st} commit={commit}".strip())

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    return path


# =========================
# Index renderers
# =========================

def render_index_md(
    month: str,
    updated_at_utc: str,
    counts: Dict[str, int],
    latest_tail: List[Dict[str, Any]],
    transitions: List[Transition],
    raw_ledgers: List[str],
    issues: List[LedgerIssue],
    metrics: Optional[EscalationMetrics],
    mutation: Optional[MutationScore],
) -> str:
    lines: List[str] = []
    lines.append(f"# RTS Sessions — {month}")
    lines.append("")
    lines.append(f"- updated_at_utc: `{updated_at_utc}`")
    lines.append("")

    # Ledger integrity
    lines.append("## Ledger Integrity")
    lines.append("")
    if issues:
        err = sum(1 for x in issues if x.severity == "ERROR")
        warn = sum(1 for x in issues if x.severity == "WARN")
        lines.append(f"- status: **DEGRADED** (errors={err}, warnings={warn})")
        lines.append("")
        lines.append("### Issues (latest)")
        lines.append("")
        for it in issues[-12:]:
            lines.append(f"- `{it.file}:{it.line_no}` **{it.severity}** — {it.message}")
    else:
        lines.append("- status: **OK**")
    lines.append("")

    lines.append("## Counts")
    lines.append("")
    for k in sorted(counts.keys()):
        lines.append(f"- `{k}`: {counts[k]}")
    lines.append("")

    # Metrics block
    lines.append("## Metrics (latest)")
    lines.append("")
    if metrics and mutation:
        lines.append(f"- fail_count_last_n (n={metrics.window_n}): `{metrics.fail_count_last_n}`")
        lines.append(f"- fail_density: `{metrics.fail_density:.3f}`")
        lines.append(f"- burst_fail (k={metrics.burst_window_k}, b={metrics.burst_threshold_b}): `{metrics.burst_fail}`")
        lines.append(f"- recovery_speed_runs: `{metrics.recovery_speed_runs}`")
        lines.append(f"- flip_frequency_last_n: `{metrics.flip_frequency_last_n:.3f}` (flips={metrics.flips_in_last_n})")
        lines.append(f"- mutation_score: `{mutation.mutation_score:.3f}` (breakpoint={mutation.breakpoint})")
        if mutation.breakpoint_reasons:
            lines.append(f"- breakpoint_reasons: `{', '.join(mutation.breakpoint_reasons)}`")
    else:
        lines.append("- (none)")
    lines.append("")

    lines.append("## Latest (tail)")
    lines.append("")
    for e in latest_tail:
        ts = str(e.get("ts", ""))
        kind = str(e.get("kind", ""))
        wf = str(e.get("workflow", ""))
        rid = str(e.get("run_id", ""))
        st = str((e.get("conclusion") or e.get("status") or ""))
        commit = str(e.get("commit", ""))
        note = str(e.get("note", "")).strip()
        s = f"- `{ts}` `{kind}`"
        if wf:
            s += f" workflow={wf}"
        if rid:
            s += f" run={rid}"
        if st:
            s += f" status={st}"
        if commit:
            s += f" commit={commit}"
        if note:
            s += f" — {note}"
        lines.append(s)
    if not latest_tail:
        lines.append("- (none)")
    lines.append("")

    lines.append("## Transitions (latest)")
    lines.append("")
    if transitions:
        for t in transitions:
            s = f"- `{t.ts}` **{t.severity}** — {t.title}"
            if t.detail:
                s += f"  \n  {t.detail}"
            lines.append(s)
    else:
        lines.append("- (none)")
    lines.append("")

    lines.append("## Raw ledgers")
    lines.append("")
    for fn in raw_ledgers:
        lines.append(f"- `{fn}`")
    if not raw_ledgers:
        lines.append("- (none)")
    lines.append("")

    return "\n".join(lines)


# =========================
# Main
# =========================

def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python scripts/session_rollup.py YYYY-MM [YYYYMMDD]", file=sys.stderr)
        return 2

    month = sys.argv[1].strip()
    day_tag = sys.argv[2].strip() if len(sys.argv) >= 3 else None

    month_dir = os.path.join("sessions", month)
    os.makedirs(month_dir, exist_ok=True)

    events, raw_ledgers, ledger_paths = read_month_events(month)

    # Validate ledgers (hard guard)
    issues = validate_month_ledgers(month, ledger_paths)
    # If ledger is corrupted, still write index showing DEGRADED to avoid silent failure.
    # (Do not auto-fix; RTS reveals structure.)
    counts = count_by_kind(events)

    sentinel_only = [e for e in events if e.get("kind") == "sentinel.run"]
    latest_tail = tail(sentinel_only, n=8)

    transitions, metrics, mutation = compute_transitions_and_metrics(events, rule_version="2026-02")

    updated_at_utc = utc_now_iso()

    # Evidence pack when breakpoint
    evidence_path: Optional[str] = None
    if metrics and mutation and mutation.breakpoint:
        # determine day tag
        if day_tag is None:
            if sentinel_only:
                day_tag = yyyymmdd_from_ts(str(sentinel_only[-1].get("ts")))
            else:
                day_tag = datetime.now(timezone.utc).strftime("%Y%m%d")
        evidence_path = write_evidence_pack(
            month=month,
            day_tag=day_tag,
            updated_at_utc=updated_at_utc,
            metrics=metrics,
            mutation=mutation,
            latest_tail=tail(sentinel_only, n=12),
        )

    index_obj: Dict[str, Any] = {
        "month": month,
        "updated_at_utc": updated_at_utc,
        "counts": counts,
        "ledger_integrity": {
            "status": "DEGRADED" if issues else "OK",
            "issues": [asdict(x) for x in issues[-200:]],  # cap
        },
        "latest": [
            {
                "ts": e.get("ts"),
                "kind": e.get("kind"),
                "workflow": e.get("workflow"),
                "run_id": e.get("run_id"),
                "status": e.get("conclusion") or e.get("status"),
                "commit": e.get("commit"),
                "note": e.get("note"),
            }
            for e in latest_tail
        ],
        "transitions": [asdict(t) for t in transitions],
        "raw_ledgers": raw_ledgers,
        "metrics_latest": asdict(metrics) if metrics else None,
        "mutation_latest": asdict(mutation) if mutation else None,
        "evidence_latest": evidence_path,
    }

    index_json_path = os.path.join(month_dir, "index.json")
    index_md_path = os.path.join(month_dir, "index.md")

    with open(index_json_path, "w", encoding="utf-8") as f:
        json.dump(index_obj, f, ensure_ascii=False, indent=2)

    md = render_index_md(
        month=month,
        updated_at_utc=updated_at_utc,
        counts=counts,
        latest_tail=latest_tail,
        transitions=transitions,
        raw_ledgers=raw_ledgers,
        issues=issues,
        metrics=metrics,
        mutation=mutation,
    )
    with open(index_md_path, "w", encoding="utf-8") as f:
        f.write(md + "\n")

    print(f"Wrote: {index_json_path}")
    print(f"Wrote: {index_md_path}")
    if evidence_path:
        print(f"Wrote: {evidence_path}")
    if issues:
        # non-zero exit to make structural corruption visible
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
RTS Sessions rollup (FULL REPLACE) — START/END aware + evidence collision fix + index snapshots + evidence links
- Read sessions/<YYYY-MM>/session_*.jsonl (JSON Lines)
- Validate ledger (parseable JSON, required keys, ts parseable)
- Sort events by timestamp
- Compute:
    * Counts by kind
    * Latest tail (sentinel.run.end preferred; fallback sentinel.run)
    * Transitions (END stream):
        - status flip
        - failure streak start/end
        - failure density spike
        - dangling run (START exists but END missing)
    * Escalation metrics + Mutation scoring + breakpoint reasons
    * Evidence index: list evidence snapshots for the month, link in index.md
- Write:
    sessions/<YYYY-MM>/index.json
    sessions/<YYYY-MM>/index.md
    sessions/<YYYY-MM>/index_snapshot.json
    sessions/<YYYY-MM>/index_snapshot.md
    incidents/evidence_snapshots/ESC_<YYYYMMDD>_<RULE>_<HHMMSSZ>.md (collision-free)

Usage:
  python scripts/session_rollup.py 2026-02
  python scripts/session_rollup.py 2026-02 20260226
"""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from glob import glob
from typing import Any, Dict, List, Optional, Tuple


# =========================
# Time / parsing utilities
# =========================

def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def utc_now_iso() -> str:
    return utc_now().isoformat().replace("+00:00", "Z")


def parse_ts(ts: str) -> datetime:
    s = str(ts).strip()
    if s.endswith("Z"):
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    return datetime.fromisoformat(s)


def yyyymmdd_from_ts(ts: str) -> str:
    d = parse_ts(ts).astimezone(timezone.utc)
    return d.strftime("%Y%m%d")


def hhmmssz_from_ts(ts: str) -> str:
    d = parse_ts(ts).astimezone(timezone.utc)
    return d.strftime("%H%M%SZ")


def safe_load_json_line(line: str) -> Optional[Dict[str, Any]]:
    line = line.strip()
    if not line:
        return None
    try:
        obj = json.loads(line)
        return obj if isinstance(obj, dict) else None
    except Exception:
        return None


# =========================
# Validation / normalization
# =========================

REQUIRED_KEYS = ("ts", "kind")


def normalize_status(e: Dict[str, Any]) -> str:
    v = e.get("conclusion") or e.get("status") or ""
    return str(v).strip().lower()


def is_failure_status(status: str) -> bool:
    # default: everything except "success" is treated as failure
    s = str(status).lower()
    return s != "success"


@dataclass
class LedgerIssue:
    file: str
    line_no: int
    severity: str  # "WARN" or "ERROR"
    message: str


def validate_month_ledgers(jsonl_paths: List[str]) -> List[LedgerIssue]:
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
                for k in REQUIRED_KEYS:
                    if k not in obj:
                        issues.append(LedgerIssue(base, i, "ERROR", f"missing key: {k}"))
                try:
                    parse_ts(str(obj.get("ts", "")))
                except Exception:
                    issues.append(LedgerIssue(base, i, "ERROR", "unparseable ts"))
    return issues


def read_month_events(month: str) -> Tuple[List[Dict[str, Any]], List[str], List[str]]:
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
# START/END modeling
# =========================

END_KINDS = ("sentinel.run.end", "sentinel.run")   # end preferred; legacy supported
START_KIND = "sentinel.run.start"


def split_sentinel_stream(events: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[str]]:
    starts = [e for e in events if e.get("kind") == START_KIND and e.get("run_id")]
    ends = [e for e in events if e.get("kind") in END_KINDS and e.get("run_id")]

    start_ids = {str(e.get("run_id")) for e in starts}
    end_ids = {str(e.get("run_id")) for e in ends}

    dangling = sorted(list(start_ids - end_ids))
    return starts, ends, dangling


def end_stream_dedup_by_run_id(end_events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    best: Dict[str, Dict[str, Any]] = {}
    for e in end_events:
        rid = str(e.get("run_id"))
        if not rid:
            continue
        if rid not in best:
            best[rid] = e
            continue
        try:
            if parse_ts(str(e["ts"])) >= parse_ts(str(best[rid]["ts"])):
                best[rid] = e
        except Exception:
            pass
    out = list(best.values())
    out.sort(key=lambda x: parse_ts(str(x["ts"])))
    return out


# =========================
# Transitions + metrics + mutation
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
    dangling_runs: int


@dataclass
class MutationScore:
    rule_version: str
    weights: Dict[str, float]
    components: Dict[str, float]
    mutation_score: float
    breakpoint: bool
    breakpoint_reasons: List[str]


def compute_transitions_and_metrics(
    end_events: List[Dict[str, Any]],
    dangling_run_ids: List[str],
    rule_version: str = "2026-02",
) -> Tuple[List[Transition], Optional[EscalationMetrics], Optional[MutationScore]]:
    end_stream = end_stream_dedup_by_run_id(end_events)
    if not end_stream:
        if dangling_run_ids:
            t = Transition(
                ts=utc_now_iso(),
                kind="sentinel.run",
                severity="HIGH",
                title="dangling runs detected (start without end)",
                detail=f"dangling_run_ids={','.join(dangling_run_ids[:8])}" + (" ..." if len(dangling_run_ids) > 8 else ""),
            )
            metrics = EscalationMetrics(
                window_n=20, fail_count_last_n=0, fail_density=0.0,
                burst_window_k=5, burst_threshold_b=3, burst_fail=False,
                recovery_speed_runs=None, flip_frequency_last_n=0.0, flips_in_last_n=0,
                dangling_runs=len(dangling_run_ids),
            )
            mutation = MutationScore(
                rule_version=rule_version,
                weights={"w_dangling_runs": 1.0},
                components={"dangling_runs": float(len(dangling_run_ids))},
                mutation_score=1.0,
                breakpoint=True,
                breakpoint_reasons=["dangling_run_detected"],
            )
            return [t], metrics, mutation
        return [], None, None

    statuses = [normalize_status(e) for e in end_stream]
    times = [str(e["ts"]) for e in end_stream]

    WINDOW_N = 20
    BURST_K = 5
    BURST_B = 3
    SPIKE_DENSITY_DELTA = 0.20
    FLIP_WINDOW_N = 20

    fails = [1 if is_failure_status(s) else 0 for s in statuses]

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

    transitions: List[Transition] = []

    if dangling_run_ids:
        transitions.append(
            Transition(
                ts=times[-1],
                kind="sentinel.run",
                severity="HIGH",
                title="dangling runs detected (start without end)",
                detail=f"dangling_runs={len(dangling_run_ids)} ids={','.join(dangling_run_ids[:8])}" + (" ..." if len(dangling_run_ids) > 8 else ""),
            )
        )

    flips_idx: List[int] = []
    for i in range(1, len(end_stream)):
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
                    detail=mk_detail(end_stream[i]),
                    run_id=str(end_stream[i].get("run_id")) if end_stream[i].get("run_id") else None,
                    commit=str(end_stream[i].get("commit")) if end_stream[i].get("commit") else None,
                )
            )

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
                    detail=mk_detail(end_stream[i]),
                    run_id=str(end_stream[i].get("run_id")) if end_stream[i].get("run_id") else None,
                    commit=str(end_stream[i].get("commit")) if end_stream[i].get("commit") else None,
                )
            )
        if prev_fail and (not cur_fail):
            transitions.append(
                Transition(
                    ts=times[i],
                    kind="sentinel.run",
                    severity="MED",
                    title="failure streak ended (recovery)",
                    detail=mk_detail(end_stream[i]),
                    run_id=str(end_stream[i].get("run_id")) if end_stream[i].get("run_id") else None,
                    commit=str(end_stream[i].get("commit")) if end_stream[i].get("commit") else None,
                )
            )

    def window_density(end_i: int, n: int) -> float:
        start = max(0, end_i - n + 1)
        w = fails[start:end_i + 1]
        if not w:
            return 0.0
        return sum(w) / float(len(w))

    for i in range(len(end_stream)):
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
                    detail=f"fail_density_last_{WINDOW_N}={dn:.3f} (+{(dn-dp):.3f}) {mk_detail(end_stream[i])}".strip(),
                    run_id=str(end_stream[i].get("run_id")) if end_stream[i].get("run_id") else None,
                    commit=str(end_stream[i].get("commit")) if end_stream[i].get("commit") else None,
                )
            )

    transitions.sort(key=lambda t: parse_ts(t.ts))
    latest_transitions = transitions[-12:]

    last_i = len(end_stream) - 1
    n_eff = min(WINDOW_N, len(end_stream))
    last_window = fails[-n_eff:]
    fail_count_last_n = sum(last_window)
    fail_density = fail_count_last_n / float(n_eff) if n_eff else 0.0

    k_eff = min(BURST_K, len(end_stream))
    burst_window = fails[-k_eff:]
    burst_fail = sum(burst_window) >= BURST_B

    recovery_speed_runs: Optional[int] = None
    last_end: Optional[int] = None
    for i in range(1, len(end_stream)):
        if is_failure_status(statuses[i - 1]) and (not is_failure_status(statuses[i])):
            last_end = i
    if last_end is not None:
        recovery_speed_runs = 0

    fn_eff = min(FLIP_WINDOW_N, len(end_stream))
    flips_in_last_n = sum(1 for idx in flips_idx if idx >= (len(end_stream) - fn_eff))
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
        dangling_runs=int(len(dangling_run_ids)),
    )

    density_now = fail_density
    prev_end = last_i - n_eff
    density_prev = window_density(prev_end, WINDOW_N) if prev_end >= 0 else 0.0
    fail_density_delta = max(0.0, density_now - density_prev)

    streak_len = 0
    j = last_i
    while j >= 0 and is_failure_status(statuses[j]):
        streak_len += 1
        j -= 1
    STREAK_CAP = 10
    streak_norm = min(streak_len, STREAK_CAP) / float(STREAK_CAP)

    burst_spike = 1.0 if burst_fail else 0.0
    flip_freq = flip_frequency_last_n

    dangling_n = len(dangling_run_ids)
    DANGLING_CAP = 3
    dangling_norm = min(dangling_n, DANGLING_CAP) / float(DANGLING_CAP)

    weights = {
        "w1_fail_density_delta": 0.35,
        "w2_streak_length": 0.25,
        "w3_burst_spike": 0.15,
        "w4_flip_frequency": 0.10,
        "w5_dangling_runs": 0.15,
    }

    components = {
        "fail_density_delta": float(fail_density_delta),
        "streak_length": float(streak_norm),
        "burst_spike": float(burst_spike),
        "flip_frequency": float(flip_freq),
        "dangling_runs": float(dangling_norm),
    }

    mutation_score = (
        weights["w1_fail_density_delta"] * components["fail_density_delta"]
        + weights["w2_streak_length"] * components["streak_length"]
        + weights["w3_burst_spike"] * components["burst_spike"]
        + weights["w4_flip_frequency"] * components["flip_frequency"]
        + weights["w5_dangling_runs"] * components["dangling_runs"]
    )

    reasons: List[str] = []
    last_status = statuses[last_i]
    prev_status = statuses[last_i - 1] if last_i >= 1 else ""

    if (prev_status != last_status) and is_failure_status(last_status):
        reasons.append("status_flip_toward_failure")

    if streak_len >= 1 and is_failure_status(last_status) and (last_i >= 1) and (not is_failure_status(prev_status)):
        reasons.append("failure_streak_began")

    dn = window_density(last_i, WINDOW_N)
    dp = window_density(max(0, last_i - 1), WINDOW_N)
    if (dn - dp) >= SPIKE_DENSITY_DELTA and is_failure_status(last_status):
        reasons.append("fail_density_spike")

    if dangling_n > 0:
        reasons.append("dangling_run_detected")

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
# Evidence pack + evidence index (NEW)
# =========================

def evidence_month_prefix(month: str) -> str:
    # month "2026-02" -> "202602"
    return month.replace("-", "")


def list_evidence_for_month(month: str) -> List[Dict[str, Any]]:
    """
    Collect evidence snapshots for this month only.
    Filename format:
      ESC_<YYYYMMDD>_<RULE>_<HHMMSSZ>.md
    Returns list sorted by (day, time) ascending.
    """
    base = os.path.join("incidents", "evidence_snapshots")
    if not os.path.isdir(base):
        return []
    pref = evidence_month_prefix(month)
    paths = sorted(glob(os.path.join(base, f"ESC_{pref}[0-9][0-9]_*_*.md")))

    out: List[Dict[str, Any]] = []
    rx = re.compile(r"^ESC_(\d{8})_([0-9A-Za-z]+)_(\d{6}Z)\.md$")
    for p in paths:
        fn = os.path.basename(p)
        m = rx.match(fn)
        if not m:
            continue
        day, rule, t = m.group(1), m.group(2), m.group(3)
        out.append({
            "day": day,
            "time": t,
            "rule": rule,
            "file": fn,
            "path": p,
            "rel": os.path.join("..", "..", "incidents", "evidence_snapshots", fn),
        })
    out.sort(key=lambda x: (x["day"], x["time"]))
    return out


def write_evidence_pack(
    month: str,
    day_tag: str,
    updated_at_utc: str,
    metrics: EscalationMetrics,
    mutation: MutationScore,
    latest_tail: List[Dict[str, Any]],
    dangling_run_ids: List[str],
) -> Optional[str]:
    os.makedirs(os.path.join("incidents", "evidence_snapshots"), exist_ok=True)
    rule = mutation.rule_version.replace("-", "")

    # collision-free suffix
    try:
        time_tag = hhmmssz_from_ts(updated_at_utc)
    except Exception:
        time_tag = utc_now().strftime("%H%M%SZ")

    path = os.path.join("incidents", "evidence_snapshots", f"ESC_{day_tag}_{rule}_{time_tag}.md")

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
    lines.append(f"- dangling_runs: `{metrics.dangling_runs}`")
    lines.append("")
    if dangling_run_ids:
        lines.append("## Dangling Runs (START without END)")
        lines.append("")
        for rid in dangling_run_ids[:20]:
            lines.append(f"- `{rid}`")
        if len(dangling_run_ids) > 20:
            lines.append(f"- ... ({len(dangling_run_ids)} total)")
        lines.append("")

    lines.append("## Mutation")
    lines.append("")
    lines.append(f"- breakpoint: `{mutation.breakpoint}`")
    lines.append(f"- reasons: `{', '.join(mutation.breakpoint_reasons) if mutation.breakpoint_reasons else '(none)'}`")
    lines.append(f"- mutation_score: `{mutation.mutation_score:.3f}`")
    lines.append("")
    lines.append("## Last N END Events (tail)")
    lines.append("")
    for e in latest_tail:
        ts = str(e.get("ts", ""))
        rid = str(e.get("run_id", ""))
        st = str((e.get("conclusion") or e.get("status") or "")).strip()
        commit = str(e.get("commit", "")).strip()
        k = str(e.get("kind", "")).strip()
        lines.append(f"- `{ts}` `{k}` run={rid} status={st} commit={commit}".strip())

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return path


# =========================
# Index render (Evidence Links added)
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
    evidence_items: List[Dict[str, Any]],
    evidence_latest_file: Optional[str],
) -> str:
    lines: List[str] = []
    lines.append(f"# RTS Sessions — {month}")
    lines.append("")
    lines.append(f"- updated_at_utc: `{updated_at_utc}`")
    lines.append("")

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

    lines.append("## Metrics (latest)")
    lines.append("")
    if metrics and mutation:
        lines.append(f"- fail_count_last_n (n={metrics.window_n}): `{metrics.fail_count_last_n}`")
        lines.append(f"- fail_density: `{metrics.fail_density:.3f}`")
        lines.append(f"- burst_fail (k={metrics.burst_window_k}, b={metrics.burst_threshold_b}): `{metrics.burst_fail}`")
        lines.append(f"- recovery_speed_runs: `{metrics.recovery_speed_runs}`")
        lines.append(f"- flip_frequency_last_n: `{metrics.flip_frequency_last_n:.3f}` (flips={metrics.flips_in_last_n})")
        lines.append(f"- dangling_runs: `{metrics.dangling_runs}`")
        lines.append(f"- mutation_score: `{mutation.mutation_score:.3f}` (breakpoint={mutation.breakpoint})")
        if mutation.breakpoint_reasons:
            lines.append(f"- breakpoint_reasons: `{', '.join(mutation.breakpoint_reasons)}`")
    else:
        lines.append("- (none)")
    lines.append("")

    # NEW: Evidence section
    lines.append("## Evidence Snapshots")
    lines.append("")
    if evidence_latest_file:
        # link from sessions/<month>/index.md to incidents/...
        rel = os.path.join("..", "..", "incidents", "evidence_snapshots", evidence_latest_file)
        lines.append(f"- latest: [{evidence_latest_file}]({rel})")
    else:
        lines.append("- latest: (none)")
    lines.append("")
    if evidence_items:
        lines.append("### Recent (latest 12)")
        lines.append("")
        for it in evidence_items[-12:][::-1]:
            rel = it["rel"]
            fn = it["file"]
            lines.append(f"- `{it['day']}` `{it['time']}` rule=`{it['rule']}` — [{fn}]({rel})")
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
# Snapshot writers
# =========================

def write_index_snapshots(month_dir: str, index_obj: Dict[str, Any], index_md: str) -> Tuple[str, str]:
    snap_json = os.path.join(month_dir, "index_snapshot.json")
    snap_md = os.path.join(month_dir, "index_snapshot.md")

    with open(snap_json, "w", encoding="utf-8") as f:
        json.dump(index_obj, f, ensure_ascii=False, indent=2)
        f.write("\n")

    with open(snap_md, "w", encoding="utf-8") as f:
        f.write(index_md + "\n")

    return snap_json, snap_md


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

    issues = validate_month_ledgers(ledger_paths)
    counts = count_by_kind(events)

    _, ends, dangling_run_ids = split_sentinel_stream(events)

    end_stream = end_stream_dedup_by_run_id(ends)
    latest_tail = tail(end_stream, n=8)

    transitions, metrics, mutation = compute_transitions_and_metrics(
        end_events=ends,
        dangling_run_ids=dangling_run_ids,
        rule_version="2026-02",
    )

    updated_at_utc = utc_now_iso()

    evidence_path: Optional[str] = None
    evidence_latest_file: Optional[str] = None

    # If breakpoint, write evidence file (collision-free)
    if metrics and mutation and mutation.breakpoint:
        if day_tag is None:
            if latest_tail:
                day_tag = yyyymmdd_from_ts(str(latest_tail[-1].get("ts")))
            else:
                day_tag = utc_now().strftime("%Y%m%d")
        evidence_path = write_evidence_pack(
            month=month,
            day_tag=day_tag,
            updated_at_utc=updated_at_utc,
            metrics=metrics,
            mutation=mutation,
            latest_tail=tail(end_stream, n=12),
            dangling_run_ids=dangling_run_ids,
        )
        if evidence_path:
            evidence_latest_file = os.path.basename(evidence_path)

    # Collect evidence list for the month (and also find latest if exists)
    evidence_items = list_evidence_for_month(month)
    if not evidence_latest_file and evidence_items:
        evidence_latest_file = evidence_items[-1]["file"]

    index_obj: Dict[str, Any] = {
        "month": month,
        "updated_at_utc": updated_at_utc,
        "counts": counts,
        "ledger_integrity": {
            "status": "DEGRADED" if issues else "OK",
            "issues": [asdict(x) for x in issues[-200:]],
        },
        "sentinel": {
            "end_kinds": list(END_KINDS),
            "start_kind": START_KIND,
            "dangling_run_ids": dangling_run_ids[:200],
            "dangling_runs": len(dangling_run_ids),
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
        "evidence_latest": evidence_latest_file,
        "evidence_index": [
            {"day": it["day"], "time": it["time"], "rule": it["rule"], "file": it["file"], "rel": it["rel"]}
            for it in evidence_items[-200:]
        ],
    }

    index_json_path = os.path.join(month_dir, "index.json")
    index_md_path = os.path.join(month_dir, "index.md")

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
        evidence_items=evidence_items,
        evidence_latest_file=evidence_latest_file,
    )

    with open(index_json_path, "w", encoding="utf-8") as f:
        json.dump(index_obj, f, ensure_ascii=False, indent=2)
        f.write("\n")

    with open(index_md_path, "w", encoding="utf-8") as f:
        f.write(md + "\n")

    snap_json, snap_md = write_index_snapshots(month_dir, index_obj, md)

    print(f"Wrote: {index_json_path}")
    print(f"Wrote: {index_md_path}")
    print(f"Wrote: {snap_json}")
    print(f"Wrote: {snap_md}")
    if evidence_path:
        print(f"Wrote: {evidence_path}")

    if issues:
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

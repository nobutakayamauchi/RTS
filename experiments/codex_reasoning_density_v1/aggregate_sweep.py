#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def load_run(path: Path) -> dict:
    events = []
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        raw = raw.strip()
        if not raw:
            continue
        try:
            events.append(json.loads(raw))
        except json.JSONDecodeError:
            continue

    completed = [e for e in events if e.get("type") == "turn.completed" and isinstance(e.get("usage"), dict)]
    failed = [e for e in events if e.get("type") == "turn.failed"]
    if not completed:
        return {"status": "NO_USAGE", "event_count": len(events), "turn_failed_events": len(failed)}

    usage = completed[-1]["usage"]
    input_tokens = int(usage.get("input_tokens", 0) or 0)
    cached = int(usage.get("cached_input_tokens", 0) or 0)
    output = int(usage.get("output_tokens", 0) or 0)
    reasoning = int(usage.get("reasoning_output_tokens", 0) or 0)
    return {
        "status": "COMPLETED",
        "event_count": len(events),
        "input_tokens": input_tokens,
        "cached_input_tokens": cached,
        "uncached_input_tokens": max(0, input_tokens - cached),
        "output_tokens": output,
        "reasoning_output_tokens": reasoning,
        "cached_input_ratio": (cached / input_tokens) if input_tokens else None,
        "turn_failed_events": len(failed),
    }


def quality_check(path: Path) -> dict:
    if not path.exists():
        return {"status": "MISSING", "pass": False}
    text = path.read_text(encoding="utf-8", errors="replace")
    upper = text.upper()
    lower = text.lower()
    checks = {
        "has_required_headings": all(h in upper for h in ("STATE", "ADEQUACY", "NEXT", "EVIDENCE")),
        "states_completed": "COMPLETED" in upper,
        "states_adequate": "ADEQUATE" in upper,
        "preserves_residual_risk": ("zero" in lower and ("defect" in lower or "risk" in lower)) or "residual" in lower,
        "cites_current_pointer": "freezer/items/RTS-FRZ-000024/current.json" in text,
        "cites_resolution": "docs/implementation/frz000024_resolution.json" in text,
        "cites_k2_readme": "test_adequacy_gate/README.md" in text,
    }
    return {"status": "CHECKED", "pass": all(checks.values()), "checks": checks}


def reduction(base: dict, candidate: dict, key: str):
    a = base.get(key)
    b = candidate.get(key)
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)) or a == 0:
        return None
    return (a - b) / a


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", default="experiments/codex_reasoning_density_v1/results")
    args = parser.parse_args()
    root = Path(args.results_dir)

    files = {
        "cold": "cold",
        "full": "reuse",
        "thin": "reuse_thin",
        "minimal": "reuse_minimal",
        "restart": "reuse_restart",
    }
    runs = {}
    for label, stem in files.items():
        jsonl = root / f"{stem}.jsonl"
        runs[label] = load_run(jsonl) if jsonl.exists() else {"status": "MISSING"}
        final = root / f"{stem}.final.txt"
        runs[label]["quality"] = quality_check(final)
        meta = root / f"{stem}.meta.json"
        if meta.exists():
            try:
                runs[label]["meta"] = json.loads(meta.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                runs[label]["meta"] = {"parse_error": True}

    cold = runs["cold"]
    candidate_labels = ("full", "thin", "minimal", "restart")
    comparisons = {}
    for label in candidate_labels:
        candidate = runs[label]
        comparisons[label] = {
            "cold_to_candidate_input_reduction": reduction(cold, candidate, "input_tokens"),
            "cold_to_candidate_uncached_input_reduction": reduction(cold, candidate, "uncached_input_tokens"),
            "cold_to_candidate_reasoning_output_reduction": reduction(cold, candidate, "reasoning_output_tokens"),
            "candidate_total_below_cold": (
                isinstance(cold.get("input_tokens"), int)
                and isinstance(candidate.get("input_tokens"), int)
                and candidate["input_tokens"] < cold["input_tokens"]
            ),
            "candidate_uncached_below_cold": (
                isinstance(cold.get("uncached_input_tokens"), int)
                and isinstance(candidate.get("uncached_input_tokens"), int)
                and candidate["uncached_input_tokens"] < cold["uncached_input_tokens"]
            ),
            "quality_gate_pass": bool(candidate.get("quality", {}).get("pass")),
        }

    winners = [
        label for label in candidate_labels
        if comparisons[label]["candidate_total_below_cold"]
        and comparisons[label]["candidate_uncached_below_cold"]
        and comparisons[label]["quality_gate_pass"]
    ]

    report = {
        "schema": "codex-reuse-density-sweep/v2",
        "goal": "reduce total and uncached input below COLD without losing bounded decision quality",
        "runs": runs,
        "comparisons": comparisons,
        "strict_winners": winners,
        "interpretation": {
            "strict_win_requires": [
                "total input < COLD",
                "uncached input < COLD",
                "deterministic quality checklist passes",
            ],
            "quality_warning": "The deterministic checklist is a guardrail, not a semantic correctness proof. Review final answers before claiming success.",
            "baseline_warning": "COLD/FULL/THIN/MINIMAL may be reused from preceding exploratory runs; RESTART is fresh. Use a later fully rerun sweep for publication-grade comparison.",
            "restart_rule": "RESTART verifies listed source blobs without reading source contents; source expansion is allowed only on hash mismatch, contradiction, or task-relevant insufficiency.",
        },
    }
    out = root / "reuse_sweep.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

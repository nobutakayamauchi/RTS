#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def load_run(path: Path):
    events = []
    for raw in path.read_text(encoding="utf-8").splitlines():
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
        return {
            "file": str(path),
            "status": "NO_USAGE",
            "turn_failed_events": len(failed),
            "event_count": len(events),
        }

    # codex exec normally emits one terminal turn.completed event for one exec turn.
    # If multiple are present, use the last terminal usage snapshot rather than summing
    # potentially cumulative snapshots.
    usage = completed[-1]["usage"]
    input_tokens = int(usage.get("input_tokens", 0) or 0)
    cached_input_tokens = int(usage.get("cached_input_tokens", 0) or 0)
    cache_write_input_tokens = int(usage.get("cache_write_input_tokens", 0) or 0)
    output_tokens = int(usage.get("output_tokens", 0) or 0)
    reasoning_output_tokens = int(usage.get("reasoning_output_tokens", 0) or 0)
    uncached_input_tokens = max(0, input_tokens - cached_input_tokens)

    item_types = {}
    for event in events:
        if not event.get("type", "").startswith("item."):
            continue
        item = event.get("item") or {}
        item_type = item.get("type", "unknown")
        item_types[item_type] = item_types.get(item_type, 0) + 1

    return {
        "file": str(path),
        "status": "COMPLETED",
        "event_count": len(events),
        "input_tokens": input_tokens,
        "cached_input_tokens": cached_input_tokens,
        "cache_write_input_tokens": cache_write_input_tokens,
        "uncached_input_tokens": uncached_input_tokens,
        "output_tokens": output_tokens,
        "reasoning_output_tokens": reasoning_output_tokens,
        "cached_input_ratio": (cached_input_tokens / input_tokens) if input_tokens else None,
        "visible_item_types": item_types,
        "turn_failed_events": len(failed),
    }


def reduction(old, new, key):
    a = old.get(key)
    b = new.get(key)
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)) or a == 0:
        return None
    return (a - b) / a


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", default="experiments/codex_reasoning_density_v1/results")
    parser.add_argument("--reference-tokens", type=int, default=5_000_000)
    args = parser.parse_args()

    root = Path(args.results_dir)
    runs = {}
    for name in ("cold", "reuse", "next"):
        runs[name] = load_run(root / f"{name}.jsonl")
        meta_path = root / f"{name}.meta.json"
        if meta_path.exists():
            try:
                runs[name]["meta"] = json.loads(meta_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                runs[name]["meta"] = {"parse_error": True}

    cold = runs["cold"]
    reuse = runs["reuse"]
    nxt = runs["next"]

    comparisons = {
        "cold_to_reuse_input_reduction": reduction(cold, reuse, "input_tokens"),
        "cold_to_reuse_uncached_input_reduction": reduction(cold, reuse, "uncached_input_tokens"),
        "cold_to_reuse_output_reduction": reduction(cold, reuse, "output_tokens"),
        "cold_to_reuse_reasoning_output_reduction": reduction(cold, reuse, "reasoning_output_tokens"),
        "cold_to_next_input_reduction": reduction(cold, nxt, "input_tokens"),
        "cold_to_next_uncached_input_reduction": reduction(cold, nxt, "uncached_input_tokens"),
    }

    reference = args.reference_tokens
    reference_ratios = {}
    for name, row in runs.items():
        measured = row.get("input_tokens")
        reference_ratios[name] = (measured / reference) if reference and isinstance(measured, int) else None

    report = {
        "schema_version": "codex-reasoning-density-benchmark/v1",
        "measurement_warning": (
            "REFERENCE_TOKENS is an external comparison number only. Do not infer that it uses the same meter "
            "as codex exec provider-reported usage without independent provenance."
        ),
        "reference_tokens": reference,
        "runs": runs,
        "comparisons": comparisons,
        "reference_ratios_only": reference_ratios,
    }

    out = root / "summary.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

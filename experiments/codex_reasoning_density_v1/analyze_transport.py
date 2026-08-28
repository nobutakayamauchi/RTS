#!/usr/bin/env python3
"""Analyze transport overhead in Codex exec JSONL without reading prompt/response text."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


def load(path: Path) -> list[dict[str, Any]]:
    rows=[]
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            obj=json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            rows.append(obj)
    return rows


def summarize(path: Path) -> dict[str, Any]:
    events=load(path)
    event_types=Counter()
    item_types=Counter()
    command_like=0
    tool_like=0
    completed_usage=None
    for e in events:
        et=str(e.get("type") or "unknown")
        event_types[et]+=1
        item=e.get("item")
        if isinstance(item, dict):
            it=str(item.get("type") or "unknown")
            item_types[it]+=1
            low=it.lower()
            if any(x in low for x in ("command","tool","shell","exec")):
                tool_like+=1
            if any(x in low for x in ("command","shell","exec")):
                command_like+=1
        if et=="turn.completed" and isinstance(e.get("usage"), dict):
            completed_usage=e["usage"]
    usage=completed_usage or {}
    input_tokens=int(usage.get("input_tokens",0) or 0)
    cached=int(usage.get("cached_input_tokens",0) or 0)
    return {
        "file": str(path),
        "event_count": len(events),
        "event_types": dict(event_types),
        "item_types": dict(item_types),
        "tool_like_items": tool_like,
        "command_like_items": command_like,
        "input_tokens": input_tokens,
        "cached_input_tokens": cached,
        "uncached_input_tokens": max(0,input_tokens-cached),
        "output_tokens": int(usage.get("output_tokens",0) or 0),
        "reasoning_output_tokens": int(usage.get("reasoning_output_tokens",0) or 0),
    }


def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument("--results-dir", default="experiments/codex_reasoning_density_v1/results")
    p.add_argument("--names", nargs="+", default=["cold","reuse_restart","reuse_attested"])
    a=p.parse_args()
    root=Path(a.results_dir)
    runs={}
    for name in a.names:
        path=root/f"{name}.jsonl"
        runs[name]=summarize(path) if path.exists() else {"status":"MISSING"}
    report={"schema":"codex-transport-cost/v1","runs":runs}
    out=root/"transport_analysis.json"
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()

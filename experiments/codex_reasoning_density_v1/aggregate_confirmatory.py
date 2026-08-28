#!/usr/bin/env python3
"""Aggregate fresh paired COLD vs ATTESTED confirmatory benchmark runs."""
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Any


def load_events(path: Path) -> list[dict[str, Any]]:
    rows=[]
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            obj=json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            rows.append(obj)
    return rows


def usage_from(events: list[dict[str, Any]]) -> dict[str, int]:
    completed=[e for e in events if e.get("type")=="turn.completed" and isinstance(e.get("usage"),dict)]
    if completed:
        u=completed[-1]["usage"]
        return {k:int(u.get(k,0) or 0) for k in ("input_tokens","cached_input_tokens","output_tokens","reasoning_output_tokens")}
    snapshots=[]
    for e in events:
        p=e.get("payload")
        if not isinstance(p,dict) or p.get("type")!="token_count":
            continue
        info=p.get("info")
        if not isinstance(info,dict):
            continue
        total=info.get("total_token_usage")
        if isinstance(total,dict):
            snapshots.append(total)
    if snapshots:
        u=snapshots[-1]
        return {k:int(u.get(k,0) or 0) for k in ("input_tokens","cached_input_tokens","output_tokens","reasoning_output_tokens")}
    return {}


def quality(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"pass":False,"checks":{"file_exists":False}}
    text=path.read_text(encoding="utf-8",errors="replace")
    upper=text.upper(); lower=text.lower()
    checks={
        "headings": all(h in upper for h in ("STATE","ADEQUACY","NEXT","EVIDENCE")),
        "completed": "COMPLETED" in upper,
        "adequate": "ADEQUATE" in upper,
        "bounded_adequacy": ("CURRENT_DEFINED_K2_LANES_ONLY" in upper) or ("BOUNDED" in upper and "ADEQUATE" in upper),
        "residual_risk": ("ZERO" in upper and ("DEFECT" in upper or "RISK" in upper)) or "RESIDUAL" in upper,
        "current_pointer": "freezer/items/RTS-FRZ-000024/current.json" in text,
        "resolution": "docs/implementation/frz000024_resolution.json" in text,
        "k2_readme": "test_adequacy_gate/README.md" in text,
    }
    return {"pass":all(checks.values()),"checks":checks}


def transport(events: list[dict[str, Any]]) -> dict[str, Any]:
    item_types={}; tool_like=0; command_like=0
    for e in events:
        item=e.get("item")
        if not isinstance(item,dict):
            continue
        typ=str(item.get("type") or "unknown")
        item_types[typ]=item_types.get(typ,0)+1
        low=typ.lower()
        if any(x in low for x in ("command","tool","shell","exec")):
            tool_like+=1
        if any(x in low for x in ("command","shell","exec")):
            command_like+=1
    return {"event_count":len(events),"item_types":item_types,"tool_like_items":tool_like,"command_like_items":command_like}


def load_run(root: Path, stem: str) -> dict[str, Any]:
    events=load_events(root/f"{stem}.jsonl")
    u=usage_from(events)
    inp=u.get("input_tokens")
    cached=u.get("cached_input_tokens")
    row={
        "input_tokens":inp,
        "cached_input_tokens":cached,
        "uncached_input_tokens": max(0,inp-cached) if isinstance(inp,int) and isinstance(cached,int) else None,
        "output_tokens":u.get("output_tokens"),
        "reasoning_output_tokens":u.get("reasoning_output_tokens"),
        "quality":quality(root/f"{stem}.final.txt"),
        "transport":transport(events),
    }
    meta=root/f"{stem}.meta.json"
    if meta.exists():
        try: row["meta"]=json.loads(meta.read_text(encoding="utf-8"))
        except json.JSONDecodeError: row["meta"]={"parse_error":True}
    return row


def reduction(a: Any,b: Any) -> float | None:
    if not isinstance(a,(int,float)) or not isinstance(b,(int,float)) or a==0:
        return None
    return (a-b)/a


def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument("--results-dir",required=True)
    ap.add_argument("--pairs",type=int,default=3)
    ns=ap.parse_args()
    root=Path(ns.results_dir)
    pairs=[]
    total_reductions=[]; uncached_reductions=[]
    for i in range(1,ns.pairs+1):
        cold=load_run(root,f"pair{i}_cold")
        att=load_run(root,f"pair{i}_attested")
        same_head=cold.get("meta",{}).get("git_head")==att.get("meta",{}).get("git_head")
        same_model=cold.get("meta",{}).get("requested_model")==att.get("meta",{}).get("requested_model")
        exits_ok=cold.get("meta",{}).get("exit_code")==0 and att.get("meta",{}).get("exit_code")==0
        tr=reduction(cold.get("input_tokens"),att.get("input_tokens"))
        ur=reduction(cold.get("uncached_input_tokens"),att.get("uncached_input_tokens"))
        if tr is not None: total_reductions.append(tr)
        if ur is not None: uncached_reductions.append(ur)
        win=(
            same_head and same_model and exits_ok
            and cold["quality"]["pass"] and att["quality"]["pass"]
            and isinstance(cold.get("input_tokens"),int) and isinstance(att.get("input_tokens"),int)
            and att["input_tokens"] < cold["input_tokens"]
            and isinstance(cold.get("uncached_input_tokens"),int) and isinstance(att.get("uncached_input_tokens"),int)
            and att["uncached_input_tokens"] < cold["uncached_input_tokens"]
        )
        pairs.append({
            "pair":i,"cold":cold,"attested":att,
            "same_git_head":same_head,"same_model":same_model,"exit_codes_ok":exits_ok,
            "total_input_reduction":tr,"uncached_input_reduction":ur,"strict_pair_win":win,
        })
    median_total=statistics.median(total_reductions) if len(total_reductions)==ns.pairs else None
    median_uncached=statistics.median(uncached_reductions) if len(uncached_reductions)==ns.pairs else None
    all_pairs_win=len(pairs)==ns.pairs and all(p["strict_pair_win"] for p in pairs)
    confirmed=all_pairs_win and isinstance(median_total,float) and median_total>0 and isinstance(median_uncached,float) and median_uncached>0
    report={
        "schema":"codex-attested-confirmatory/v1",
        "pair_count":ns.pairs,
        "pairs":pairs,
        "median_total_input_reduction":median_total,
        "median_uncached_input_reduction":median_uncached,
        "strict_pair_wins":sum(1 for p in pairs if p["strict_pair_win"]),
        "result":"CONFIRMED_STRICT_WIN" if confirmed else "NOT_CONFIRMED",
        "confirmation_rule":"Every fresh pair must use the same model/head, exit cleanly, pass bounded quality checks, and have ATTESTED below COLD on both total and uncached input; medians must also improve.",
        "warning":"This is task-specific empirical evidence, not a universal Codex token-reduction guarantee. Deterministic quality checks remain guardrails, not semantic proof.",
    }
    (root/"confirmatory_summary.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()

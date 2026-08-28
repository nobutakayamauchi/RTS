#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Any


def load_events(path: Path) -> list[dict[str, Any]]:
    rows=[]
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try: obj=json.loads(raw)
        except json.JSONDecodeError: continue
        if isinstance(obj,dict): rows.append(obj)
    return rows


def usage(events: list[dict[str, Any]]) -> dict[str,int]:
    done=[e for e in events if e.get("type")=="turn.completed" and isinstance(e.get("usage"),dict)]
    if not done: return {}
    u=done[-1]["usage"]
    return {k:int(u.get(k,0) or 0) for k in ("input_tokens","cached_input_tokens","output_tokens","reasoning_output_tokens")}


def quality(path: Path) -> dict[str,Any]:
    if not path.exists(): return {"semantic_pass":False,"provenance_complete":False,"checks":{"file_exists":False}}
    text=path.read_text(encoding="utf-8",errors="replace")
    up=text.upper(); low=text.lower()
    semantic={
        "headings": all(h in up for h in ("STATE","S3","CLAIM","NEXT","EVIDENCE")),
        "completed": "COMPLETED" in up,
        "s3_external_contract": "S3" in up and ("EXECUTION-CONTRACT" in up or "EXECUTION CONTRACT" in up) and ("TOPOLOGY" in up or "EXTERNAL" in up or "OBSERVABLE" in up),
        "no_hidden_architecture_proof": ("HIDDEN" in up or "NEURAL" in up or "ARCHITECTURE" in up) and ("NONE" in up or "NOT" in up or "NO " in up),
        "docs_claim_unverified": ("DOCS" in up or "DOCUMENT" in up) and ("UNVERIFIED" in up or ("NOT" in up and "OBSERVED" in up)),
        "non_authorizing": ("NO EXECUTION" in up or "AUTHORITY" in up or "NON-AUTHORIZ" in up or "DOES NOT" in up) and ("PROFILE" in up or "RUNTIME" in up or "PROMOTION" in up),
        "bounded_next": "BOUNDED" in up and ("PROBE" in up or "REPROFILE" in up or "REPROFIL" in up),
    }
    prov={
        "current_pointer":"freezer/items/RTS-FRZ-000018/current.json" in text,
        "v005_pointer":"freezer/items/RTS-FRZ-000018/v005.json" in text,
        "meteor_pointer":"thin-rts/ultimate-loop/METEOR_RESULT_FRZ_000018_2026-08-27.md" in text,
    }
    return {"semantic_pass":all(semantic.values()),"provenance_complete":all(prov.values()),"checks":semantic,"provenance_checks":prov}


def transport(events: list[dict[str,Any]]) -> dict[str,Any]:
    item_types={}; tool_like=0; command_like=0
    for e in events:
        item=e.get("item")
        if not isinstance(item,dict): continue
        typ=str(item.get("type") or "unknown")
        item_types[typ]=item_types.get(typ,0)+1
        low=typ.lower()
        if any(x in low for x in ("command","tool","shell","exec","mcp")): tool_like+=1
        if any(x in low for x in ("command","shell","exec")): command_like+=1
    return {"event_count":len(events),"item_types":item_types,"tool_like_items":tool_like,"command_like_items":command_like}


def load_run(root:Path,stem:str)->dict[str,Any]:
    ev=load_events(root/f"{stem}.jsonl")
    u=usage(ev); inp=u.get("input_tokens"); cached=u.get("cached_input_tokens")
    row={"input_tokens":inp,"cached_input_tokens":cached,"uncached_input_tokens":max(0,inp-cached) if isinstance(inp,int) and isinstance(cached,int) else None,"output_tokens":u.get("output_tokens"),"reasoning_output_tokens":u.get("reasoning_output_tokens"),"quality":quality(root/f"{stem}.final.txt"),"transport":transport(ev)}
    mp=root/f"{stem}.meta.json"
    if mp.exists(): row["meta"]=json.loads(mp.read_text(encoding="utf-8"))
    return row


def reduction(a:Any,b:Any):
    if not isinstance(a,(int,float)) or not isinstance(b,(int,float)) or a==0:return None
    return (a-b)/a


def main()->None:
    ap=argparse.ArgumentParser(); ap.add_argument("--results-dir",required=True); ap.add_argument("--pairs",type=int,default=3); ns=ap.parse_args(); root=Path(ns.results_dir)
    pairs=[]; trs=[]; urs=[]; wrs=[]; relations=[]
    for i in range(1,ns.pairs+1):
        cold=load_run(root,f"pair{i}_cold"); att=load_run(root,f"pair{i}_attested")
        same_head=cold.get("meta",{}).get("git_head")==att.get("meta",{}).get("git_head")
        same_model=cold.get("meta",{}).get("requested_model")==att.get("meta",{}).get("requested_model")
        exits=cold.get("meta",{}).get("exit_code")==0 and att.get("meta",{}).get("exit_code")==0
        csem=cold["quality"]["semantic_pass"]; asem=att["quality"]["semantic_pass"]
        relation="PRESERVED" if csem and asem else "IMPROVED" if (not csem and asem) else "REGRESSED" if (csem and not asem) else "BOTH_FAIL"
        tr=reduction(cold.get("input_tokens"),att.get("input_tokens")); ur=reduction(cold.get("uncached_input_tokens"),att.get("uncached_input_tokens")); wr=reduction(cold.get("meta",{}).get("wall_seconds"),att.get("meta",{}).get("wall_seconds"))
        if tr is not None: trs.append(tr)
        if ur is not None: urs.append(ur)
        if wr is not None: wrs.append(wr)
        relations.append(relation)
        win=(same_head and same_model and exits and asem and relation!="REGRESSED" and isinstance(tr,float) and tr>0 and isinstance(ur,float) and ur>0)
        pairs.append({"pair":i,"cold":cold,"attested":att,"quality_relation":relation,"same_git_head":same_head,"same_model":same_model,"exit_codes_ok":exits,"total_input_reduction":tr,"uncached_input_reduction":ur,"wall_time_reduction":wr,"strict_pair_win":win})
    mt=statistics.median(trs) if len(trs)==ns.pairs else None; mu=statistics.median(urs) if len(urs)==ns.pairs else None; mw=statistics.median(wrs) if len(wrs)==ns.pairs else None
    wins=sum(1 for p in pairs if p["strict_pair_win"]); confirmed=wins==ns.pairs and isinstance(mt,float) and mt>0 and isinstance(mu,float) and mu>0
    report={"schema":"codex-heldout-frz000018/v1","heldout_item":"RTS-FRZ-000018","pair_count":ns.pairs,"pairs":pairs,"median_total_input_reduction":mt,"median_uncached_input_reduction":mu,"median_wall_time_reduction":mw,"strict_pair_wins":wins,"quality_relations":{k:relations.count(k) for k in ("PRESERVED","IMPROVED","REGRESSED","BOTH_FAIL")},"result":"HELDOUT_CONFIRMED_STRICT_WIN" if confirmed else "HELDOUT_NOT_CONFIRMED","warning":"Task-specific held-out evidence. Exact provenance completeness is reported separately from semantic quality."}
    (root/"heldout_summary.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=="__main__": main()

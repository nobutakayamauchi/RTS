#!/usr/bin/env python3
"""Build a fail-closed, read-only attestation for the compact restart surface."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def git(*args: str) -> str:
    p=subprocess.run(["git",*args],check=True,capture_output=True,text=True)
    return p.stdout.strip()


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--surface", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ns=ap.parse_args()
    surface_path=ns.surface
    raw=surface_path.read_bytes()
    surface=json.loads(raw)
    checks=[]
    all_match=True
    for src in surface.get("sources",[]):
        path=src["path"]
        expected=src["git_blob_sha1"]
        actual=git("hash-object",path)
        match=(actual==expected)
        all_match=all_match and match
        checks.append({"path":path,"expected_blob":expected,"actual_blob":actual,"match":match})
    out={
        "schema":"rts-runner-attestation/v1",
        "generated_at":datetime.now(timezone.utc).isoformat(),
        "git_head":git("rev-parse","HEAD"),
        "surface_path":str(surface_path),
        "surface_sha256":hashlib.sha256(raw).hexdigest(),
        "verified":all_match and bool(checks),
        "verified_source_count":sum(1 for x in checks if x["match"]),
        "source_count":len(checks),
        "state":surface.get("state",{}),
        "authority":surface.get("authority","NONE"),
        "checks":checks,
        "rule":"If verified=true, source blobs matched immediately before model invocation. Expand source contents only if the task cannot be answered from this attestation or another contradiction is present.",
    }
    ns.output.parent.mkdir(parents=True,exist_ok=True)
    ns.output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(out,ensure_ascii=False,indent=2))
    return 0 if out["verified"] else 3

if __name__=="__main__":
    raise SystemExit(main())

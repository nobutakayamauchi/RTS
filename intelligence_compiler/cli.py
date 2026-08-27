from __future__ import annotations
import argparse,json
from .core import load_manifest,verify_job

def main(argv=None):
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest='cmd',required=True)
    v=sub.add_parser('verify'); v.add_argument('--store',default='intelligence/compiler_sample'); v.add_argument('--job')
    n=sub.add_parser('next'); n.add_argument('--store',default='intelligence/compiler_sample'); n.add_argument('--job',required=True)
    a=p.parse_args(argv)
    if a.cmd=='verify':
        job=a.job
        if not job:
            from pathlib import Path
            manifests=list(Path(a.store).glob('jobs/*/manifest.json'))
            if len(manifests)!=1: raise SystemExit('specify --job')
            job=manifests[0].parent.name
        out=verify_job(a.store,job)
    else:
        m=load_manifest(a.store,a.job); c=next((x for x in m['chunks'] if x['status']=='PENDING'),None); out={'next_chunk_id':None if c is None else c['chunk_id'],'learning_status':m['learning_status'],'application_authority':'NONE','promotion_authority':'NONE'}
    print(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True))

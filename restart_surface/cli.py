from __future__ import annotations
import argparse, json
from pathlib import Path
from .core import validate_surface, decide_restart
def main(argv=None):
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest='cmd',required=True)
    v=sub.add_parser('verify'); v.add_argument('--surface',default='restart/restart_surface.json')
    d=sub.add_parser('decide'); d.add_argument('--surface',default='restart/restart_surface.json'); d.add_argument('--request',required=True)
    a=p.parse_args(argv)
    s=json.loads(Path(a.surface).read_text())
    if a.cmd=='verify': out=validate_surface(Path('.'),s)
    else: out=decide_restart(s,json.loads(Path(a.request).read_text()))
    print(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True))

import argparse,json
from pathlib import Path
from .core import compute_report,validate_report

def main(argv=None):
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest='cmd',required=True)
    c=sub.add_parser('compute'); c.add_argument('--events',default='metrics/reuse_events.json'); c.add_argument('--output')
    v=sub.add_parser('verify'); v.add_argument('--report',default='metrics/reuse_report.json')
    a=p.parse_args(argv)
    if a.cmd=='compute':
        r=compute_report(json.loads(Path(a.events).read_text()));
        if a.output: Path(a.output).write_text(json.dumps(r,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
        print(json.dumps(r,ensure_ascii=False,indent=2,sort_keys=True))
    else:
        print(json.dumps(validate_report(json.loads(Path(a.report).read_text())),indent=2,sort_keys=True))

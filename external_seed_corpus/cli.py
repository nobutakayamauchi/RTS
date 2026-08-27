import argparse
import json
from .core import load_registry, match_candidates


def main(argv=None):
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='cmd', required=True)
    v = sub.add_parser('verify')
    v.add_argument('--registry', default='external_seeds/registry.json')
    m = sub.add_parser('match')
    m.add_argument('--registry', default='external_seeds/registry.json')
    m.add_argument('--tag', action='append', required=True)
    m.add_argument('--limit', type=int, default=2)
    a = p.parse_args(argv)
    registry = load_registry(a.registry)
    if a.cmd == 'verify':
        result = {'valid': True, 'seed_count': len(registry['seeds']), 'authority': registry['authority']}
    else:
        result = match_candidates(registry, a.tag, a.limit)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))

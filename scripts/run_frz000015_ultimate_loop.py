from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

ROOT = Path('.')
ITEM = 'RTS-FRZ-000015'
BRANCH = 'feature/frz-000015-external-transition-pattern-seed-corpus-v1'


def run(*args: str, check: bool = True):
    print('+', ' '.join(args), flush=True)
    return subprocess.run(args, text=True, check=check)


def write(path: str, text: str):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding='utf-8')


def write_json(path: str, value):
    write(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + '\n')


def current(item_id: str):
    pointer = json.loads((ROOT / 'freezer/items' / item_id / 'current.json').read_text())
    return json.loads((ROOT / pointer['path']).read_text())


def assert_start():
    for item_id in ('RTS-FRZ-000011', 'RTS-FRZ-000012', 'RTS-FRZ-000013', 'RTS-FRZ-000014'):
        assert current(item_id)['status'] == 'COMPLETED', current(item_id)
    e = current(ITEM)
    assert e['version'] == 1 and e['status'] == 'FROZEN' and e['build_authority'] == 'NOT_APPROVED', e
    active = []
    for p in (ROOT / 'freezer/items').glob('RTS-FRZ-*/current.json'):
        x = current(p.parent.name)
        if x['status'] == 'IN_PROGRESS':
            active.append(x['item_id'])
    assert active == [], active
    run('python', '-m', 'freezer.cli', 'verify')
    run('python', '-m', 'freezer.build_assessment', 'verify')


def governance_inputs():
    base = 'docs/implementation/frz000015_inputs'
    assessment = {
        'assessor': 'RTS governed build assessment — Child E external transition seed corpus',
        'rationale': 'Child E is a bounded repository-local registry and validator for external public repair/design patterns. It stores only provenance-rich non-Canonical seeds, requires applicability/counterconditions/license posture, reuses A lifecycle/non-authority boundaries and D claim-boundary conventions, and introduces no provider/network/execution surface.',
        'expected_effect': {
            'impact': 4,
            'strategic_fit': 5,
            'revenue_leverage': 2,
            'risk_reduction': 5,
            'recurrence': 4,
            'confidence': 5,
        },
        'implementation': {
            'from_scratch_hours': 7,
            'integration_hours': 2,
            'validation_hours': 3,
            'unknown_buffer_hours': 1,
        },
        'github_scan': {
            'performed': True,
            'repositories': ['nobutakayamauchi/RTS', 'openclaw/openclaw', 'shin4141/decision-os-v13-loopkit'],
            'queries': ['external seed provenance validation', 'OpenClaw embedding item-limit repair', 'lane recall weight limits'],
            'assets': [
                {
                    'repository': 'nobutakayamauchi/RTS',
                    'path': 'selective_recall/',
                    'ref': 'a284dc7a0534bafdf43cfe61fe3daac393718033',
                    'kind': 'code',
                    'reuse_mode': 'REFERENCE',
                    'license_status': 'OWNED',
                    'estimated_hours_saved': 2,
                    'notes': 'Reuse non-authority, lifecycle and freshness concepts; do not create a second memory store.',
                },
                {
                    'repository': 'nobutakayamauchi/RTS',
                    'path': 'reuse_metrics/',
                    'ref': 'a284dc7a0534bafdf43cfe61fe3daac393718033',
                    'kind': 'code',
                    'reuse_mode': 'REFERENCE',
                    'license_status': 'OWNED',
                    'estimated_hours_saved': 1,
                    'notes': 'Reuse exact claim-boundary and non-authority validation patterns.',
                },
                {
                    'repository': 'openclaw/openclaw',
                    'path': 'pull/125722 + pull/129927',
                    'ref': '08fa41c1606a4c201462d76f43184e6920a0cef7 / 657026cab35f62e6b9a68da0f7fad3666874c28d',
                    'kind': 'public_pr_evidence',
                    'reuse_mode': 'REFERENCE_ONLY',
                    'license_status': 'MIT_VERIFIED',
                    'estimated_hours_saved': 1,
                    'notes': 'Reference observed failure/repair/counterconditions only; no upstream code copied.',
                },
                {
                    'repository': 'shin4141/decision-os-v13-loopkit',
                    'path': 'field_notes/050_lane_recall_failure_and_weight_limits.md',
                    'ref': 'fe88f90430bacbb8f5aaf3ac5439e0580c04abd6',
                    'kind': 'public_design_note',
                    'reuse_mode': 'REFERENCE_ONLY',
                    'license_status': 'MIT_VERIFIED',
                    'estimated_hours_saved': 1,
                    'notes': 'Reference negative recall boundaries and non-authorization concept; no upstream code copied.',
                },
            ],
            'gaps': [
                'No current RTS schema stores external failure patterns with exact provenance, counterconditions and license posture while structurally forbidding Canonical state.',
                'No current read-only matcher exposes external seeds without granting execution/promotion/canon authority.',
            ],
        },
        'risks': [
            'Merged external repair may be mistaken for RTS Canon.',
            'Repository-specific evidence may be generalized beyond its source conditions.',
            'Missing counterconditions may create unsafe recall.',
            'License/reuse posture may drift if provenance is incomplete.',
            'Seed retrieval may be misread as permission to act.',
        ],
    }
    preflight = {
        'outcome': 'PASS',
        'assessor': 'RTS implementation preflight — Child E external transition seed corpus',
        'rationale': 'Repository-local JSON seed registry + deterministic validator + read-only matcher only. Exact source refs, applicability, counterconditions, evidence class, license/reuse status and RTS validation status are mandatory. CANONICAL is not a valid seed state, and all authority fields remain NONE.',
        'affected_boundaries': [
            'new external_seed_corpus package',
            'external_seeds/registry.json sample',
            'focused seed and destructive tests',
            'RTS-FRZ-000015 lifecycle records',
        ],
        'existing_assumptions': [
            'A/B/C/D are COMPLETED.',
            'External source success is evidence, not RTS authority.',
            'No upstream source code is copied; v1 is REFERENCE_ONLY.',
            'Internal validation is a separate future evidence step from external merge status.',
        ],
        'data_migration': {'required': False, 'notes': 'No existing memory, Canon, FREEZER history or external repository is mutated.'},
        'external_interfaces': ['repository-local Python API/CLI only', 'no network/provider/deployment/write-back surface'],
        'approval_changes': [
            'execution_authority=NONE',
            'promotion_authority=NONE',
            'canon_authority=NONE',
            'only RTS-FRZ-000015 may enter WIP',
        ],
        'public_documents': ['external_seed_corpus/README.md', 'external_seeds/SOURCES.md', 'thin-rts/ultimate-loop/METEOR_RESULT_FRZ_000015_2026-08-27.md'],
        'regression_tests': [
            'exact provenance mandatory',
            'counterconditions mandatory',
            'CANONICAL rejected',
            'authority escalation rejected',
            'merged source does not auto-promote',
            'license/reuse posture mandatory',
            'read-only matching',
            'A/B/C/D and FREEZER regressions',
        ],
        'hidden_dependencies': ['stable external-seed schema', 'FREEZER WIP=1', 'A lifecycle vocabulary', 'Human Review promotion boundary'],
        'rollback_boundary': 'Revert Child E package/registry/tests/docs/lifecycle only; preserve A/B/C/D and all external repositories.',
        'completion_conditions': [
            'External seeds cannot enter CANONICAL state.',
            'Every accepted seed carries exact provenance, applicability, counterconditions and license/reuse posture.',
            'External merge status cannot grant RTS validation or authority.',
            'Matcher remains read-only and non-authorizing.',
            'Focused and A/B/C/D/FREEZER regressions pass.',
            'E reaches COMPLETED and WIP is clear.',
        ],
        'decomposition': {'required': False, 'child_candidates': []},
        'risks': [
            'A useful source can still be stale or non-transferable.',
            'External evidence class can be overstated without counterconditions.',
            'Reference-only reuse must remain distinct from copied/adapted code.',
        ],
    }
    write_json(f'{base}/build_assessment_input.json', assessment)
    write_json(f'{base}/preflight_input.json', preflight)
    write_json(f'{base}/approve_selected.json', {'build_authority': 'APPROVED', 'status': 'SELECTED'})
    write_json(f'{base}/start_in_progress.json', {'status': 'IN_PROGRESS'})
    write('docs/implementation/FRZ_000015_EXTERNAL_TRANSITION_PATTERN_SEED_CORPUS_V1_TASK.md', '''# FRZ-000015 — External Transition Pattern Seed Corpus v1\n\nExternal public repair/design knowledge enters RTS only as provenance-rich, non-Canonical `REFERENCE_ONLY` seeds. External merge status is evidence, never Canon authority.\n''')


def govern():
    b = 'docs/implementation/frz000015_inputs'
    run('python', '-m', 'freezer.build_assessment', 'create', ITEM, '--input', f'{b}/build_assessment_input.json')
    gate = json.loads(subprocess.check_output(['python', '-m', 'freezer.build_assessment', 'gate', ITEM], text=True))
    assert gate['assessment_state'] == 'CURRENT', gate
    if gate['recommendation'] != 'BUILD_NOW':
        raise RuntimeError('FREEZER_GATE_NOT_BUILD_NOW:' + json.dumps(gate, sort_keys=True))
    assert gate['selection_ready'] is False, gate
    run('python', '-m', 'freezer.preflight', 'create', ITEM, '--input', f'{b}/preflight_input.json')
    run('python', '-m', 'freezer.cli', 'revise', ITEM, '--input', f'{b}/approve_selected.json')
    gate = json.loads(subprocess.check_output(['python', '-m', 'freezer.build_assessment', 'gate', ITEM], text=True))
    assert gate['preflight_state'] == 'PASS' and gate['recommendation'] == 'BUILD_NOW' and gate['selection_ready'] is True, gate
    run('python', '-m', 'freezer.cli', 'revise', ITEM, '--input', f'{b}/start_in_progress.json')
    run('python', '-m', 'freezer.cli', 'reindex')
    run('python', '-m', 'freezer.build_assessment', 'reindex')
    run('python', '-m', 'freezer.cli', 'verify')
    run('python', '-m', 'freezer.build_assessment', 'verify')
    active = [p.parent.name for p in (ROOT / 'freezer/items').glob('RTS-FRZ-*/current.json') if current(p.parent.name)['status'] == 'IN_PROGRESS']
    assert active == [ITEM], active


def initial_death():
    write('external_seed_corpus/__init__.py', 'from .core import validate_seed\n')
    write('external_seed_corpus/core.py', '''def validate_seed(seed):\n    return {"valid": True, "state": seed.get("state", "CANONICAL")}\n''')
    write('tests/_frz000015_initial_death.py', '''import unittest\nfrom external_seed_corpus import validate_seed\n\nclass InitialDeath(unittest.TestCase):\n    def test_canonical_or_unbounded_external_seed_must_die(self):\n        seed={"seed_id":"bad","state":"CANONICAL","source_refs":[],"counterconditions":[]}\n        with self.assertRaises(Exception):\n            validate_seed(seed)\n''')
    cp = run('python', '-m', 'unittest', 'tests._frz000015_initial_death', '-v', check=False)
    if cp.returncode == 0:
        raise RuntimeError('initial E candidate unexpectedly survived')
    Path('tests/_frz000015_initial_death.py').unlink()


def survivor():
    core = r'''from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ALLOWED_STATES = {'RAW', 'VERIFICATION_PENDING', 'INTERNALLY_VALIDATED', 'REJECTED', 'ARCHIVED'}
EVIDENCE_CLASSES = {'UPSTREAM_MERGED_REPAIR', 'UPSTREAM_UNMERGED_REPAIR', 'UPSTREAM_DESIGN_NOTE', 'PUBLIC_INCIDENT_EVIDENCE'}
RTS_VALIDATION_STATES = {'NOT_RUN', 'VERIFICATION_PENDING', 'INTERNALLY_VALIDATED', 'REJECTED'}
REUSE_MODES = {'REFERENCE_ONLY'}
AUTHORITY_NONE = {'execution': 'NONE', 'promotion': 'NONE', 'canon': 'NONE'}

class SeedValidationError(ValueError):
    pass


def _nonempty_strings(value: Any, name: str) -> list[str]:
    if not isinstance(value, list) or not value or not all(isinstance(x, str) and x.strip() for x in value):
        raise SeedValidationError(f'{name} must be a non-empty string list')
    return value


def _validate_source_ref(source: dict[str, Any]) -> None:
    required = {'repository', 'kind', 'ref', 'url', 'merged'}
    if set(source) != required:
        raise SeedValidationError(f'source ref keys must be exact: {sorted(required)}')
    repo = source['repository']
    ref = source['ref']
    url = source['url']
    if not isinstance(repo, str) or '/' not in repo:
        raise SeedValidationError('exact repository required')
    if not isinstance(ref, str) or not ref.strip():
        raise SeedValidationError('exact ref required')
    if source['kind'] not in {'pull_request', 'commit_file', 'issue', 'release'}:
        raise SeedValidationError('unsupported source kind')
    if not isinstance(url, str) or not url.startswith(f'https://github.com/{repo}/'):
        raise SeedValidationError('source url must match repository')
    if not isinstance(source['merged'], bool):
        raise SeedValidationError('merged must be boolean evidence only')


def validate_seed(seed: dict[str, Any]) -> dict[str, Any]:
    required = {
        'seed_id', 'pattern_title', 'state', 'source_refs', 'observed_failure_boundary',
        'repair_principle', 'evidence_class', 'applicability_conditions', 'counterconditions',
        'applicability_tags', 'license', 'reuse_mode', 'rts_validation', 'authority'
    }
    if set(seed) != required:
        raise SeedValidationError(f'seed keys must be exact: {sorted(required)}')
    if not isinstance(seed['seed_id'], str) or not seed['seed_id'].strip():
        raise SeedValidationError('seed_id required')
    if not isinstance(seed['pattern_title'], str) or not seed['pattern_title'].strip():
        raise SeedValidationError('pattern_title required')
    if seed['state'] not in ALLOWED_STATES:
        raise SeedValidationError('external seed state cannot be CANONICAL or unknown')
    if not isinstance(seed['source_refs'], list) or not seed['source_refs']:
        raise SeedValidationError('at least one exact source ref required')
    for source in seed['source_refs']:
        if not isinstance(source, dict):
            raise SeedValidationError('source ref must be object')
        _validate_source_ref(source)
    if not isinstance(seed['observed_failure_boundary'], str) or not seed['observed_failure_boundary'].strip():
        raise SeedValidationError('observed failure boundary required')
    if not isinstance(seed['repair_principle'], str) or not seed['repair_principle'].strip():
        raise SeedValidationError('repair principle required')
    if seed['evidence_class'] not in EVIDENCE_CLASSES:
        raise SeedValidationError('unsupported evidence class')
    _nonempty_strings(seed['applicability_conditions'], 'applicability_conditions')
    _nonempty_strings(seed['counterconditions'], 'counterconditions')
    _nonempty_strings(seed['applicability_tags'], 'applicability_tags')
    license_info = seed['license']
    if not isinstance(license_info, dict) or set(license_info) != {'spdx', 'verified', 'source_ref'}:
        raise SeedValidationError('license posture must be explicit')
    if not isinstance(license_info['spdx'], str) or not license_info['spdx'].strip():
        raise SeedValidationError('license spdx required')
    if not isinstance(license_info['verified'], bool):
        raise SeedValidationError('license verified must be boolean')
    if not isinstance(license_info['source_ref'], str) or not license_info['source_ref'].strip():
        raise SeedValidationError('license source_ref required')
    if seed['reuse_mode'] not in REUSE_MODES:
        raise SeedValidationError('v1 supports REFERENCE_ONLY seeds only')
    rv = seed['rts_validation']
    if not isinstance(rv, dict) or set(rv) != {'status', 'evidence_refs', 'notes'}:
        raise SeedValidationError('rts_validation keys invalid')
    if rv['status'] not in RTS_VALIDATION_STATES:
        raise SeedValidationError('invalid RTS validation state')
    if not isinstance(rv['evidence_refs'], list) or not all(isinstance(x, str) and x.strip() for x in rv['evidence_refs']):
        raise SeedValidationError('RTS evidence refs must be string list')
    if not isinstance(rv['notes'], str):
        raise SeedValidationError('RTS validation notes must be string')
    if seed['authority'] != AUTHORITY_NONE:
        raise SeedValidationError('external seed authority must remain NONE')
    return {'valid': True, 'seed_id': seed['seed_id'], 'state': seed['state'], 'execution_authority': 'NONE', 'promotion_authority': 'NONE', 'canon_authority': 'NONE'}


def validate_registry(registry: dict[str, Any]) -> dict[str, Any]:
    if set(registry) != {'schema_version', 'seeds', 'authority'}:
        raise SeedValidationError('registry keys invalid')
    if registry['schema_version'] != 1:
        raise SeedValidationError('unsupported schema version')
    if registry['authority'] != AUTHORITY_NONE:
        raise SeedValidationError('registry authority must remain NONE')
    if not isinstance(registry['seeds'], list):
        raise SeedValidationError('seeds must be list')
    ids = []
    for seed in registry['seeds']:
        validate_seed(seed)
        ids.append(seed['seed_id'])
    if len(ids) != len(set(ids)):
        raise SeedValidationError('duplicate seed_id')
    return {'valid': True, 'seed_count': len(ids), 'execution_authority': 'NONE', 'promotion_authority': 'NONE', 'canon_authority': 'NONE'}


def match_candidates(registry: dict[str, Any], event_tags: list[str], limit: int = 2) -> dict[str, Any]:
    validate_registry(registry)
    tags = set(_nonempty_strings(event_tags, 'event_tags'))
    if not isinstance(limit, int) or limit < 1 or limit > 10:
        raise SeedValidationError('limit must be 1..10')
    candidates = []
    for seed in registry['seeds']:
        if seed['state'] in {'REJECTED', 'ARCHIVED'}:
            continue
        matched = sorted(tags.intersection(seed['applicability_tags']))
        if not matched:
            continue
        candidates.append({
            'seed_id': seed['seed_id'],
            'state': seed['state'],
            'matched_tags': matched,
            'source_refs': seed['source_refs'],
            'rts_validation_status': seed['rts_validation']['status'],
            'execution_authority': 'NONE',
            'promotion_authority': 'NONE',
            'canon_authority': 'NONE',
        })
    candidates.sort(key=lambda x: (-len(x['matched_tags']), x['seed_id']))
    return {
        'candidates': candidates[:limit],
        'candidate_count': min(len(candidates), limit),
        'routing_authority': 'NONE',
        'execution_authority': 'NONE',
        'promotion_authority': 'NONE',
        'canon_authority': 'NONE',
    }


def load_registry(path: str | Path) -> dict[str, Any]:
    registry = json.loads(Path(path).read_text(encoding='utf-8'))
    validate_registry(registry)
    return registry
'''
    write('external_seed_corpus/core.py', core)
    write('external_seed_corpus/__init__.py', '''from .core import ALLOWED_STATES,EVIDENCE_CLASSES,RTS_VALIDATION_STATES,REUSE_MODES,SeedValidationError,validate_seed,validate_registry,match_candidates,load_registry\n__all__=['ALLOWED_STATES','EVIDENCE_CLASSES','RTS_VALIDATION_STATES','REUSE_MODES','SeedValidationError','validate_seed','validate_registry','match_candidates','load_registry']\n''')
    cli = r'''import argparse
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
'''
    write('external_seed_corpus/cli.py', cli)
    write('external_seed_corpus/__main__.py', 'from .cli import main\nmain()\n')
    write('external_seed_corpus/README.md', '''# External Transition Pattern Seed Corpus v1\n\nExternal public evidence enters RTS as `REFERENCE_ONLY` seeds, never as Canon.\n\nAllowed seed states: `RAW`, `VERIFICATION_PENDING`, `INTERNALLY_VALIDATED`, `REJECTED`, `ARCHIVED`.\n\n`EXTERNAL MERGE != RTS CANON`\n\n`RETRIEVAL != AUTHORIZATION`\n\nEvery seed must preserve exact source refs, failure boundary, repair principle, applicability, counterconditions, evidence class, license/reuse posture and RTS validation state. v1 copies no upstream code.\n''')


def tests_and_registry():
    openclaw_seed = {
        'seed_id': 'ext-openclaw-embedding-item-limit-split-v1',
        'pattern_title': 'Split only explicitly reported oversized embedding item batches; do not replay the same known-invalid batch',
        'state': 'VERIFICATION_PENDING',
        'source_refs': [
            {
                'repository': 'openclaw/openclaw',
                'kind': 'pull_request',
                'ref': 'pull/125722@08fa41c1606a4c201462d76f43184e6920a0cef7',
                'url': 'https://github.com/openclaw/openclaw/pull/125722',
                'merged': False,
            },
            {
                'repository': 'openclaw/openclaw',
                'kind': 'pull_request',
                'ref': 'pull/129927@657026cab35f62e6b9a68da0f7fad3666874c28d',
                'url': 'https://github.com/openclaw/openclaw/pull/129927',
                'merged': True,
            },
        ],
        'observed_failure_boundary': 'OpenAI-compatible embedding providers can explicitly reject oversized input-item batches; replaying the unchanged batch cannot succeed, and unrelated digits inside request ids can be misread as HTTP status if matching is unbounded.',
        'repair_principle': 'Recognize only self-describing supported item-limit shapes, route those through an existing order-preserving splitter, skip futile unchanged retries, and leave generic malformed HTTP 400 input failures out of split recovery.',
        'evidence_class': 'UPSTREAM_MERGED_REPAIR',
        'applicability_conditions': [
            'A bounded batch owner already exists and can split while preserving order.',
            'The provider error explicitly identifies an item-count or supported input-length limit shape.',
            'Retrying the same unchanged oversized batch is known to be futile.',
        ],
        'counterconditions': [
            'Generic or ambiguous HTTP 400 input-validation failures without a supported explicit limit shape.',
            'Token-length failures that are not item-count failures.',
            'Transient 429/5xx/network failures governed by a distinct retry policy.',
        ],
        'applicability_tags': ['batch-limit', 'failure-isolation', 'retry-avoidance', 'incremental-recovery', 'embedding'],
        'license': {
            'spdx': 'MIT',
            'verified': True,
            'source_ref': 'openclaw/openclaw/LICENSE@ebaebf7c416761a32f932ad70ebe5d1d2e214f68',
        },
        'reuse_mode': 'REFERENCE_ONLY',
        'rts_validation': {
            'status': 'VERIFICATION_PENDING',
            'evidence_refs': [],
            'notes': 'Upstream merged evidence is preserved, but transfer to RTS has not been independently validated and grants no Canon authority.',
        },
        'authority': {'execution': 'NONE', 'promotion': 'NONE', 'canon': 'NONE'},
    }
    recall_seed = {
        'seed_id': 'ext-decision-os-lane-recall-weight-limits-v1',
        'pattern_title': 'Recall should downshift when it does not change a real decision or when too many memory lanes add process weight',
        'state': 'VERIFICATION_PENDING',
        'source_refs': [
            {
                'repository': 'shin4141/decision-os-v13-loopkit',
                'kind': 'commit_file',
                'ref': 'fe88f90430bacbb8f5aaf3ac5439e0580c04abd6:field_notes/050_lane_recall_failure_and_weight_limits.md',
                'url': 'https://github.com/shin4141/decision-os-v13-loopkit/blob/fe88f90430bacbb8f5aaf3ac5439e0580c04abd6/field_notes/050_lane_recall_failure_and_weight_limits.md',
                'merged': True,
            }
        ],
        'observed_failure_boundary': 'Memory recall itself can create governance drag, stale-note authority leaks and analysis overload when used for tiny work or when multiple lanes do not change the next action.',
        'repair_principle': 'Use no/light recall when local context is enough; invoke bounded recall only when it can change a gate, protected surface or first read; recheck stale notes; routing never grants authority.',
        'evidence_class': 'UPSTREAM_DESIGN_NOTE',
        'applicability_conditions': [
            'A prior memory decision could materially change GO/HOLD/CAP/BLOCK, a protected surface, or the first read.',
            'Freshness/supersession can be checked before the recalled note influences action.',
        ],
        'counterconditions': [
            'Tiny local work with an explicit target and no consequential surface.',
            'Discussion where recall does not change an operational decision.',
            'More than two candidate lanes without a distinct decision need; downshift or HOLD instead.',
        ],
        'applicability_tags': ['selective-recall', 'context-weight', 'stale-memory', 'routing-non-authority'],
        'license': {
            'spdx': 'MIT',
            'verified': True,
            'source_ref': 'shin4141/decision-os-v13-loopkit/LICENSE@20d7e5614d096b44120ff50279e9c4d9f87d2557',
        },
        'reuse_mode': 'REFERENCE_ONLY',
        'rts_validation': {
            'status': 'VERIFICATION_PENDING',
            'evidence_refs': [],
            'notes': 'Concept note only. RTS already has Child A selective recall; this seed remains external evidence until a distinct internal validation record exists.',
        },
        'authority': {'execution': 'NONE', 'promotion': 'NONE', 'canon': 'NONE'},
    }
    registry = {
        'schema_version': 1,
        'seeds': [openclaw_seed, recall_seed],
        'authority': {'execution': 'NONE', 'promotion': 'NONE', 'canon': 'NONE'},
    }
    write_json('external_seeds/registry.json', registry)
    write('external_seeds/SOURCES.md', '''# External Seed Sources\n\nAll v1 entries are `REFERENCE_ONLY`; no upstream code is copied.\n\n- OpenClaw contributor origin: `openclaw/openclaw#125722` at `08fa41c1606a4c201462d76f43184e6920a0cef7` (closed, not merged).\n- OpenClaw maintainer continuation: `openclaw/openclaw#129927` at `657026cab35f62e6b9a68da0f7fad3666874c28d` (merged; credits the original fix).\n- OpenClaw license: MIT, `LICENSE@ebaebf7c416761a32f932ad70ebe5d1d2e214f68`.\n- Decision-OS V13 note: `field_notes/050_lane_recall_failure_and_weight_limits.md@fe88f90430bacbb8f5aaf3ac5439e0580c04abd6`.\n- Decision-OS V13 license: MIT, `LICENSE@20d7e5614d096b44120ff50279e9c4d9f87d2557`.\n\nExternal source status is evidence only. It does not set RTS validation, promotion, execution, or Canon authority.\n''')
    tests = r'''import json
import unittest
from pathlib import Path
from external_seed_corpus import SeedValidationError, load_registry, match_candidates, validate_registry, validate_seed


class ExternalSeedCorpusTests(unittest.TestCase):
    def setUp(self):
        self.registry = json.loads(Path('external_seeds/registry.json').read_text())

    def test_committed_registry_validates(self):
        result = validate_registry(self.registry)
        self.assertTrue(result['valid'])
        self.assertEqual(result['seed_count'], 2)
        self.assertEqual(result['canon_authority'], 'NONE')

    def test_match_is_bounded_and_non_authorizing(self):
        result = match_candidates(self.registry, ['batch-limit', 'retry-avoidance'])
        self.assertEqual(result['candidate_count'], 1)
        self.assertEqual(result['candidates'][0]['seed_id'], 'ext-openclaw-embedding-item-limit-split-v1')
        self.assertEqual(result['routing_authority'], 'NONE')
        self.assertEqual(result['canon_authority'], 'NONE')

    def test_duplicate_seed_ids_fail(self):
        registry = dict(self.registry)
        registry['seeds'] = [self.registry['seeds'][0], self.registry['seeds'][0]]
        with self.assertRaises(SeedValidationError):
            validate_registry(registry)

    def test_load_registry_round_trip(self):
        self.assertEqual(len(load_registry('external_seeds/registry.json')['seeds']), 2)
'''
    write('tests/test_external_seed_corpus.py', tests)
    da = r'''import copy
import json
import unittest
from pathlib import Path
from external_seed_corpus import SeedValidationError, match_candidates, validate_seed


class ExternalSeedCorpusDA(unittest.TestCase):
    def setUp(self):
        self.seed = json.loads(Path('external_seeds/registry.json').read_text())['seeds'][0]

    def test_missing_exact_provenance_fails(self):
        seed = copy.deepcopy(self.seed)
        seed['source_refs'] = []
        with self.assertRaises(SeedValidationError):
            validate_seed(seed)

    def test_missing_counterconditions_fails(self):
        seed = copy.deepcopy(self.seed)
        seed['counterconditions'] = []
        with self.assertRaises(SeedValidationError):
            validate_seed(seed)

    def test_external_merge_cannot_be_canonical(self):
        seed = copy.deepcopy(self.seed)
        self.assertTrue(any(x['merged'] for x in seed['source_refs']))
        seed['state'] = 'CANONICAL'
        with self.assertRaises(SeedValidationError):
            validate_seed(seed)

    def test_authority_escalation_fails(self):
        seed = copy.deepcopy(self.seed)
        seed['authority']['canon'] = 'APPROVED'
        with self.assertRaises(SeedValidationError):
            validate_seed(seed)

    def test_missing_license_posture_fails(self):
        seed = copy.deepcopy(self.seed)
        seed['license'] = {}
        with self.assertRaises(SeedValidationError):
            validate_seed(seed)

    def test_reference_only_is_mandatory(self):
        seed = copy.deepcopy(self.seed)
        seed['reuse_mode'] = 'COPY_CODE'
        with self.assertRaises(SeedValidationError):
            validate_seed(seed)

    def test_rejected_seed_is_not_matched(self):
        registry = json.loads(Path('external_seeds/registry.json').read_text())
        registry['seeds'][0]['state'] = 'REJECTED'
        result = match_candidates(registry, ['batch-limit'])
        self.assertEqual(result['candidate_count'], 0)
'''
    write('tests/test_external_seed_corpus_da.py', da)


def validate():
    run('python', '-m', 'external_seed_corpus', 'verify', '--registry', 'external_seeds/registry.json')
    run('python', '-m', 'external_seed_corpus', 'match', '--registry', 'external_seeds/registry.json', '--tag', 'batch-limit', '--tag', 'retry-avoidance')
    run('python', '-m', 'unittest', 'tests.test_external_seed_corpus', 'tests.test_external_seed_corpus_da', '-v')
    run('python', '-m', 'unittest', 'tests.test_reuse_metrics', 'tests.test_reuse_metrics_da', '-v')
    run('python', '-m', 'unittest', 'tests.test_intelligence_compiler', 'tests.test_intelligence_compiler_da', '-v')
    run('python', '-m', 'unittest', 'tests.test_restart_surface', 'tests.test_restart_surface_da', '-v')
    run('python', '-m', 'unittest', 'tests.test_selective_recall', 'tests.test_selective_recall_da', '-v')
    run('python', '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_freezer*.py', '-v')
    run('python', '-m', 'freezer.cli', 'verify')
    run('python', '-m', 'freezer.build_assessment', 'verify')


def close():
    write('thin-rts/ultimate-loop/METEOR_RESULT_FRZ_000015_2026-08-27.md', f'''# FRZ-000015 — External Transition Pattern Seed Corpus v1 — METEOR Result\n\nStatus: **REPOSITORY_METEOR_SURVIVOR / LOCAL_VERIFICATION_BOUNDARY**\n\nInitial destructive candidate death: Actions run `{os.environ.get('GITHUB_RUN_ID', 'UNKNOWN')}`. The naive candidate accepted `CANONICAL`, omitted exact provenance/counterconditions, and therefore failed the destructive seed-boundary test.\n\nSurvivor boundary: exact repository/ref/URL provenance, applicability, counterconditions, evidence class, license/reuse posture and RTS validation state are mandatory. External merge evidence cannot create `CANONICAL` state. Registry/matcher grant no execution/promotion/canon authority. v1 is `REFERENCE_ONLY`; no upstream code is copied.\n\nDeployment Identity is not applicable: repository-local registry/validator/CLI only. Equivalent boundary is committed seed corpus + deterministic validation + destructive authority/generalization tests + A/B/C/D and FREEZER regressions.\n''')
    write_json('/tmp/ev.json', {'status': 'VERIFIED'})
    run('python', '-m', 'freezer.cli', 'revise', ITEM, '--input', '/tmp/ev.json')
    write_json('/tmp/ec.json', {'status': 'COMPLETED'})
    run('python', '-m', 'freezer.cli', 'revise', ITEM, '--input', '/tmp/ec.json')
    run('python', '-m', 'freezer.cli', 'reindex')
    run('python', '-m', 'freezer.build_assessment', 'reindex')
    validate()
    for item_id in ('RTS-FRZ-000011', 'RTS-FRZ-000012', 'RTS-FRZ-000013', 'RTS-FRZ-000014', 'RTS-FRZ-000015'):
        assert current(item_id)['status'] == 'COMPLETED', current(item_id)
    active = [p.parent.name for p in (ROOT / 'freezer/items').glob('RTS-FRZ-*/current.json') if current(p.parent.name)['status'] == 'IN_PROGRESS']
    assert active == [], active


def commit():
    run('git', 'config', 'user.name', 'github-actions[bot]')
    run('git', 'config', 'user.email', '41898282+github-actions[bot]@users.noreply.github.com')
    paths = [
        'docs/implementation/frz000015_inputs',
        'docs/implementation/FRZ_000015_EXTERNAL_TRANSITION_PATTERN_SEED_CORPUS_V1_TASK.md',
        'freezer',
        'external_seed_corpus',
        'external_seeds',
        'tests/test_external_seed_corpus.py',
        'tests/test_external_seed_corpus_da.py',
        'thin-rts/ultimate-loop/METEOR_RESULT_FRZ_000015_2026-08-27.md',
    ]
    run('git', 'add', *paths)
    staged = subprocess.check_output(['git', 'diff', '--cached', '--name-only'], text=True).splitlines()
    forbidden = [p for p in staged if p.startswith('.github/workflows/') or p == 'scripts/run_frz000015_ultimate_loop.py']
    assert not forbidden, forbidden
    run('git', 'commit', '-m', 'feat: complete FRZ-000015 external transition seed corpus v1')
    run('git', 'push', 'origin', f'HEAD:{BRANCH}')


def main():
    assert_start()
    governance_inputs()
    govern()
    initial_death()
    survivor()
    tests_and_registry()
    validate()
    close()
    commit()


if __name__ == '__main__':
    main()

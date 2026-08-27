from __future__ import annotations

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

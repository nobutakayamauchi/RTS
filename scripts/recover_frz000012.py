from __future__ import annotations

import os
import subprocess
from pathlib import Path

SOURCE = Path('.github/workflows/frz-000012-ultimate-loop-once.yml')
TARGET_STEPS = [
    'Assert exact B start boundary',
    'Materialize governed assessment and preflight inputs',
    'Govern B through BUILD_NOW PASS SELECTED IN_PROGRESS',
    'Build initial B candidate and prove DA death',
    'Minimal repair and permanent B implementation',
    'Final B baseline DA and Counter-DA',
    'Write B METEOR evidence and close FREEZER',
    'Post-completion regression and sibling freeze proof',
]


def extract_run_blocks(text: str) -> dict[str, str]:
    lines = text.splitlines()
    blocks: dict[str, str] = {}
    i = 0
    while i < len(lines):
        line = lines[i]
        prefix = '      - name: '
        if not line.startswith(prefix):
            i += 1
            continue
        name = line[len(prefix):].strip()
        i += 1
        while i < len(lines) and not lines[i].startswith('      - '):
            if lines[i] == '        run: |':
                i += 1
                body: list[str] = []
                while i < len(lines) and not lines[i].startswith('      - '):
                    current = lines[i]
                    if current.startswith('          '):
                        body.append(current[10:])
                    elif current.strip() == '':
                        body.append('')
                    else:
                        raise RuntimeError(f'unexpected run indentation for {name}: {current!r}')
                    i += 1
                blocks[name] = '\n'.join(body) + '\n'
                break
            i += 1
    return blocks


def run_shell(name: str, script: str) -> None:
    print(f'=== replay: {name} ===', flush=True)
    subprocess.run(['bash', '-c', 'set -euo pipefail\n' + script], check=True, env=os.environ.copy())


def correct_meteor() -> None:
    run = os.environ.get('GITHUB_RUN_ID', 'UNKNOWN')
    text = f'''# FRZ-000012 — Compact Active + Restart Surface v1 — METEOR Result

Status: **REPOSITORY_METEOR_SURVIVOR / LOCAL_VERIFICATION_BOUNDARY**

Initial destructive candidate death: GitHub Actions run `33049315043`. The deliberately naive compactor dropped `do_not_touch`, did not reject over-budget unresolved state, and failed restart equivalence. Those death classes remain permanent DA tests.

Recovery / survivor verification run: `{run}`.

Minimal repair: fixed restart denominator; traceable current source pointers; restart-equivalence validation; measured active load; fail-closed over-budget behavior; explicit full-history reopen reasons; bounded Selective Recall handoff; permanent `execution_authority=NONE` and `promotion_authority=NONE`.

Counter-DA proves compact state preserves UNKNOWN and do-not-touch constraints, while required-state loss is detected instead of hidden.

Deployment Identity is not applicable because this is a repository-local library/CLI with no live route. Equivalent verification boundary: committed source + deterministic CLI + current source hashes + destructive tests + FREEZER governance verification.
'''
    Path('thin-rts/ultimate-loop/METEOR_RESULT_FRZ_000012_2026-08-27.md').write_text(text, encoding='utf-8')


def assert_final_boundary() -> None:
    subprocess.run(['python', '-m', 'restart_surface', 'verify'], check=True)
    subprocess.run(['python', '-m', 'unittest', 'tests.test_restart_surface', 'tests.test_restart_surface_da', '-v'], check=True)
    subprocess.run(['python', '-m', 'unittest', 'tests.test_selective_recall', 'tests.test_selective_recall_da', '-v'], check=True)
    subprocess.run(['python', '-m', 'freezer.cli', 'verify'], check=True)
    subprocess.run(['python', '-m', 'freezer.build_assessment', 'verify'], check=True)


def commit_survivor() -> None:
    paths = [
        'docs/implementation/frz000012_inputs',
        'docs/implementation/FRZ_000012_COMPACT_ACTIVE_RESTART_SURFACE_V1_TASK.md',
        'freezer',
        'restart',
        'restart_surface',
        'tests/test_restart_surface.py',
        'tests/test_restart_surface_da.py',
        'thin-rts/ultimate-loop/METEOR_RESULT_FRZ_000012_2026-08-27.md',
    ]
    subprocess.run(['git', 'config', 'user.name', 'github-actions[bot]'], check=True)
    subprocess.run(['git', 'config', 'user.email', '41898282+github-actions[bot]@users.noreply.github.com'], check=True)
    subprocess.run(['git', 'add', *paths], check=True)
    staged = subprocess.check_output(['git', 'diff', '--cached', '--name-only'], text=True).splitlines()
    forbidden = [p for p in staged if p.startswith('.github/workflows/') or p == 'scripts/recover_frz000012.py']
    if forbidden:
        raise RuntimeError(f'forbidden recovery stage: {forbidden}')
    subprocess.run(['git', 'commit', '-m', 'feat: complete FRZ-000012 compact restart surface v1'], check=True)
    subprocess.run(['git', 'push', 'origin', 'HEAD:feature/frz-000012-compact-active-restart-surface-v1'], check=True)


def main() -> None:
    blocks = extract_run_blocks(SOURCE.read_text(encoding='utf-8'))
    missing = [name for name in TARGET_STEPS if name not in blocks]
    if missing:
        raise RuntimeError(f'missing replay blocks: {missing}')
    for name in TARGET_STEPS:
        run_shell(name, blocks[name])
    correct_meteor()
    assert_final_boundary()
    commit_survivor()


if __name__ == '__main__':
    main()

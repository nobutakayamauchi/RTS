#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
EXP="$ROOT/experiments/codex_reasoning_density_v1"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="${1:-$EXP/results/history-$STAMP}"

mkdir -p "$OUT"

printf 'Codex history inventory\n'
printf '  output: %s\n' "$OUT"
printf '  mode: read-only\n'
printf '  raw prompt/response text: excluded\n'
printf '  auth/config secrets: excluded\n\n'

python3 "$EXP/collect_history.py" --output "$OUT"

printf '\nTop historical sessions by input_tokens (HIGH confidence first):\n'
python3 - "$OUT/historical_baseline.json" <<'PY'
import json, sys
p=sys.argv[1]
data=json.load(open(p, encoding='utf-8'))
rows=data.get('sessions', [])
rank={'HIGH':0,'LOW':1,'NONE':2}
rows.sort(key=lambda r:(rank.get(r.get('usage_confidence'),9), -(r.get('input_tokens') or -1)))
for r in rows[:20]:
    print(
        f"{r.get('usage_confidence','?'):4} "
        f"input={str(r.get('input_tokens')):>10} "
        f"cached={str(r.get('cached_input_tokens')):>10} "
        f"reasoning={str(r.get('reasoning_output_tokens')):>10} "
        f"model={r.get('model') or '-'} "
        f"cwd={r.get('cwd') or '-'} "
        f"file={r.get('session_file')}"
    )
PY

printf '\nNext: send summary.json plus the top-session table back for baseline review.\n'

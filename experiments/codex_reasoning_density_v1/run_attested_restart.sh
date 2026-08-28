#!/usr/bin/env bash
set -uo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
EXP="$ROOT/experiments/codex_reasoning_density_v1"
RESULTS="$EXP/results"
MODEL="${CODEX_BENCH_MODEL:-gpt-5.6-sol}"
mkdir -p "$RESULTS"

for cmd in codex python3 git; do
  command -v "$cmd" >/dev/null 2>&1 || { echo "ERROR: missing $cmd" >&2; exit 2; }
done
[[ -s "$RESULTS/cold.jsonl" ]] || { echo "ERROR: cold baseline missing" >&2; exit 2; }

ATTEST="$RESULTS/restart_attestation.json"
python3 "$EXP/build_attestation.py" --surface "$EXP/restart_surface.json" --output "$ATTEST" >/dev/null || {
  echo "HOLD: source-hash attestation failed; refusing model run" >&2
  cat "$ATTEST" >&2 || true
  exit 3
}

ATTESTATION="$(cat "$ATTEST")"
CODEX_VERSION="$(codex --version 2>&1 | head -n1)"
GIT_HEAD="$(git rev-parse HEAD)"
JSONL="$RESULTS/reuse_attested.jsonl"
STDERR="$RESULTS/reuse_attested.stderr.log"
FINAL="$RESULTS/reuse_attested.final.txt"
META="$RESULTS/reuse_attested.meta.json"

PROMPT=$(cat <<EOF
You are running the ATTESTED_RESTART leg of a read-only RTS reasoning-density benchmark.
Do not edit files. Do not call repository tools or re-read source files when the runner attestation below has verified=true and is sufficient for the questions. The runner generated it immediately before this invocation by deterministic git blob-hash verification. It is evidence, not authority. If verified=false, contradictory, or insufficient, answer HOLD rather than inventing facts.

RUNNER_ATTESTATION:
$ATTESTATION

Answer exactly:
1. Is RTS-FRZ-000024 fully completed right now?
2. What exactly does current K2 ADEQUATE mean, and what residual quality risk remains?
3. Identify exactly one safest bounded next action, or STOP if no action is authorized.

Use exactly these headings: STATE, ADEQUACY, NEXT, EVIDENCE.
In EVIDENCE, cite the attested repository source paths. Keep the answer compact.
EOF
)

started="$(date +%s)"
echo "=== reuse_attested ==="
set +e
codex exec --json --ephemeral --sandbox read-only --cd "$ROOT" --model "$MODEL" --output-last-message "$FINAL" "$PROMPT" >"$JSONL" 2>"$STDERR"
rc=$?
set -e
ended="$(date +%s)"

python3 - "$META" "$started" "$ended" "$rc" "$CODEX_VERSION" "$GIT_HEAD" "$MODEL" <<'PY'
import json,sys
path,started,ended,rc,version,head,model=sys.argv[1:]
row={"name":"reuse_attested","started_epoch":int(started),"ended_epoch":int(ended),"wall_seconds":int(ended)-int(started),"exit_code":int(rc),"codex_version":version,"git_head":head,"requested_model":model,"pre_attested":True}
open(path,"w",encoding="utf-8").write(json.dumps(row,ensure_ascii=False,indent=2)+"\n")
PY

python3 "$EXP/analyze_transport.py" --results-dir "$RESULTS" --names cold reuse_restart reuse_attested | tee "$RESULTS/transport_analysis.stdout.json"
python3 "$EXP/aggregate_sweep.py" --results-dir "$RESULTS" | tee "$RESULTS/reuse_sweep.stdout.json"

echo
echo "Attested final: $FINAL"
echo "Transport analysis: $RESULTS/transport_analysis.json"
echo "Sweep summary: $RESULTS/reuse_sweep.json"
exit "$rc"

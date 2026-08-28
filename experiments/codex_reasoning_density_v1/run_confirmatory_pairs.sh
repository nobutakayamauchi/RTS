#!/usr/bin/env bash
set -uo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
EXP="$ROOT/experiments/codex_reasoning_density_v1"
MODEL="${CODEX_BENCH_MODEL:-gpt-5.6-sol}"
PAIRS="${CONFIRM_PAIRS:-3}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="$EXP/results/confirmatory-$STAMP"
mkdir -p "$OUT"

for cmd in codex python3 git; do
  command -v "$cmd" >/dev/null 2>&1 || { echo "ERROR: missing $cmd" >&2; exit 2; }
done
[[ "$PAIRS" =~ ^[1-9][0-9]*$ ]] || { echo "ERROR: CONFIRM_PAIRS must be a positive integer" >&2; exit 2; }
(( PAIRS <= 5 )) || { echo "ERROR: CONFIRM_PAIRS > 5 refused for bounded-cost confirmation" >&2; exit 2; }

CODEX_VERSION="$(codex --version 2>&1 | head -n1)"
GIT_HEAD="$(git rev-parse HEAD)"
COMMON=(exec --json --ephemeral --sandbox read-only --cd "$ROOT" --model "$MODEL")

COLD_PROMPT=$(cat <<'EOF'
You are running the COLD leg of a read-only RTS confirmatory benchmark. Do not edit files.
Starting without a supplied current-state attestation, inspect only the repository evidence needed to answer exactly:
1. Is RTS-FRZ-000024 fully completed right now?
2. What exactly does current K2 ADEQUATE mean, and what residual quality risk remains?
3. Identify exactly one safest bounded next action, or STOP if no action is authorized.
Do not speculate. Use exactly these headings: STATE, ADEQUACY, NEXT, EVIDENCE.
In EVIDENCE cite current repository paths. Keep the answer compact.
EOF
)

make_attested_prompt() {
  local attestation="$1"
  cat <<EOF
You are running the ATTESTED leg of a read-only RTS confirmatory benchmark. Do not edit files.
The runner immediately before this invocation performed deterministic git blob-hash verification and supplied the attestation below. When verified=true and sufficient, do not call repository tools or re-read source contents. The attestation is evidence, not authority. If verified=false, contradictory, or insufficient, answer HOLD rather than inventing facts.

RUNNER_ATTESTATION:
$attestation

Answer exactly:
1. Is RTS-FRZ-000024 fully completed right now?
2. What exactly does current K2 ADEQUATE mean, and what residual quality risk remains?
3. Identify exactly one safest bounded next action, or STOP if no action is authorized.
Use exactly these headings: STATE, ADEQUACY, NEXT, EVIDENCE.
In EVIDENCE cite the attested repository source paths. Keep the answer compact.
EOF
}

run_one() {
  local stem="$1" condition="$2" prompt="$3" order="$4"
  local jsonl="$OUT/$stem.jsonl" stderr="$OUT/$stem.stderr.log" final="$OUT/$stem.final.txt" meta="$OUT/$stem.meta.json"
  local started ended rc
  started="$(date +%s)"
  echo "=== $stem ($condition, order=$order) ==="
  set +e
  codex "${COMMON[@]}" --output-last-message "$final" "$prompt" >"$jsonl" 2>"$stderr"
  rc=$?
  set -e
  ended="$(date +%s)"
  python3 - "$meta" "$stem" "$condition" "$order" "$started" "$ended" "$rc" "$CODEX_VERSION" "$GIT_HEAD" "$MODEL" <<'PY'
import json,sys
path,stem,condition,order,started,ended,rc,version,head,model=sys.argv[1:]
row={
  "name":stem,"condition":condition,"order_in_pair":int(order),
  "started_epoch":int(started),"ended_epoch":int(ended),"wall_seconds":int(ended)-int(started),
  "exit_code":int(rc),"codex_version":version,"git_head":head,"requested_model":model,
  "fresh_ephemeral":True,
}
open(path,"w",encoding="utf-8").write(json.dumps(row,ensure_ascii=False,indent=2)+"\n")
PY
  if [[ $rc -ne 0 ]]; then
    echo "WARN: $stem exited $rc; evidence preserved" >&2
  fi
}

for ((i=1; i<=PAIRS; i++)); do
  ATTEST="$OUT/pair${i}_attestation.json"
  if ! python3 "$EXP/build_attestation.py" --surface "$EXP/restart_surface.json" --output "$ATTEST" >/dev/null; then
    echo "HOLD: pair $i source attestation failed; refusing further model runs" >&2
    cat "$ATTEST" >&2 || true
    exit 3
  fi
  ATTESTATION="$(cat "$ATTEST")"
  ATTESTED_PROMPT="$(make_attested_prompt "$ATTESTATION")"

  if (( i % 2 == 1 )); then
    run_one "pair${i}_cold" "COLD" "$COLD_PROMPT" 1
    run_one "pair${i}_attested" "ATTESTED" "$ATTESTED_PROMPT" 2
  else
    run_one "pair${i}_attested" "ATTESTED" "$ATTESTED_PROMPT" 1
    run_one "pair${i}_cold" "COLD" "$COLD_PROMPT" 2
  fi
done

python3 "$EXP/aggregate_confirmatory.py" --results-dir "$OUT" --pairs "$PAIRS" | tee "$OUT/confirmatory_summary.stdout.json"

echo
echo "Confirmatory directory: $OUT"
echo "Summary: $OUT/confirmatory_summary.json"
echo "Rule: all $PAIRS fresh pairs must win on total + uncached input with quality preserved."

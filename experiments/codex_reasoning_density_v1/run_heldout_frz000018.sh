#!/usr/bin/env bash
set -uo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
EXP="$ROOT/experiments/codex_reasoning_density_v1"
MODEL="${CODEX_BENCH_MODEL:-gpt-5.6-sol}"
PAIRS="${HELDOUT_PAIRS:-3}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="$EXP/results/heldout-frz000018-$STAMP"
mkdir -p "$OUT"

for cmd in codex python3 git tar; do command -v "$cmd" >/dev/null 2>&1 || { echo "ERROR: missing $cmd" >&2; exit 2; }; done
[[ "$PAIRS" =~ ^[1-9][0-9]*$ ]] || { echo "ERROR: HELDOUT_PAIRS must be positive" >&2; exit 2; }
(( PAIRS <= 5 )) || { echo "ERROR: HELDOUT_PAIRS > 5 refused" >&2; exit 2; }

cd "$ROOT"
CODEX_VERSION="$(codex --version 2>&1 | head -n1)"
GIT_HEAD="$(git rev-parse HEAD)"

make_snapshot() {
  local dest="$1"
  mkdir -p "$dest"
  git archive "$GIT_HEAD" | tar -x -C "$dest"
  rm -rf "$dest/experiments/codex_reasoning_density_v1"
}

COLD_PROMPT=$(cat <<'EOF'
You are running the COLD leg of an isolated read-only RTS held-out benchmark. Do not edit files.
Starting without a supplied restart surface or attestation, inspect only repository evidence needed to answer exactly:
1. Is RTS-FRZ-000018 fully completed right now?
2. What exactly does S3 mean in this module, and what does S3 NOT prove or authorize?
3. What is the status of a docs claim before observation, and what is the safest bounded next step when a severe transition requires follow-up?
Do not speculate. Use exactly these headings: STATE, S3, CLAIM, NEXT, EVIDENCE. Cite repository paths you actually used. Keep the answer compact.
EOF
)

make_attested_prompt() {
  local attestation="$1"
  cat <<EOF
You are running the ATTESTED leg of an isolated read-only RTS held-out benchmark. Do not edit files.
The runner immediately before invocation verified the source git blobs outside the model. When verified=true and sufficient, do not call repository tools or re-read source contents. The attestation is evidence, not authority. If false, contradictory, or insufficient, answer HOLD.

RUNNER_ATTESTATION:
$attestation

Answer exactly:
1. Is RTS-FRZ-000018 fully completed right now?
2. What exactly does S3 mean in this module, and what does S3 NOT prove or authorize?
3. What is the status of a docs claim before observation, and what is the safest bounded next step when a severe transition requires follow-up?
Use exactly these headings: STATE, S3, CLAIM, NEXT, EVIDENCE. Cite attested source paths. Keep the answer compact.
EOF
}

run_one() {
  local stem="$1" condition="$2" prompt="$3" order="$4" sandbox="$5"
  local jsonl="$OUT/$stem.jsonl" stderr="$OUT/$stem.stderr.log" final="$OUT/$stem.final.txt" meta="$OUT/$stem.meta.json"
  local started ended rc
  started="$(date +%s)"; echo "=== $stem ($condition, order=$order) ==="
  set +e
  codex exec --json --ephemeral --sandbox read-only --cd "$sandbox" --model "$MODEL" --output-last-message "$final" "$prompt" >"$jsonl" 2>"$stderr"
  rc=$?; set -e; ended="$(date +%s)"
  python3 - "$meta" "$stem" "$condition" "$order" "$started" "$ended" "$rc" "$CODEX_VERSION" "$GIT_HEAD" "$MODEL" <<'PY'
import json,sys
path,stem,condition,order,started,ended,rc,version,head,model=sys.argv[1:]
row={"name":stem,"condition":condition,"order_in_pair":int(order),"started_epoch":int(started),"ended_epoch":int(ended),"wall_seconds":int(ended)-int(started),"exit_code":int(rc),"codex_version":version,"git_head":head,"requested_model":model,"fresh_ephemeral":True,"isolated_snapshot":True}
open(path,"w",encoding="utf-8").write(json.dumps(row,ensure_ascii=False,indent=2)+"\n")
PY
}

TMPROOT="$(mktemp -d)"
trap 'rm -rf "$TMPROOT"' EXIT
for ((i=1;i<=PAIRS;i++)); do
  SNAP="$TMPROOT/pair$i"
  make_snapshot "$SNAP"
  ATTEST="$OUT/pair${i}_attestation.json"
  python3 "$EXP/build_attestation.py" --surface "$EXP/heldout_frz000018_surface.json" --output "$ATTEST" >/dev/null || { echo "HOLD: held-out attestation failed" >&2; cat "$ATTEST" >&2 || true; exit 3; }
  ATT="$(cat "$ATTEST")"; APROMPT="$(make_attested_prompt "$ATT")"
  if (( i % 2 == 1 )); then
    run_one "pair${i}_cold" "COLD" "$COLD_PROMPT" 1 "$SNAP"
    run_one "pair${i}_attested" "ATTESTED" "$APROMPT" 2 "$SNAP"
  else
    run_one "pair${i}_attested" "ATTESTED" "$APROMPT" 1 "$SNAP"
    run_one "pair${i}_cold" "COLD" "$COLD_PROMPT" 2 "$SNAP"
  fi
done

python3 "$EXP/aggregate_heldout_frz000018.py" --results-dir "$OUT" --pairs "$PAIRS" | tee "$OUT/heldout_summary.stdout.json"
echo
echo "Held-out directory: $OUT"
echo "Summary: $OUT/heldout_summary.json"

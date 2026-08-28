#!/usr/bin/env bash
set -uo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
EXP="$ROOT/experiments/codex_reasoning_density_v1"
RESULTS="$EXP/results"
CODEX_BENCH_MODEL="${CODEX_BENCH_MODEL:-gpt-5.6-sol}"
mkdir -p "$RESULTS"

if ! command -v codex >/dev/null 2>&1; then
  echo "ERROR: codex CLI not found in PATH" >&2
  exit 2
fi
if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 not found in PATH" >&2
  exit 2
fi
if [[ ! -s "$RESULTS/cold.jsonl" || ! -s "$RESULTS/reuse.jsonl" ]]; then
  echo "ERROR: prior cold.jsonl and reuse.jsonl are required. Run run.sh first." >&2
  exit 2
fi

CODEX_VERSION="$(codex --version 2>&1 | head -n1)"
GIT_HEAD="$(git rev-parse HEAD 2>/dev/null || echo UNKNOWN)"
COMMON=(exec --json --ephemeral --sandbox read-only --cd "$ROOT" --model "$CODEX_BENCH_MODEL")

make_prompt() {
  local packet="$1"
  cat <<EOF
You are running a read-only RTS reuse-density sweep.
Read AGENTS.md, then read $packet first. Do not edit files.

The packet is routing aid, not authority. Verify only its freshness-critical pointers first. Broaden only if current evidence conflicts or is insufficient.

Answer exactly these questions:
1. Is RTS-FRZ-000024 fully completed right now?
2. What exactly does the current K2 adequacy result mean, and what residual quality risk remains?
3. Identify exactly one safest bounded next action, or say STOP if no action is currently authorized.

Do not speculate. Cite repository paths used as evidence. Keep the final answer compact and use exactly these headings: STATE, ADEQUACY, NEXT, EVIDENCE.
EOF
}

run_one() {
  local name="$1"
  local packet="$2"
  local jsonl="$RESULTS/$name.jsonl"
  local stderr_log="$RESULTS/$name.stderr.log"
  local final_txt="$RESULTS/$name.final.txt"
  local meta="$RESULTS/$name.meta.json"
  local prompt started ended rc
  prompt="$(make_prompt "$packet")"
  started="$(date +%s)"
  echo "=== $name ==="
  set +e
  codex "${COMMON[@]}" --output-last-message "$final_txt" "$prompt" >"$jsonl" 2>"$stderr_log"
  rc=$?
  set -e
  ended="$(date +%s)"
  python3 - "$meta" "$name" "$packet" "$started" "$ended" "$rc" "$CODEX_VERSION" "$GIT_HEAD" "$CODEX_BENCH_MODEL" <<'PY'
import json, sys
path, name, packet, started, ended, rc, version, git_head, model = sys.argv[1:]
row = {
    "name": name,
    "packet": packet,
    "started_epoch": int(started),
    "ended_epoch": int(ended),
    "wall_seconds": int(ended) - int(started),
    "exit_code": int(rc),
    "codex_version": version,
    "git_head": git_head,
    "requested_model": model,
}
with open(path, "w", encoding="utf-8") as f:
    json.dump(row, f, ensure_ascii=False, indent=2)
    f.write("\n")
PY
  if [[ $rc -ne 0 ]]; then
    echo "WARN: $name exited $rc; preserved evidence" >&2
  fi
}

# Preserve the first benchmark's COLD and FULL reuse as the baseline. Only spend
# new provider work on the two thinner routing variants in this exploratory sweep.
run_one reuse_thin "experiments/codex_reasoning_density_v1/reuse_packet_thin.md"
run_one reuse_minimal "experiments/codex_reasoning_density_v1/reuse_packet_minimal.md"

python3 "$EXP/aggregate_sweep.py" --results-dir "$RESULTS" | tee "$RESULTS/reuse_sweep.stdout.json"

echo
echo "Sweep summary: $RESULTS/reuse_sweep.json"
echo "Final answers: $RESULTS/{reuse_thin,reuse_minimal}.final.txt"

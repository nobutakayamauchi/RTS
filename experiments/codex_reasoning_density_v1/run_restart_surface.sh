#!/usr/bin/env bash
set -uo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
EXP="$ROOT/experiments/codex_reasoning_density_v1"
RESULTS="$EXP/results"
CODEX_BENCH_MODEL="${CODEX_BENCH_MODEL:-gpt-5.6-sol}"
PACKET="experiments/codex_reasoning_density_v1/restart_surface.json"
mkdir -p "$RESULTS"

if ! command -v codex >/dev/null 2>&1; then
  echo "ERROR: codex CLI not found in PATH" >&2
  exit 2
fi
if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 not found in PATH" >&2
  exit 2
fi
if [[ ! -s "$RESULTS/cold.jsonl" ]]; then
  echo "ERROR: prior cold.jsonl is required. Run run.sh first." >&2
  exit 2
fi
if [[ ! -s "$ROOT/$PACKET" ]]; then
  echo "ERROR: restart surface missing: $PACKET" >&2
  exit 2
fi

CODEX_VERSION="$(codex --version 2>&1 | head -n1)"
GIT_HEAD="$(git rev-parse HEAD 2>/dev/null || echo UNKNOWN)"
COMMON=(exec --json --ephemeral --sandbox read-only --cd "$ROOT" --model "$CODEX_BENCH_MODEL")

PROMPT=$(cat <<'EOF'
You are running a read-only RTS compact-restart benchmark.
Read AGENTS.md, then read experiments/codex_reasoning_density_v1/restart_surface.json. Do not edit files.

The restart surface is routing/state cache, not authority. For every source listed in it, verify freshness with `git hash-object <path>` only. If all source hashes match, do NOT read those source contents. Expand only on a hash mismatch, a contradiction, or a fact required by this task that the restart surface does not represent.

Answer exactly these questions:
1. Is RTS-FRZ-000024 fully completed right now?
2. What exactly does the current K2 adequacy result mean, and what residual quality risk remains?
3. Identify exactly one safest bounded next action, or say STOP if no action is currently authorized.

Do not speculate. Cite the restart surface plus the source paths whose hashes you verified. Keep the final answer compact and use exactly these headings: STATE, ADEQUACY, NEXT, EVIDENCE.
EOF
)

name="reuse_restart"
jsonl="$RESULTS/$name.jsonl"
stderr_log="$RESULTS/$name.stderr.log"
final_txt="$RESULTS/$name.final.txt"
meta="$RESULTS/$name.meta.json"
started="$(date +%s)"

echo "=== $name ==="
set +e
codex "${COMMON[@]}" --output-last-message "$final_txt" "$PROMPT" >"$jsonl" 2>"$stderr_log"
rc=$?
set -e
ended="$(date +%s)"

python3 - "$meta" "$name" "$PACKET" "$started" "$ended" "$rc" "$CODEX_VERSION" "$GIT_HEAD" "$CODEX_BENCH_MODEL" <<'PY'
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

python3 "$EXP/aggregate_sweep.py" --results-dir "$RESULTS" | tee "$RESULTS/restart_surface.stdout.json"

echo
echo "Sweep summary: $RESULTS/reuse_sweep.json"
echo "Restart final: $RESULTS/reuse_restart.final.txt"

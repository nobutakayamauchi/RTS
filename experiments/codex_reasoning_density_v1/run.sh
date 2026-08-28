#!/usr/bin/env bash
set -uo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
EXP="$ROOT/experiments/codex_reasoning_density_v1"
RESULTS="$EXP/results"
REFERENCE_TOKENS="${REFERENCE_TOKENS:-5000000}"
CODEX_BENCH_MODEL="${CODEX_BENCH_MODEL:-}"
mkdir -p "$RESULTS"

if ! command -v codex >/dev/null 2>&1; then
  echo "ERROR: codex CLI not found in PATH" >&2
  exit 2
fi
if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 not found in PATH" >&2
  exit 2
fi

CODEX_VERSION="$(codex --version 2>&1 | head -n1)"
GIT_HEAD="$(git rev-parse HEAD 2>/dev/null || echo UNKNOWN)"

COMMON=(exec --json --ephemeral --sandbox read-only --cd "$ROOT")
if [[ -n "$CODEX_BENCH_MODEL" ]]; then
  COMMON+=(--model "$CODEX_BENCH_MODEL")
fi

COLD_PROMPT=$(cat <<'EOF'
You are running a read-only reasoning-density benchmark in the RTS repository.
Read AGENTS.md first. Do not edit files.

Starting without any supplied restart packet, inspect only what you need to answer these three questions from current repository evidence:
1. Is RTS-FRZ-000024 fully completed right now?
2. What exactly does the current K2 adequacy result mean, and what residual quality risk remains?
3. Identify exactly one safest bounded next action, or say STOP if no action is currently authorized.

Do not speculate. Cite repository paths used as evidence. Keep the final answer compact and use exactly these headings: STATE, ADEQUACY, NEXT, EVIDENCE.
EOF
)

REUSE_PROMPT=$(cat <<'EOF'
You are running a read-only reasoning-density benchmark in the RTS repository.
Read AGENTS.md, then read experiments/codex_reasoning_density_v1/reuse_packet.md first. Do not edit files.

The reuse packet is routing aid, not authority. Verify only its freshness-critical pointers first. Do not broadly rediscover completed K0/K1/K2 history unless the packet is stale, contradictory, or insufficient.

Answer the same three questions:
1. Is RTS-FRZ-000024 fully completed right now?
2. What exactly does the current K2 adequacy result mean, and what residual quality risk remains?
3. Identify exactly one safest bounded next action, or say STOP if no action is currently authorized.

Do not speculate. Cite repository paths used as evidence. Keep the final answer compact and use exactly these headings: STATE, ADEQUACY, NEXT, EVIDENCE.
EOF
)

NEXT_PROMPT=$(cat <<'EOF'
You are running the third, read-only leg of an RTS reasoning-density benchmark.
Read AGENTS.md and experiments/codex_reasoning_density_v1/reuse_packet.md first. Do not edit files.

Assume completed historical K0/K1/K2 exploration is KNOWN only after verifying the packet's freshness-critical pointers. Do not re-derive that history unless current evidence conflicts.

Perform the next related reasoning task: design one bounded held-out sampling experiment for a future model/corpus transition that can test whether false greens still escape the current K2 inspection surface.

Requirements:
- 3 to 5 independent held-out case classes;
- explicit expected failure/stop conditions;
- state what evidence would justify AI_CONTINUE, HOLD, or HUMAN escalation;
- preserve the doctrine that 0 observed defects is not a 0% defect-rate claim;
- no implementation and no authority expansion.

Keep the final answer compact and use exactly these headings: PLAN, CASES, STOP, EVIDENCE.
EOF
)

run_one() {
  local name="$1"
  local prompt="$2"
  local jsonl="$RESULTS/$name.jsonl"
  local stderr_log="$RESULTS/$name.stderr.log"
  local final_txt="$RESULTS/$name.final.txt"
  local meta="$RESULTS/$name.meta.json"
  local started ended rc

  started="$(date +%s)"
  echo "=== $name ==="
  set +e
  codex "${COMMON[@]}" --output-last-message "$final_txt" "$prompt" >"$jsonl" 2>"$stderr_log"
  rc=$?
  set -e
  ended="$(date +%s)"

  python3 - "$meta" "$name" "$started" "$ended" "$rc" "$CODEX_VERSION" "$GIT_HEAD" "$CODEX_BENCH_MODEL" <<'PY'
import json, sys
path, name, started, ended, rc, version, git_head, requested_model = sys.argv[1:]
out = {
    "name": name,
    "started_epoch": int(started),
    "ended_epoch": int(ended),
    "wall_seconds": int(ended) - int(started),
    "exit_code": int(rc),
    "codex_version": version,
    "git_head": git_head,
    "requested_model": requested_model or None,
}
with open(path, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
    f.write("\n")
PY

  if [[ $rc -ne 0 ]]; then
    echo "WARN: $name exited $rc; preserved JSONL/stderr for diagnosis" >&2
  fi
  return 0
}

# Fresh ephemeral runs isolate RTS externalized reuse from resumed-session replay effects.
run_one cold "$COLD_PROMPT"
run_one reuse "$REUSE_PROMPT"
run_one next "$NEXT_PROMPT"

python3 "$EXP/aggregate.py" --results-dir "$RESULTS" --reference-tokens "$REFERENCE_TOKENS" | tee "$RESULTS/summary.stdout.json"

echo
echo "Summary: $RESULTS/summary.json"
echo "Final answers: $RESULTS/{cold,reuse,next}.final.txt"
echo "Raw JSONL: $RESULTS/{cold,reuse,next}.jsonl"

name: RTS Sessions Rollup (Chain-Safe)

on:
  workflow_dispatch:
    inputs:
      month:
        description: "Target month (YYYY-MM). Empty = current UTC month"
        required: false
      day:
        description: "Optional day tag (YYYYMMDD). Empty = auto"
        required: false
  schedule:
    # every 30 minutes
    - cron: "*/30 * * * *"

permissions:
  contents: write

concurrency:
  group: rts-sessions-rollup-main
  cancel-in-progress: true

jobs:
  rollup:
    runs-on: ubuntu-latest
    timeout-minutes: 8

    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Resolve target month/day (UTC)
        shell: bash
        run: |
          set -euo pipefail

          # 1) Prefer workflow_dispatch inputs
          IN_MONTH="${{ github.event.inputs.month }}"
          IN_DAY="${{ github.event.inputs.day }}"

          # 2) Fallback: current UTC month
          if [ -z "${IN_MONTH}" ]; then
            IN_MONTH="$(date -u +"%Y-%m")"
          fi

          # 3) Day is optional
          if [ -z "${IN_DAY}" ]; then
            IN_DAY=""
          fi

          echo "SESSION_MONTH=${IN_MONTH}" >> "$GITHUB_ENV"
          echo "SESSION_DAY=${IN_DAY}" >> "$GITHUB_ENV"

          echo "[info] SESSION_MONTH=${IN_MONTH}"
          echo "[info] SESSION_DAY=${IN_DAY}"

      - name: Rollup monthly index (chain-safe, allow DEGRADED=3)
        shell: bash
        run: |
          set -o pipefail

          echo "[info] Running session_rollup.py (month=$SESSION_MONTH day=$SESSION_DAY)"

          # IMPORTANT:
          # We must capture exit code without failing the step early.
          set +e
          if [ -n "${SESSION_DAY:-}" ]; then
            python scripts/session_rollup.py "$SESSION_MONTH" "$SESSION_DAY"
          else
            python scripts/session_rollup.py "$SESSION_MONTH"
          fi
          rc=$?
          set -e

          echo "[info] session_rollup exit code: $rc"

          # B policy:
          # 3 = DEGRADED (ledger issues present) -> continue chain (success)
          if [ "$rc" -eq 3 ]; then
            echo "[warn] Ledger integrity DEGRADED (exit 3). Continuing pipeline."
            exit 0
          fi

          # Any other non-zero = real failure
          if [ "$rc" -ne 0 ]; then
            echo "[error] session_rollup failed with exit code $rc"
            exit "$rc"
          fi

          echo "[info] session_rollup completed successfully."

      - name: Commit rollup outputs (if changed)
        shell: bash
        run: |
          set -euo pipefail

          git config user.name "rts-bot"
          git config user.email "rts-bot@users.noreply.github.com"

          # add only generated targets (safe)
          git add "sessions/${SESSION_MONTH}/index.json" \
                  "sessions/${SESSION_MONTH}/index.md" \
                  "sessions/${SESSION_MONTH}/index_snapshot.json" \
                  "sessions/${SESSION_MONTH}/index_snapshot.md" || true

          # evidence snapshots may be written when breakpoint triggers
          git add "incidents/evidence_snapshots/" || true

          if git diff --cached --quiet; then
            echo "[ok] no changes to commit"
            exit 0
          fi

          git commit -m "sessions: rollup ${SESSION_MONTH} (chain-safe)"

      - name: Push
        if: success()
        shell: bash
        run: |
          set -euo pipefail
          git push

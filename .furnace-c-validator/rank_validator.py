from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess
import sys
from typing import Any

from datasets import disable_progress_bars, load_dataset

ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "ULTIMATE_LOOP_RECONSTRUCTION_FURNACE_20260818"
sys.path.insert(0, str(EXPERIMENT))
import stage0_control  # noqa: E402
import task_envelope  # noqa: E402


DATASET_REPO = "SWE-bench-Live/MultiLang"
DATASET_REVISION = "608f7ae9ab8ea1f9f0d030fe04562cf6bd1a0c8b"
EVALUATOR_REVISION = "70ec57e852e3f2d195790fe71f553e272c691833"
SEED_SHA256 = "050b40668443f667bcc5eabb7ff6c0ea3db5f2e962ac2178ce8e95d4e9e7921b"


class RankValidatorError(RuntimeError):
    pass


def _dump(path: pathlib.Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def _eval_once(*, evaluator_root: pathlib.Path, row_path: pathlib.Path, private_root: pathlib.Path, run_no: int) -> bool:
    out = private_root / f"run-{run_no}"
    out.mkdir(parents=True, exist_ok=True)
    log = out / "private.log"
    cmd = [
        sys.executable,
        "evaluation/evaluation.py",
        "--dataset", str(row_path.resolve()),
        "--patch_dir", "gold",
        "--platform", "linux",
        "--workers", "1",
        "--output_dir", str(out.resolve()),
        "--overwrite", "1",
    ]
    try:
        with log.open("wb") as fh:
            proc = subprocess.run(cmd, cwd=evaluator_root, stdout=fh, stderr=subprocess.STDOUT, check=False, timeout=170 * 60)
    except (OSError, subprocess.TimeoutExpired):
        return False
    if proc.returncode != 0:
        return False
    results_path = out / "results.json"
    if not results_path.exists():
        return False
    try:
        result = json.loads(results_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return (
        result.get("submitted") == 1
        and result.get("success") == 1
        and result.get("failure") == 0
        and result.get("error") == 0
        and result.get("incomplete") == 0
        and result.get("empty_patch") == 0
    )


def run(*, rank: int, evaluator_root: pathlib.Path, output_root: pathlib.Path) -> int:
    if rank < 1:
        raise RankValidatorError("rank must be >= 1")
    disable_progress_bars()
    rows = [dict(row) for row in load_dataset(DATASET_REPO, split="c", revision=DATASET_REVISION)]
    ordered = stage0_control.candidate_order(rows, split="c", seed_sha256=SEED_SHA256)
    if rank > len(ordered):
        raise RankValidatorError("rank outside dataset")
    row = ordered[rank - 1]

    private = output_root / ".private" / f"rank-{rank}"
    safe = output_root / "safe" / f"rank-{rank}"
    private.mkdir(parents=True, exist_ok=True)
    safe.mkdir(parents=True, exist_ok=True)
    row_path = private / "candidate.jsonl"
    row_path.write_text(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

    passes = sum(
        1 for run_no in (1, 2, 3)
        if _eval_once(evaluator_root=evaluator_root, row_path=row_path, private_root=private, run_no=run_no)
    )

    summary: dict[str, Any] = {
        "schema_version": "ultimate-loop-reconstruction-furnace/c-rank-validator-v1",
        "split": "c",
        "candidate_rank": rank,
        "gold_validation_runs": 3,
        "gold_validation_passes": passes,
        "dataset_revision": DATASET_REVISION,
        "evaluator_revision": EVALUATOR_REVISION,
        "solver_gold_access": False,
        "solver_dataset_access": False,
        "state": "GOLD_NOT_REPRODUCIBLE",
    }

    if passes == 3:
        task_id = stage0_control.opaque_task_id(
            instance_id=str(row["instance_id"]),
            seed_sha256=SEED_SHA256,
            ordinal=1,
        )
        try:
            envelope = task_envelope.sanitize_for_solver(
                row,
                opaque_task_id=task_id,
                task_valid=True,
                platform="linux",
            )
        except task_envelope.TaskPublicInputError:
            summary["state"] = "GOLD_VALID_BUT_BLIND_INPUT_UNUSABLE"
        else:
            task_envelope.verify_solver_envelope(envelope)
            if task_envelope.forbidden_key_scan(envelope):
                raise RankValidatorError("forbidden field leaked to solver envelope")
            _dump(safe / "solver-envelope.json", envelope)
            summary.update(
                {
                    "state": "ADMITTED_3_OF_3",
                    "task_id": task_id,
                    "solver_envelope_sha256": hashlib.sha256(
                        json.dumps(envelope, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
                    ).hexdigest(),
                }
            )

    _dump(safe / "summary.json", summary)
    print(f"SAFE_C_RANK_VALIDATOR rank={rank} state={summary['state']} passes={passes}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rank", type=int, required=True)
    parser.add_argument("--evaluator-root", required=True)
    parser.add_argument("--output-root", required=True)
    args = parser.parse_args()
    return run(rank=args.rank, evaluator_root=pathlib.Path(args.evaluator_root).resolve(), output_root=pathlib.Path(args.output_root).resolve())


if __name__ == "__main__":
    raise SystemExit(main())

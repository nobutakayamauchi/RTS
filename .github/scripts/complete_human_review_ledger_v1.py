"""Complete RTS-FRZ-000009 through VERIFIED and COMPLETED.

Temporary candidate helper. Remove before merge.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import freezer.cli as freezer_cli
from governed_loop.common import pretty_json
from governed_loop.generation import generate_run

ITEM_ID = "RTS-FRZ-000009"
VERIFIED_AT = "2026-07-26T05:10:00Z"
COMPLETED_AT = "2026-07-26T05:11:00Z"


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def revise(status: str, at: str) -> dict[str, object]:
    source = ROOT / f".{ITEM_ID.lower()}-{status.lower()}.json"
    write_json(source, {"status": status})
    freezer_cli.utc_now = lambda: at
    try:
        return freezer_cli.revise_item(ROOT, ITEM_ID, source)
    finally:
        source.unlink(missing_ok=True)


def update_governed_test() -> None:
    path = ROOT / "tests/test_governed_loop.py"
    text = path.read_text(encoding="utf-8")
    old = '''        self.assertEqual(loop["active_item_ids"], ["RTS-FRZ-000009"])
        self.assertEqual(loop["wip_count"], 1)
        self.assertEqual(loop["state"], "FOCUS")
        self.assertEqual(loop["recommendation_action"], "CONTINUE_OR_VERIFY_ACTIVE_ITEM")
        self.assertEqual(loop["recommendation_item_id"], "RTS-FRZ-000009")
'''
    new = '''        self.assertEqual(loop["active_item_ids"], [])
        self.assertEqual(loop["wip_count"], 0)
        self.assertEqual(loop["state"], "NORMAL")
        self.assertEqual(loop["recommendation_action"], "REQUEST_HUMAN_APPROVAL")
        self.assertEqual(loop["recommendation_item_id"], "RTS-FRZ-000003")
'''
    if text.count(old) != 1:
        raise RuntimeError("governed-loop lifecycle assertion anchor mismatch")
    path.write_text(text.replace(old, new), encoding="utf-8")


def write_completion_doc() -> None:
    path = ROOT / "docs/implementation/HUMAN_REVIEW_LEDGER_V1_COMPLETION_TASK.md"
    path.write_text(
        "# Human Review Ledger v1 Completion\n\n"
        "## Lifecycle\n\n"
        "```text\n"
        "v001 FROZEN / NOT_APPROVED\n"
        "v002 SELECTED / APPROVED\n"
        "v003 IN_PROGRESS / APPROVED\n"
        "v004 VERIFIED / APPROVED\n"
        "v005 COMPLETED / APPROVED\n"
        "```\n\n"
        "## Completion evidence\n\n"
        "- implementation PR: `#254`\n"
        "- implementation merge commit: `8850649649101ac8857f7edf8c5932743d85353d`\n"
        "- final implementation head: `4d917cac0afdfa6d75251e9e014045886e768e9c`\n"
        "- final PR checks: `FREEZER Tests / success`, `Unicode Guard / success`\n"
        "- independent review findings fixed: governed proposer identity linkage, ordinary expiry evaluation, and rejection of unmanifested decision files\n"
        "- committed ledger remains empty and non-authorizing: `NO_DECISIONS / NOT_APPROVED / NOT_APPLIED`\n\n"
        "## Preserved boundary\n\n"
        "Completion does not create a reviewer identity or decision and grants no Skill application, mutation, merge, adjacent-repository write, provider, scheduler, network, subprocess, publication, deployment, messaging, or external-action authority.\n",
        encoding="utf-8",
    )


def main() -> None:
    verified = revise("VERIFIED", VERIFIED_AT)
    completed = revise("COMPLETED", COMPLETED_AT)
    update_governed_test()
    run = generate_run(ROOT)
    (ROOT / "governed_loop/runs/current.json").write_text(pretty_json(run), encoding="utf-8")
    write_completion_doc()
    print(verified["version"], verified["status"])
    print(completed["version"], completed["status"])
    print(run["run_id"])


if __name__ == "__main__":
    main()

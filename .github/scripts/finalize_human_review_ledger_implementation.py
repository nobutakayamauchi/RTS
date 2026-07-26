"""Integrate Human Review Ledger v1 into the governed one-shot loop.

Temporary candidate helper. Remove before merge.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"expected one anchor in {path}, found {count}: {old[:80]!r}")
    path.write_text(text.replace(old, new), encoding="utf-8")


def replace_exact_count(path: Path, old: str, new: str, expected: int) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != expected:
        raise RuntimeError(f"expected {expected} anchors in {path}, found {count}: {old[:80]!r}")
    path.write_text(text.replace(old, new), encoding="utf-8")


def update_generation() -> None:
    path = ROOT / "governed_loop/generation.py"
    replace_once(
        path,
        "from execution_controller.cli import command_verify as verify_execution_controller\n",
        "from execution_controller.cli import command_verify as verify_execution_controller\n"
        "from human_review_ledger.corpus import verify_all as verify_human_review_ledger\n",
    )
    replace_once(
        path,
        '    "governed_loop/schemas/loop_run.schema.json",\n',
        '    "governed_loop/schemas/loop_run.schema.json",\n'
        '    "human_review_ledger/policy/v1.json",\n'
        '    "human_review_ledger/reviewer_scopes/default.json",\n'
        '    "human_review_ledger/ledger/manifest.json",\n'
        '    "human_review_ledger/ledger/current.json",\n'
        '    "human_review_ledger/schemas/decision.schema.json",\n'
        '    "human_review_ledger/schemas/policy.schema.json",\n'
        '    "human_review_ledger/schemas/reviewer_scope.schema.json",\n'
        '    "human_review_ledger/schemas/manifest.schema.json",\n'
        '    "human_review_ledger/schemas/current_summary.schema.json",\n',
    )
    replace_once(
        path,
        "    proposal = verify_learning_proposals(root)\n    return {\n",
        "    proposal = verify_learning_proposals(root)\n"
        "    human_review = verify_human_review_ledger(root)\n"
        "    return {\n",
    )
    replace_once(
        path,
        '        "proposal_summary": proposal,\n',
        '        "proposal_summary": proposal,\n'
        '        "human_review_summary": human_review,\n',
    )
    replace_once(
        path,
        '    proposal = sources["proposal_summary"]\n\n',
        '    proposal = sources["proposal_summary"]\n'
        '    human_review = sources["human_review_summary"]\n\n',
    )
    proposal_block = '''            "learning_proposal": {
                "verification": "PASSED",
                "proposal_id": proposal["proposal_id"],
                "proposal_fingerprint": proposal["proposal_fingerprint"],
                "proposal_status": proposal["proposal_status"],
                "review_status": proposal["review_status"],
                "recommendation": proposal["recommendation"],
                "approval_status": proposal["approval_status"],
                "application_status": proposal["application_status"],
            },
'''
    ledger_block = proposal_block + '''            "human_review_ledger": {
                "verification": "PASSED",
                "ledger_id": human_review["ledger_id"],
                "record_count": human_review["record_count"],
                "state": human_review["state"],
                "current_decision_id": human_review["current_decision_id"],
                "current_decision_type": human_review["current_decision_type"],
                "current_decision_fingerprint": human_review["current_decision_fingerprint"],
                "approval_status": human_review["approval_status"],
                "application_status": human_review["application_status"],
                "stale": human_review["stale"],
                "expired": human_review["expired"],
                "policy_fingerprint": human_review["policy_fingerprint"],
                "reviewer_scope_fingerprint": human_review["reviewer_scope_fingerprint"],
                "manifest_fingerprint": human_review["manifest_fingerprint"],
                "summary_fingerprint": human_review["summary_fingerprint"],
            },
'''
    replace_once(path, proposal_block, ledger_block)
    replace_once(
        path,
        "all six repository-local component verification stages passed in the fixed governed order",
        "all seven repository-local component verification stages passed in the fixed governed order",
    )
    replace_once(
        path,
        '                "the learning proposal and pending review remain reconstructable from exact committed sources",\n',
        '                "the learning proposal and pending review remain reconstructable from exact committed sources",\n'
        '                "the Human Review Ledger verifies as an empty non-authorizing append-only ledger with no manufactured human decision",\n',
    )


def update_models() -> None:
    path = ROOT / "governed_loop/models.py"
    replace_once(
        path,
        '    "learning_proposals",\n]',
        '    "learning_proposals",\n    "human_review_ledger",\n]',
    )
    replace_once(
        path,
        '    "learning_proposal",\n}',
        '    "learning_proposal",\n    "human_review_ledger",\n}',
    )
    anchor = '    _sha256(proposal["proposal_fingerprint"], field="proposal_fingerprint")\n\n    evidence = exact_object('
    ledger_validation = '''    _sha256(proposal["proposal_fingerprint"], field="proposal_fingerprint")

    ledger = exact_object(
        components["human_review_ledger"],
        {
            "verification",
            "ledger_id",
            "record_count",
            "state",
            "current_decision_id",
            "current_decision_type",
            "current_decision_fingerprint",
            "approval_status",
            "application_status",
            "stale",
            "expired",
            "policy_fingerprint",
            "reviewer_scope_fingerprint",
            "manifest_fingerprint",
            "summary_fingerprint",
        },
        field="components.human_review_ledger",
    )
    if ledger["verification"] != "PASSED":
        raise GovernedLoopError("human review ledger verification did not pass")
    if ledger["ledger_id"] != "RTS-HUMAN-REVIEW-LEDGER-000001":
        raise GovernedLoopError("human review ledger identifier mismatch")
    record_count = _integer(ledger["record_count"], field="human review record_count")
    if ledger["application_status"] != "NOT_APPLIED":
        raise GovernedLoopError("human review ledger application authority widened")
    for field in ("stale", "expired"):
        if not isinstance(ledger[field], bool):
            raise GovernedLoopError(f"human review ledger {field} must be boolean")
    for field in (
        "policy_fingerprint",
        "reviewer_scope_fingerprint",
        "manifest_fingerprint",
        "summary_fingerprint",
    ):
        _sha256(ledger[field], field=f"human review ledger {field}")
    if record_count == 0:
        if (
            ledger["state"] != "NO_DECISIONS"
            or ledger["current_decision_id"] is not None
            or ledger["current_decision_type"] is not None
            or ledger["current_decision_fingerprint"] is not None
            or ledger["approval_status"] != "NOT_APPROVED"
            or ledger["stale"] is not False
            or ledger["expired"] is not False
        ):
            raise GovernedLoopError("empty human review ledger boundary widened")
    else:
        if not isinstance(ledger["current_decision_id"], str) or not ledger["current_decision_id"]:
            raise GovernedLoopError("human review current_decision_id is required")
        if ledger["current_decision_type"] not in {
            "APPROVE", "REJECT", "RETURN_FOR_REVISION", "EXPIRE", "SUPERSEDE"
        }:
            raise GovernedLoopError("human review current_decision_type mismatch")
        _sha256(
            ledger["current_decision_fingerprint"],
            field="human review current_decision_fingerprint",
        )
        if ledger["approval_status"] not in {"APPROVED", "NOT_APPROVED"}:
            raise GovernedLoopError("human review approval status mismatch")
        if (ledger["stale"] or ledger["expired"]) and ledger["approval_status"] != "NOT_APPROVED":
            raise GovernedLoopError("stale or expired human review evidence remained approved")

    evidence = exact_object('''
    replace_once(path, anchor, ledger_validation)


def update_schema() -> None:
    path = ROOT / "governed_loop/schemas/loop_run.schema.json"
    schema = json.loads(path.read_text(encoding="utf-8"))
    order = schema["properties"]["verification_order"]["const"]
    if "human_review_ledger" not in order:
        order.append("human_review_ledger")
    components = schema["properties"]["components"]
    if "human_review_ledger" not in components["required"]:
        components["required"].append("human_review_ledger")
    components["properties"]["human_review_ledger"] = {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "verification", "ledger_id", "record_count", "state",
            "current_decision_id", "current_decision_type", "current_decision_fingerprint",
            "approval_status", "application_status", "stale", "expired",
            "policy_fingerprint", "reviewer_scope_fingerprint",
            "manifest_fingerprint", "summary_fingerprint",
        ],
        "properties": {
            "verification": {"const": "PASSED"},
            "ledger_id": {"const": "RTS-HUMAN-REVIEW-LEDGER-000001"},
            "record_count": {"type": "integer", "minimum": 0},
            "state": {"enum": ["NO_DECISIONS", "CURRENT_DECISION", "STALE_DECISION", "EXPIRED_DECISION"]},
            "current_decision_id": {"type": ["string", "null"]},
            "current_decision_type": {"type": ["string", "null"]},
            "current_decision_fingerprint": {"type": ["string", "null"], "pattern": "^[0-9a-f]{64}$"},
            "approval_status": {"enum": ["APPROVED", "NOT_APPROVED"]},
            "application_status": {"const": "NOT_APPLIED"},
            "stale": {"type": "boolean"},
            "expired": {"type": "boolean"},
            "policy_fingerprint": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
            "reviewer_scope_fingerprint": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
            "manifest_fingerprint": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
            "summary_fingerprint": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        },
    }
    path.write_text(json.dumps(schema, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def update_governed_tests() -> None:
    path = ROOT / "tests/test_governed_loop.py"
    replace_once(
        path,
        '        self.assertEqual(loop["recommendation_item_id"], "RTS-FRZ-000009")\n        self.assertTrue(run["authority"]["read_only"])\n',
        '        self.assertEqual(loop["recommendation_item_id"], "RTS-FRZ-000009")\n'
        '        ledger = run["components"]["human_review_ledger"]\n'
        '        self.assertEqual(ledger["record_count"], 0)\n'
        '        self.assertEqual(ledger["state"], "NO_DECISIONS")\n'
        '        self.assertEqual(ledger["approval_status"], "NOT_APPROVED")\n'
        '        self.assertEqual(ledger["application_status"], "NOT_APPLIED")\n'
        '        self.assertTrue(run["authority"]["read_only"])\n',
    )
    replace_once(
        path,
        '    def test_proposal_remains_pending_and_not_applied(self) -> None:\n',
        '    def test_human_review_application_authority_cannot_widen(self) -> None:\n'
        '        run = generate_run(self.root)\n'
        '        run["components"]["human_review_ledger"]["application_status"] = "APPLIED"\n'
        '        self.resign(run)\n'
        '        with self.assertRaisesRegex(GovernedLoopError, "application authority widened"):\n'
        '            validate_record(run)\n\n'
        '    def test_proposal_remains_pending_and_not_applied(self) -> None:\n',
    )


def update_workflow() -> None:
    path = ROOT / ".github/workflows/freezer-tests.yml"
    replace_exact_count(
        path,
        '      - "learning_proposals/**"\n',
        '      - "learning_proposals/**"\n      - "human_review_ledger/**"\n',
        2,
    )
    replace_exact_count(
        path,
        '      - "tests/test_learning_proposals.py"\n',
        '      - "tests/test_learning_proposals.py"\n      - "tests/test_human_review_ledger.py"\n',
        2,
    )
    replace_exact_count(
        path,
        '      - "docs/implementation/PROPOSAL_ONLY_OUTCOME_LEARNING_V1_TASK.md"\n',
        '      - "docs/implementation/PROPOSAL_ONLY_OUTCOME_LEARNING_V1_TASK.md"\n'
        '      - "docs/implementation/HUMAN_REVIEW_LEDGER_V1_TASK.md"\n',
        2,
    )
    replace_exact_count(
        path,
        "          python -m learning_proposals.cli verify\n",
        "          python -m learning_proposals.cli verify\n"
        "          python -m human_review_ledger.cli verify\n",
        2,
    )
    replace_once(
        path,
        "      - name: Run governed-loop tests\n",
        "      - name: Run human-review-ledger tests\n"
        "        run: python -B -m unittest discover -s tests -p 'test_human_review_ledger.py' -v\n"
        "      - name: Run governed-loop tests\n",
    )


def update_readme() -> None:
    path = ROOT / "governed_loop/README.md"
    replace_once(
        path,
        "6. Proposal-Only Outcome Learning\n",
        "6. Proposal-Only Outcome Learning\n7. Human Review Ledger\n",
    )
    replace_once(
        path,
        "The controller stage uses its bounded local self-verification.",
        "The Human Review Ledger stage verifies append-only human-review evidence and remains non-authorizing. The controller stage uses its bounded local self-verification.",
    )


def regenerate_run() -> None:
    from governed_loop.common import pretty_json
    from governed_loop.generation import generate_run

    run = generate_run(ROOT)
    (ROOT / "governed_loop/runs/current.json").write_text(pretty_json(run), encoding="utf-8")
    print(run["run_id"], run["run_fingerprint"])


if __name__ == "__main__":
    update_generation()
    update_models()
    update_schema()
    update_governed_tests()
    update_workflow()
    update_readme()
    regenerate_run()

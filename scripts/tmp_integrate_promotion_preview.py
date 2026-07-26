#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace(path: str, before: str, after: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    if before not in text:
        if after in text:
            return
        raise RuntimeError(f"expected integration anchor missing: {path}: {before[:80]!r}")
    target.write_text(text.replace(before, after), encoding="utf-8")


def update_generation() -> None:
    replace(
        "governed_loop/generation.py",
        "from outcome_evidence.corpus import corpus_summary, load_corpus\nfrom skill_regression.corpus import verify_all as verify_skill_regression\n",
        "from outcome_evidence.corpus import corpus_summary, load_corpus\nfrom promotion_application_preview.corpus import verify_all as verify_promotion_application_preview\nfrom skill_regression.corpus import verify_all as verify_skill_regression\n",
    )
    replace(
        "governed_loop/generation.py",
        '    "learning_proposals/reviews/feature-build-v1.pending.json",\n)',
        '    "learning_proposals/reviews/feature-build-v1.pending.json",\n    "promotion_application_preview/schemas/preview.schema.json",\n    "promotion_application_preview/previews/current.json",\n)',
    )
    replace(
        "governed_loop/generation.py",
        "    proposal = verify_learning_proposals(root)\n    human_review = verify_human_review_ledger(root)\n",
        "    proposal = verify_learning_proposals(root)\n    human_review = verify_human_review_ledger(root)\n    promotion_preview = verify_promotion_application_preview(root)\n",
    )
    replace(
        "governed_loop/generation.py",
        '        "human_review_summary": human_review,\n    }',
        '        "human_review_summary": human_review,\n        "promotion_preview_summary": promotion_preview,\n    }',
    )
    replace(
        "governed_loop/generation.py",
        '    human_review = sources["human_review_summary"]\n\n    outcome_links = [',
        '    human_review = sources["human_review_summary"]\n    promotion_preview = sources["promotion_preview_summary"]\n\n    outcome_links = [',
    )
    replace(
        "governed_loop/generation.py",
        '            "human_review_ledger": {\n                "verification": "PASSED",\n                "ledger_id": human_review["ledger_id"],\n                "record_count": human_review["record_count"],\n                "state": human_review["state"],\n                "current_decision_id": human_review["current_decision_id"],\n                "current_decision_type": human_review["current_decision_type"],\n                "current_decision_fingerprint": human_review["current_decision_fingerprint"],\n                "approval_status": human_review["approval_status"],\n                "application_status": human_review["application_status"],\n                "stale": human_review["stale"],\n                "expired": human_review["expired"],\n                "policy_fingerprint": human_review["policy_fingerprint"],\n                "reviewer_scope_fingerprint": human_review["reviewer_scope_fingerprint"],\n                "manifest_fingerprint": human_review["manifest_fingerprint"],\n                "summary_fingerprint": human_review["summary_fingerprint"],\n            },\n',
        '            "human_review_ledger": {\n                "verification": "PASSED",\n                "ledger_id": human_review["ledger_id"],\n                "record_count": human_review["record_count"],\n                "state": human_review["state"],\n                "current_decision_id": human_review["current_decision_id"],\n                "current_decision_type": human_review["current_decision_type"],\n                "current_decision_fingerprint": human_review["current_decision_fingerprint"],\n                "approval_status": human_review["approval_status"],\n                "application_status": human_review["application_status"],\n                "stale": human_review["stale"],\n                "expired": human_review["expired"],\n                "policy_fingerprint": human_review["policy_fingerprint"],\n                "reviewer_scope_fingerprint": human_review["reviewer_scope_fingerprint"],\n                "manifest_fingerprint": human_review["manifest_fingerprint"],\n                "summary_fingerprint": human_review["summary_fingerprint"],\n            },\n            "promotion_application_preview": {\n                "verification": "PASSED",\n                "preview_id": promotion_preview["preview_id"],\n                "preview_fingerprint": promotion_preview["preview_fingerprint"],\n                "state": promotion_preview["state"],\n                "blocker_count": promotion_preview["blocker_count"],\n                "approval_status": promotion_preview["approval_status"],\n                "application_status": promotion_preview["application_status"],\n                "target_write_authorized": promotion_preview["target_write_authorized"],\n                "adjacent_repository_write_authorized": promotion_preview["adjacent_repository_write_authorized"],\n            },\n',
    )
    replace(
        "governed_loop/generation.py",
        '                "all seven repository-local component verification stages passed in the fixed governed order",',
        '                "all eight repository-local component verification stages passed in the fixed governed order",',
    )
    replace(
        "governed_loop/generation.py",
        '                "the Human Review Ledger verifies as an empty non-authorizing append-only ledger with no manufactured human decision",\n',
        '                "the Human Review Ledger verifies as an empty non-authorizing append-only ledger with no manufactured human decision",\n                "the Promotion Application Preview verifies as BLOCKED and non-applying with exact target and rollback hashes",\n',
    )


def update_models() -> None:
    replace(
        "governed_loop/models.py",
        '    "human_review_ledger",\n]',
        '    "human_review_ledger",\n    "promotion_application_preview",\n]',
    )
    replace(
        "governed_loop/models.py",
        '    "human_review_ledger",\n}',
        '    "human_review_ledger",\n    "promotion_application_preview",\n}',
    )
    anchor = '    evidence = exact_object(record["evidence_summary"], EVIDENCE_FIELDS, field="evidence_summary")\n'
    block = '''    preview = exact_object(
        components["promotion_application_preview"],
        {
            "verification",
            "preview_id",
            "preview_fingerprint",
            "state",
            "blocker_count",
            "approval_status",
            "application_status",
            "target_write_authorized",
            "adjacent_repository_write_authorized",
        },
        field="components.promotion_application_preview",
    )
    if (
        preview["verification"] != "PASSED"
        or preview["state"] != "BLOCKED"
        or preview["approval_status"] != "NOT_APPROVED"
        or preview["application_status"] != "NOT_APPLIED"
        or preview["target_write_authorized"] is not False
        or preview["adjacent_repository_write_authorized"] is not False
    ):
        raise GovernedLoopError("promotion application preview authority widened")
    if not isinstance(preview["preview_id"], str) or not preview["preview_id"]:
        raise GovernedLoopError("promotion application preview identifier is required")
    _sha256(preview["preview_fingerprint"], field="promotion preview fingerprint")
    _integer(preview["blocker_count"], field="promotion preview blocker_count", minimum=1)

'''
    replace("governed_loop/models.py", anchor, block + anchor)


def update_schema() -> None:
    path = ROOT / "governed_loop/schemas/loop_run.schema.json"
    schema = json.loads(path.read_text(encoding="utf-8"))
    order = schema["properties"]["verification_order"]["const"]
    if "promotion_application_preview" not in order:
        order.append("promotion_application_preview")
    components = schema["properties"]["components"]
    if "promotion_application_preview" not in components["required"]:
        components["required"].append("promotion_application_preview")
    components["properties"]["promotion_application_preview"] = {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "verification", "preview_id", "preview_fingerprint", "state",
            "blocker_count", "approval_status", "application_status",
            "target_write_authorized", "adjacent_repository_write_authorized",
        ],
        "properties": {
            "verification": {"const": "PASSED"},
            "preview_id": {"type": "string", "minLength": 1},
            "preview_fingerprint": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
            "state": {"const": "BLOCKED"},
            "blocker_count": {"type": "integer", "minimum": 1},
            "approval_status": {"const": "NOT_APPROVED"},
            "application_status": {"const": "NOT_APPLIED"},
            "target_write_authorized": {"const": False},
            "adjacent_repository_write_authorized": {"const": False},
        },
    }
    path.write_text(json.dumps(schema, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def update_tests() -> None:
    replace(
        "tests/test_governed_loop.py",
        '        self.assertEqual(ledger["application_status"], "NOT_APPLIED")\n        self.assertTrue(run["authority"]["read_only"])',
        '        self.assertEqual(ledger["application_status"], "NOT_APPLIED")\n        preview = run["components"]["promotion_application_preview"]\n        self.assertEqual(preview["state"], "BLOCKED")\n        self.assertGreaterEqual(preview["blocker_count"], 1)\n        self.assertEqual(preview["application_status"], "NOT_APPLIED")\n        self.assertFalse(preview["target_write_authorized"])\n        self.assertFalse(preview["adjacent_repository_write_authorized"])\n        self.assertTrue(run["authority"]["read_only"])',
    )
    replace(
        "tests/test_governed_loop.py",
        '    def test_proposal_remains_pending_and_not_applied(self) -> None:\n',
        '    def test_promotion_preview_authority_cannot_widen(self) -> None:\n        run = generate_run(self.root)\n        run["components"]["promotion_application_preview"]["target_write_authorized"] = True\n        self.resign(run)\n        with self.assertRaisesRegex(GovernedLoopError, "promotion application preview authority widened"):\n            validate_record(run)\n\n    def test_proposal_remains_pending_and_not_applied(self) -> None:\n',
    )


def main() -> None:
    update_generation()
    update_models()
    update_schema()
    update_tests()
    from governed_loop.common import pretty_json
    from governed_loop.generation import generate_run

    (ROOT / "governed_loop/runs/current.json").write_text(
        pretty_json(generate_run(ROOT)), encoding="utf-8"
    )


if __name__ == "__main__":
    main()

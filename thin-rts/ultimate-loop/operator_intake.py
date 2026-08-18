from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

SCHEMA = "ultimate-loop-knowledge-intake/v0"
REPORT_SCHEMA = "ultimate-loop-knowledge-intake-report/v0"
EXPECTED_SOURCE_TASKS = set(range(1, 101))
FORBIDDEN_UNIVERSAL_LITERALS = {
    "LINE",
    "UTAGE",
    "Lステップ",
    "YouTube",
    "Instagram",
    "TikTok",
    "Twitter",
    "Meta",
    "Stripe",
    "Calendly",
    "万円",
    "月商",
    "年商",
}
DEFINITION_FIELDS = (
    "id",
    "name",
    "purpose",
    "invariant",
    "inputs",
    "process",
    "outputs",
    "failure_signals",
)


def _strings(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from _strings(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from _strings(item)


def evaluate(pack: dict[str, Any]) -> dict[str, Any]:
    blocks: list[str] = []
    reasons: list[str] = []

    if pack.get("schema") != SCHEMA:
        blocks.append("INVALID_SCHEMA")

    if pack.get("authority_effect") != "NONE":
        blocks.append("AUTHORITY_EFFECT_NOT_NONE")
        reasons.append("Knowledge intake cannot authorize promotion or consequential action.")

    status = str(pack.get("status", ""))
    if "NON_CANONICAL" not in status:
        blocks.append("NON_CANONICAL_STATUS_MISSING")

    operators = pack.get("operators")
    if not isinstance(operators, list):
        operators = []
        blocks.append("OPERATORS_MISSING")

    if not 15 <= len(operators) <= 20:
        blocks.append("OPERATOR_COUNT_OUT_OF_BOUNDS")

    ids = [op.get("id") for op in operators if isinstance(op, dict)]
    if len(ids) != len(set(ids)) or any(not value for value in ids):
        blocks.append("OPERATOR_IDS_NOT_UNIQUE")

    chain = pack.get("execution_chain")
    if not isinstance(chain, list) or chain != ids:
        blocks.append("EXECUTION_CHAIN_MISMATCH")

    coverage: set[int] = set()
    for op in operators:
        if not isinstance(op, dict):
            blocks.append("INVALID_OPERATOR")
            continue

        for field in (
            "id", "name", "purpose", "invariant", "inputs", "process",
            "outputs", "failure_signals", "human_gate",
            "ultimate_loop_hooks", "source_tasks"
        ):
            if field not in op:
                blocks.append(f"OPERATOR_FIELD_MISSING:{op.get('id', 'UNKNOWN')}:{field}")

        source_tasks = op.get("source_tasks", [])
        if not isinstance(source_tasks, list):
            blocks.append(f"SOURCE_TASKS_INVALID:{op.get('id', 'UNKNOWN')}")
        else:
            for task in source_tasks:
                if isinstance(task, int) and 1 <= task <= 100:
                    coverage.add(task)
                else:
                    blocks.append(f"SOURCE_TASK_INVALID:{op.get('id', 'UNKNOWN')}:{task}")

        definition_text = "\n".join(
            _strings({field: op.get(field) for field in DEFINITION_FIELDS})
        )
        for literal in sorted(FORBIDDEN_UNIVERSAL_LITERALS):
            if literal in definition_text:
                blocks.append(f"DOMAIN_LITERAL_LEAK:{op.get('id', 'UNKNOWN')}:{literal}")

    missing = sorted(EXPECTED_SOURCE_TASKS - coverage)
    extra = sorted(coverage - EXPECTED_SOURCE_TASKS)
    if missing:
        blocks.append("SOURCE_COVERAGE_INCOMPLETE")
        reasons.append(f"Missing source tasks: {missing}")
    if extra:
        blocks.append("SOURCE_COVERAGE_OUT_OF_RANGE")

    operator_ids = set(ids)
    extensions = pack.get("candidate_extensions") or []
    for ext in extensions:
        ext_id = ext.get("id", "UNKNOWN") if isinstance(ext, dict) else "UNKNOWN"
        refs = ext.get("source_operators", []) if isinstance(ext, dict) else []
        unknown = sorted(set(refs) - operator_ids)
        if unknown:
            blocks.append(f"EXTENSION_UNKNOWN_OPERATOR:{ext_id}")
            reasons.append(f"{ext_id} references unknown operators: {unknown}")

    classification = "PASS" if not blocks else "UNKNOWN_OR_BLOCKED"
    return {
        "schema": REPORT_SCHEMA,
        "pack_id": pack.get("pack_id"),
        "classification": classification,
        "operator_count": len(operators),
        "source_task_coverage_count": len(coverage),
        "source_task_coverage_complete": coverage == EXPECTED_SOURCE_TASKS,
        "candidate_extension_count": len(extensions),
        "candidate_extension_ids": [
            ext.get("id") for ext in extensions if isinstance(ext, dict)
        ],
        "canonical_promotion_authorized": False,
        "blocking_states": sorted(set(blocks)),
        "reasons": reasons,
        "disposition": (
            "ADMIT_AS_CHALLENGER_KNOWLEDGE"
            if classification == "PASS"
            else "BLOCK_INTAKE"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate non-canonical operator knowledge before Ultimate Loop intake"
    )
    parser.add_argument("pack", type=Path)
    args = parser.parse_args()

    pack = json.loads(args.pack.read_text(encoding="utf-8"))
    report = evaluate(pack)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["classification"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())

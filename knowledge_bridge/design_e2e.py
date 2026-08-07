from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path

from .council import analyze_implementation_council
from .intent_translator import translate_intent


@dataclass(frozen=True)
class DesignE2EResult:
    request_id: str
    project_id: str
    knowledge_id: str
    bundle_path: str
    translation_path: str
    council_path: str
    summary_path: str
    recommendation: str
    implementation_strategy: str
    status: str
    human_decision_required: bool


def _synthetic_record(translation: dict) -> dict:
    feature_lines = [
        f"{item['decision']}: {item['feature']} — {item['reason']}"
        for item in translation.get("feature_decisions", [])
    ]
    reference_lines = []
    for item in translation.get("reference_ledger", []):
        reference_lines.extend(item.get("adopted", []))
        reference_lines.extend(item.get("rejected", []))
        reference_lines.extend(item.get("notes", []))
    body_parts = [
        *translation.get("inferred_goals", []),
        *translation.get("design_constraints", []),
        *feature_lines,
        *reference_lines,
        *translation.get("missing_parts", []),
    ]
    tags = [
        translation.get("domain", "unknown"),
        translation.get("role", "unknown"),
        "design-translation",
        "planned-map",
    ]
    return {
        "knowledge_id": translation["request_id"],
        "title": translation.get("title", "Untitled design translation"),
        "body": "\n".join(str(item) for item in body_parts if str(item).strip()),
        "tags": [item for item in tags if item and item != "unknown"],
        "frontmatter": {
            "project_id": translation["project_id"],
            "knowledge_type": "design_decision",
            "status": "translated",
            "human_review": "required",
            "rollback": "disable generated integration adapter",
            "test_plan": ["translation contract", "council report", "planned map integrity"],
            "acceptance_criteria": [
                "translation and council outputs share request and project identity",
                "no implementation is executed automatically",
            ],
        },
    }


def run_design_e2e(
    input_path: str | Path,
    repo_root: str | Path,
    output_dir: str | Path,
) -> DesignE2EResult:
    bundle = Path(output_dir).expanduser().resolve()
    if bundle.exists():
        raise FileExistsError(f"refusing to overwrite design E2E bundle: {bundle}")
    bundle.mkdir(parents=True)

    try:
        translation_path = bundle / "translation.json"
        translation = translate_intent(input_path, translation_path)
        translation_data = asdict(translation)
        knowledge_id = translation.request_id

        state = bundle / ".state"
        normalized = state / "normalized"
        challenges = state / "challenges"
        normalized.mkdir(parents=True)
        challenges.mkdir(parents=True)
        (normalized / f"{knowledge_id}.json").write_text(
            json.dumps(_synthetic_record(translation_data), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        (challenges / f"{knowledge_id}.json").write_text(
            json.dumps(
                {
                    "knowledge_id": knowledge_id,
                    "promotion_ready": True,
                    "gate_scope": "design_translation_complete_not_implementation_approved",
                    "human_decision_required": True,
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        council_path = bundle / "council.json"
        council = analyze_implementation_council(state, knowledge_id, repo_root, council_path)

        summary = {
            "schema_version": translation.schema_version,
            "request_id": translation.request_id,
            "project_id": translation.project_id,
            "knowledge_id": knowledge_id,
            "translation_status": translation.status,
            "council_status": council.status,
            "recommendation": council.recommendation,
            "implementation_strategy": council.implementation_strategy,
            "missing_parts": [asdict(item) for item in council.missing_parts],
            "insertion_candidates": list(council.insertion_candidates),
            "related_freezer_items": list(council.related_freezer_items),
            "human_questions": list(council.human_questions),
            "human_decision_required": True,
            "status": "AWAITING_HUMAN_DECISION",
            "implementation_executed": False,
        }
        summary_path = bundle / "summary.json"
        summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (bundle / "summary.md").write_text(
            _summary_markdown(translation_data, asdict(council), summary), encoding="utf-8"
        )
        shutil.rmtree(state)

        return DesignE2EResult(
            request_id=translation.request_id,
            project_id=translation.project_id,
            knowledge_id=knowledge_id,
            bundle_path=str(bundle),
            translation_path=str(translation_path),
            council_path=str(council_path),
            summary_path=str(summary_path),
            recommendation=council.recommendation,
            implementation_strategy=council.implementation_strategy,
            status="AWAITING_HUMAN_DECISION",
            human_decision_required=True,
        )
    except Exception:
        shutil.rmtree(bundle, ignore_errors=True)
        raise


def _summary_markdown(translation: dict, council: dict, summary: dict) -> str:
    missing = "\n".join(
        f"- **{item['category']} / {item['name']}**: {item['reason']}"
        for item in summary["missing_parts"]
    ) or "- None detected"
    candidates = "\n".join(f"- {item}" for item in summary["insertion_candidates"]) or "- No executable candidate"
    freezer = "\n".join(f"- {item}" for item in summary["related_freezer_items"]) or "- None"
    questions = "\n".join(f"- {item}" for item in summary["human_questions"]) or "- None"
    return f"""# Design E2E Discussion Bundle

## Identity

- Request: `{translation['request_id']}`
- Project: `{translation['project_id']}`
- Status: `AWAITING_HUMAN_DECISION`

## Translation outcome

- Title: {translation['title']}
- Domain: {translation['domain']}
- Target user: {translation['target_user']}
- Planned nodes: {len(translation['planned_structure']['nodes'])}
- Planned edges: {len(translation['planned_structure']['edges'])}

## Council outcome

- Recommendation: `{council['recommendation']}`
- Implementation strategy: `{council['implementation_strategy']}`
- Confidence: {council['confidence']:.2f}

## Missing parts

{missing}

## Executable insertion candidates

{candidates}

## Related FREEZER items

{freezer}

## Questions for human discussion

{questions}

No approval, code modification, or implementation was executed.
"""

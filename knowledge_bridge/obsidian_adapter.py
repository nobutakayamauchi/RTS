from __future__ import annotations

import json
import re
import shutil
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .design_e2e import run_design_e2e


@dataclass(frozen=True)
class ObsidianDesignResult:
    source_note: str
    request_id: str
    project_id: str
    review_note: str
    machine_record: str
    bundle_path: str
    status: str
    human_decision_required: bool


def _scalar(value: str) -> Any:
    text = value.strip()
    if not text:
        return ""
    if text.lower() in {"true", "false"}:
        return text.lower() == "true"
    if text.startswith("[") or text.startswith("{"):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
    if "," in text:
        return [item.strip() for item in text.split(",") if item.strip()]
    return text.strip('"\'')


def _frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end < 0:
        raise ValueError("unterminated Obsidian frontmatter")
    header = text[4:end]
    body = text[end + 5 :]
    result: dict[str, Any] = {}
    for number, line in enumerate(header.splitlines(), start=2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            raise ValueError(f"unsupported frontmatter at line {number}: {line}")
        key, value = line.split(":", 1)
        result[key.strip()] = _scalar(value)
    return result, body


def _section(body: str, names: tuple[str, ...]) -> list[str]:
    heading = "|".join(re.escape(name) for name in names)
    match = re.search(rf"(?ims)^#+\s*(?:{heading})\s*$\n(.*?)(?=^#+\s|\Z)", body)
    if not match:
        return []
    values: list[str] = []
    for line in match.group(1).splitlines():
        cleaned = re.sub(r"^\s*[-*+]\s+", "", line).strip()
        if cleaned:
            values.append(cleaned)
    return values


def note_to_translation_input(note_path: str | Path) -> dict[str, Any]:
    note = Path(note_path).expanduser().resolve()
    if not note.exists() or note.suffix.lower() != ".md":
        raise FileNotFoundError(f"Obsidian note is unavailable: {note}")
    metadata, body = _frontmatter(note.read_text(encoding="utf-8"))
    if metadata.get("rts_design") is not True:
        raise PermissionError("Obsidian note requires `rts_design: true`")

    feedback = _section(body, ("Feedback", "要望", "不満", "感想"))
    goals = _section(body, ("Goals", "目的", "ゴール"))
    constraints = _section(body, ("Constraints", "制約"))
    unresolved = _section(body, ("Questions", "未決事項", "確認事項"))
    if not feedback and body.strip():
        feedback = [line.strip() for line in body.splitlines() if line.strip() and not line.lstrip().startswith("#")]

    payload: dict[str, Any] = {
        "schema_version": str(metadata.get("schema_version", "1.0")),
        "request_id": metadata.get("request_id"),
        "project_id": metadata.get("project_id"),
        "title": metadata.get("title", note.stem),
        "domain": metadata.get("domain", "unknown"),
        "role": metadata.get("role", "unknown"),
        "target_user": metadata.get("target_user", "unknown"),
        "feedback": feedback,
        "goals": goals,
        "constraints": constraints,
        "unresolved_questions": unresolved,
        "references": metadata.get("references", []),
        "features": metadata.get("features", []),
        "sensory_profile": metadata.get("sensory_profile", {}),
        "source": {"type": "obsidian", "path": note.name},
    }
    return {key: value for key, value in payload.items() if value is not None}


def run_obsidian_design(
    vault_path: str | Path,
    note_relative_path: str | Path,
    repo_root: str | Path,
    output_root: str = "_RTS/Design Reviews",
) -> ObsidianDesignResult:
    vault = Path(vault_path).expanduser().resolve()
    note = (vault / note_relative_path).resolve()
    if vault not in note.parents:
        raise PermissionError("note must remain inside the Vault")

    payload = note_to_translation_input(note)
    review_root = (vault / output_root).resolve()
    if vault not in review_root.parents:
        raise PermissionError("review output must remain inside the Vault")
    review_root.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="rts-obsidian-") as tmp:
        temp = Path(tmp)
        input_path = temp / "input.json"
        input_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        bundle = temp / "bundle"
        result = run_design_e2e(input_path, repo_root, bundle)
        review_note = review_root / f"{note.stem}--{result.request_id}.md"
        machine_record = review_root / f"{note.stem}--{result.request_id}.json"
        bundle_path = review_root / f"{note.stem}--{result.request_id}.bundle"
        if review_note.exists() or machine_record.exists() or bundle_path.exists():
            raise FileExistsError("refusing to overwrite an existing Obsidian design review")

        summary_md = (bundle / "summary.md").read_text(encoding="utf-8")
        review_note.write_text(
            "---\n"
            f"title: RTS Design Review - {payload['title']}\n"
            f"request_id: {result.request_id}\n"
            f"project_id: {result.project_id}\n"
            "status: AWAITING_HUMAN_DECISION\n"
            f"source_note: \"[[{Path(note_relative_path).as_posix()}]]\"\n"
            "human_decision_required: true\n"
            "---\n\n"
            f"> Source: [[{Path(note_relative_path).as_posix()}]]\n\n"
            + summary_md,
            encoding="utf-8",
        )
        machine_record.write_text(
            json.dumps(
                {
                    "adapter": "obsidian-design-v1",
                    "source_note": Path(note_relative_path).as_posix(),
                    **asdict(result),
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        shutil.copytree(bundle, bundle_path)

    return ObsidianDesignResult(
        source_note=Path(note_relative_path).as_posix(),
        request_id=result.request_id,
        project_id=result.project_id,
        review_note=str(review_note),
        machine_record=str(machine_record),
        bundle_path=str(bundle_path),
        status="AWAITING_HUMAN_DECISION",
        human_decision_required=True,
    )

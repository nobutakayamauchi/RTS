from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .sensitivity import SensitivityResult, assess_sensitivity


@dataclass(frozen=True)
class KnowledgeRecord:
    knowledge_id: str
    capture_id: str
    source_path: str
    source_hash: str
    title: str
    knowledge_type: str
    status: str
    project_id: str | None
    tags: tuple[str, ...]
    confidence: float
    sensitivity: str
    sensitivity_reasons: tuple[str, ...]
    public_export_allowed: bool
    frontmatter: dict[str, Any]
    body: str
    source_excerpt: str


def _scalar(value: str) -> Any:
    value = value.strip()
    if not value:
        return ""
    if value.startswith("[") and value.endswith("]"):
        return [part.strip().strip("'\"") for part in value[1:-1].split(",") if part.strip()]
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    return value.strip("'\"")


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str, bool]:
    if not text.startswith("---\n"):
        return {}, text, True
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}, text, False
    raw = text[4:end]
    data: dict[str, Any] = {}
    try:
        for line in raw.splitlines():
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            if ":" not in line:
                raise ValueError("malformed frontmatter")
            key, value = line.split(":", 1)
            data[key.strip()] = _scalar(value)
    except ValueError:
        return {}, text, False
    return data, text[end + 5 :], True


def _contains_any(text: str, words: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(word.lower() in lowered for word in words)


def _type(frontmatter: dict[str, Any], source_path: str, body: str) -> tuple[str, float]:
    explicit = str(frontmatter.get("knowledge_type", frontmatter.get("type", ""))).lower()
    allowed = {"problem", "decision", "spec", "test", "pattern", "project_context", "evidence", "idea", "archive"}
    if explicit in allowed:
        return explicit, 1.0

    # Content is evidence. Folder names are only weak hints and must never
    # override a clear statement in the note itself.
    body_rules = (
        ("decision", ("decision", "採用", "決定", "選定", "却下")),
        ("test", ("test", "acceptance criteria", "検証", "テスト", "合格条件")),
        ("spec", ("spec", "仕様", "要件", "shall", "must")),
        ("problem", ("problem", "課題", "不具合", "bug", "困っている")),
        ("evidence", ("evidence", "証拠", "log", "ログ", "実行結果")),
        ("pattern", ("pattern", "共通", "再利用", "傾向")),
        ("project_context", ("project", "プロジェクト", "進捗", "現在地")),
    )
    body_sample = body[:4000]
    for kind, words in body_rules:
        if _contains_any(body_sample, words):
            return kind, 0.78

    # Path is deliberately lower-confidence fallback information.
    path = source_path.lower()
    path_rules = (
        ("test", ("/tests/", "test", "検証")),
        ("spec", ("/specs/", "spec", "仕様")),
        ("decision", ("/decisions/", "decision", "決定")),
        ("problem", ("/problems/", "problem", "課題")),
        ("evidence", ("/evidence/", "evidence", "証拠")),
        ("pattern", ("/patterns/", "pattern", "共通")),
        ("project_context", ("/projects/", "project", "進捗")),
    )
    padded_path = f"/{path.lstrip('/')}"
    for kind, words in path_rules:
        if _contains_any(padded_path, words):
            return kind, 0.5
    return "idea", 0.4


def normalize_capture(state_root: str | Path, capture_id: str) -> KnowledgeRecord:
    root = Path(state_root)
    record_path = root / "captures" / capture_id / "record.json"
    if not record_path.exists():
        raise FileNotFoundError(f"capture not found: {capture_id}")
    capture = json.loads(record_path.read_text(encoding="utf-8"))
    content = (root / capture["content_file"]).read_text(encoding="utf-8", errors="replace")
    frontmatter, body, valid_frontmatter = parse_frontmatter(content)
    sensitivity: SensitivityResult = assess_sensitivity(content, frontmatter)
    kind, confidence = _type(frontmatter, capture["source_path"], body)
    title = str(frontmatter.get("title") or "")
    if not title:
        heading = re.search(r"^#\s+(.+)$", body, flags=re.MULTILINE)
        title = heading.group(1).strip() if heading else Path(capture["source_path"]).stem
    raw_tags = frontmatter.get("tags", [])
    if isinstance(raw_tags, str):
        tags = tuple(part.strip() for part in raw_tags.split(",") if part.strip())
    elif isinstance(raw_tags, list):
        tags = tuple(str(item).strip() for item in raw_tags if str(item).strip())
    else:
        tags = ()
    knowledge_id = f"KBR-{capture['source_hash'][:16]}"
    result = KnowledgeRecord(
        knowledge_id=knowledge_id,
        capture_id=capture_id,
        source_path=capture["source_path"],
        source_hash=capture["source_hash"],
        title=title,
        knowledge_type=kind,
        status=str(frontmatter.get("status", "captured")).lower(),
        project_id=str(frontmatter["project_id"]) if frontmatter.get("project_id") else None,
        tags=tags,
        confidence=confidence if valid_frontmatter else min(confidence, 0.3),
        sensitivity=sensitivity.level,
        sensitivity_reasons=sensitivity.reasons,
        public_export_allowed=sensitivity.public_export_allowed,
        frontmatter=frontmatter,
        body=body,
        source_excerpt=body.strip()[:500],
    )
    output = root / "normalized" / f"{knowledge_id}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    if not output.exists():
        output.write_text(json.dumps(asdict(result), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result

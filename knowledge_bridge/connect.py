from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from difflib import SequenceMatcher
from pathlib import Path


@dataclass(frozen=True)
class Connection:
    other_knowledge_id: str
    relation: str
    score: float
    reasons: tuple[str, ...]


def _tokens(text: str) -> set[str]:
    return {token.lower() for token in re.findall(r"[A-Za-z0-9_\-]+|[一-龥ぁ-んァ-ヶー]{2,}", text)}


def _load_records(root: Path) -> list[dict]:
    folder = root / "normalized"
    if not folder.exists():
        return []
    return [json.loads(path.read_text(encoding="utf-8")) for path in sorted(folder.glob("*.json"))]


def connect_record(state_root: str | Path, knowledge_id: str) -> tuple[Connection, ...]:
    root = Path(state_root)
    target_path = root / "normalized" / f"{knowledge_id}.json"
    if not target_path.exists():
        raise FileNotFoundError(f"knowledge record not found: {knowledge_id}")
    target = json.loads(target_path.read_text(encoding="utf-8"))
    target_text = f"{target.get('title', '')}\n{target.get('body', '')}"
    target_tokens = _tokens(target_text)
    connections: list[Connection] = []

    for other in _load_records(root):
        if other["knowledge_id"] == knowledge_id:
            continue
        reasons: list[str] = []
        score = 0.0
        if target.get("project_id") and target.get("project_id") == other.get("project_id"):
            reasons.append("same_project")
            score += 0.35
        shared_tags = set(target.get("tags", [])) & set(other.get("tags", []))
        if shared_tags:
            reasons.append("shared_tags:" + ",".join(sorted(shared_tags)))
            score += min(0.25, 0.08 * len(shared_tags))
        other_text = f"{other.get('title', '')}\n{other.get('body', '')}"
        other_tokens = _tokens(other_text)
        union = target_tokens | other_tokens
        overlap = len(target_tokens & other_tokens) / len(union) if union else 0.0
        similarity = SequenceMatcher(None, target_text[:2000], other_text[:2000]).ratio()
        score += min(0.3, overlap * 0.6)
        if overlap >= 0.2:
            reasons.append(f"token_overlap:{overlap:.2f}")
        relation = "related"
        if similarity >= 0.92:
            relation = "duplicate"
            reasons.append(f"text_similarity:{similarity:.2f}")
            score = max(score, 0.95)
        elif target.get("knowledge_type") == other.get("knowledge_type") == "decision" and overlap >= 0.25:
            relation = "possible_contradiction"
            reasons.append("same_decision_subject")
            score = max(score, 0.72)
        if score >= 0.35:
            connections.append(Connection(other["knowledge_id"], relation, round(min(score, 1.0), 3), tuple(reasons)))

    connections.sort(key=lambda item: (-item.score, item.other_knowledge_id))
    output = root / "connections" / f"{knowledge_id}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    if not output.exists():
        output.write_text(json.dumps([asdict(item) for item in connections], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return tuple(connections)

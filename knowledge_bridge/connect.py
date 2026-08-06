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
    """Return coarse multilingual tokens for similarity hints.

    Japanese prose is additionally split into overlapping character n-grams so
    two sentences can share a subject even when their differing predicate or
    storage destination prevents an exact word match.
    """
    lowered = text.lower()
    tokens = set(re.findall(r"[a-z0-9_\-]+|[一-龥ぁ-んァ-ヶー]{2,}", lowered))
    japanese_chunks = re.findall(r"[一-龥ぁ-んァ-ヶー]{2,}", lowered)
    for chunk in japanese_chunks:
        compact = re.sub(r"[はがをにへとでのだけするした]", "", chunk)
        for size in (2, 3):
            tokens.update(compact[index : index + size] for index in range(max(0, len(compact) - size + 1)))
    return {token for token in tokens if token}


# v1 keeps contradiction detection deterministic and explainable. These are
# incompatible choices only when they occur across two decision records that
# also share a project, tag, subject token, or a common decision anchor.
_OPPOSING_TERM_PAIRS: tuple[tuple[tuple[str, ...], tuple[str, ...], str], ...] = (
    (("端末内", "ローカル", "local", "on-device"), ("クラウド", "cloud", "remote"), "storage_location"),
    (("有効", "enable", "enabled", "許可"), ("無効", "disable", "disabled", "禁止"), "enablement"),
    (("公開", "public"), ("非公開", "private", "internal"), "visibility"),
    (("保存", "retain", "keep"), ("削除", "delete", "discard"), "retention"),
    (("必須", "required", "must"), ("任意", "optional", "may"), "requirement"),
    (("常に", "always"), ("決して", "never", "しない"), "polarity"),
    (("同期", "sync", "online"), ("オフライン", "offline", "非同期"), "connectivity"),
)

_DECISION_ANCHORS = (
    "保存",
    "データ",
    "認証",
    "同期",
    "公開",
    "接続",
    "storage",
    "data",
    "authentication",
    "sync",
    "visibility",
)


def _contains_any(text: str, terms: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(term.lower() in lowered for term in terms)


def _contradiction_reason(left: str, right: str, *, context_shared: bool) -> str | None:
    if not context_shared:
        return None
    for left_terms, right_terms, label in _OPPOSING_TERM_PAIRS:
        if (_contains_any(left, left_terms) and _contains_any(right, right_terms)) or (
            _contains_any(left, right_terms) and _contains_any(right, left_terms)
        ):
            return f"opposing_terms:{label}"
    return None


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
        same_project = bool(target.get("project_id") and target.get("project_id") == other.get("project_id"))
        if same_project:
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
        elif target.get("knowledge_type") == other.get("knowledge_type") == "decision":
            shared_anchor = any(anchor in target_text.lower() and anchor in other_text.lower() for anchor in _DECISION_ANCHORS)
            context_shared = same_project or bool(shared_tags) or overlap >= 0.12 or shared_anchor
            contradiction = _contradiction_reason(target_text, other_text, context_shared=context_shared)
            if contradiction:
                relation = "possible_contradiction"
                reasons.extend(("same_decision_subject", contradiction))
                score = max(score, 0.78)
            elif overlap >= 0.25:
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

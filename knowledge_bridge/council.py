from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class MissingPart:
    category: str
    name: str
    reason: str


@dataclass(frozen=True)
class CouncilReport:
    knowledge_id: str
    recommendation: str
    confidence: float
    codebase_files_considered: int
    freezer_items_considered: int
    insertion_candidates: tuple[str, ...]
    related_freezer_items: tuple[str, ...]
    missing_parts: tuple[MissingPart, ...]
    reasons_for: tuple[str, ...]
    opposing_view: tuple[str, ...]
    human_questions: tuple[str, ...]
    human_decision_required: bool
    status: str


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def _repo_files(repo_root: Path) -> list[Path]:
    allowed = {".py", ".js", ".ts", ".tsx", ".jsx", ".json", ".yaml", ".yml", ".toml", ".md"}
    ignored = {".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache"}
    return [
        path
        for path in repo_root.rglob("*")
        if path.is_file()
        and path.suffix.lower() in allowed
        and not any(part in ignored for part in path.parts)
    ]


def _freezer_items(repo_root: Path) -> list[dict[str, Any]]:
    freezer_root = repo_root / "freezer"
    results: list[dict[str, Any]] = []
    if not freezer_root.exists():
        return results
    for path in freezer_root.rglob("*.json"):
        if "schema" in path.name.lower() or "schemas" in path.parts:
            continue
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if isinstance(value, dict) and value.get("item_id"):
            value["_path"] = str(path.relative_to(repo_root))
            results.append(value)
    return results


def _terms(record: dict[str, Any]) -> set[str]:
    values = [record.get("title", ""), record.get("body", ""), *record.get("tags", [])]
    text = " ".join(str(value).lower() for value in values)
    terms = set(re.findall(r"[a-z0-9][a-z0-9_\-]{2,}|[一-龥ぁ-んァ-ヶー]{2,}", text))
    for chunk in re.findall(r"[一-龥ぁ-んァ-ヶー]{3,}", text):
        compact = re.sub(r"[はがをにへとでのだけするしたため方式実装]", "", chunk)
        for size in (2, 3, 4):
            terms.update(compact[index : index + size] for index in range(max(0, len(compact) - size + 1)))
    stop = {"データ", "機能", "実装", "方式", "保存", "する", "ため", "the", "and", "with"}
    return {term for term in terms if term and term not in stop}


def _safe_read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:250_000]
    except OSError:
        return ""


def _symbols(path: Path, content: str) -> list[str]:
    symbols: list[str] = []
    if path.suffix == ".py":
        symbols.extend(re.findall(r"^(?:async\s+)?def\s+([A-Za-z_][A-Za-z0-9_]*)", content, re.MULTILINE))
        symbols.extend(re.findall(r"^class\s+([A-Za-z_][A-Za-z0-9_]*)", content, re.MULTILINE))
    elif path.suffix in {".js", ".ts", ".tsx", ".jsx"}:
        symbols.extend(re.findall(r"(?:function|class)\s+([A-Za-z_$][A-Za-z0-9_$]*)", content))
        symbols.extend(re.findall(r"(?:const|let)\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*=", content))
    elif path.suffix == ".md":
        symbols.extend(re.findall(r"^#{1,4}\s+(.+)$", content, re.MULTILINE))
    return symbols[:80]


def _insertion_candidates(files: list[Path], repo: Path, record: dict[str, Any], terms: set[str]) -> list[str]:
    tags = {str(tag).lower() for tag in record.get("tags", []) if str(tag).strip()}
    ranked: list[tuple[float, str]] = []
    for path in files:
        relative = str(path.relative_to(repo))
        lowered_path = relative.lower()
        content = _safe_read(path)
        lowered_content = content.lower()
        symbols = _symbols(path, content)
        symbol_text = " ".join(symbols).lower()

        path_hits = sorted(term for term in terms | tags if term in lowered_path)
        symbol_hits = sorted(term for term in terms | tags if term in symbol_text)
        content_hits = sorted(term for term in terms | tags if term in lowered_content)
        if not (path_hits or symbol_hits or content_hits):
            continue

        score = min(0.45, len(path_hits) * 0.18) + min(0.35, len(symbol_hits) * 0.14) + min(0.30, len(content_hits) * 0.04)
        if path.name in {"cli.py", "route.py", "challenge.py", "freezer_export.py", "council.py"}:
            score += 0.05
        matched_symbols = [symbol for symbol in symbols if any(term in symbol.lower() for term in terms | tags)][:3]
        boundary = ",".join(matched_symbols) if matched_symbols else "module"
        reasons = []
        if path_hits:
            reasons.append("path=" + ",".join(path_hits[:4]))
        if symbol_hits:
            reasons.append("symbol=" + ",".join(symbol_hits[:4]))
        if content_hits:
            reasons.append("content=" + ",".join(content_hits[:4]))
        rendered = f"{relative}::{boundary} [score={min(score, 1.0):.2f}; {'; '.join(reasons)}]"
        ranked.append((score, rendered))

    ranked.sort(key=lambda item: (-item[0], item[1]))
    return [rendered for _, rendered in ranked[:8]]


def analyze_implementation_council(
    state_root: str | Path,
    knowledge_id: str,
    repo_root: str | Path,
    output_path: str | Path,
) -> CouncilReport:
    state = Path(state_root)
    repo = Path(repo_root).resolve()
    output = Path(output_path)
    if output.exists() or output.with_suffix(".md").exists():
        raise FileExistsError(f"refusing to overwrite council report: {output}")

    record = _load_json(state / "normalized" / f"{knowledge_id}.json")
    challenge = _load_json(state / "challenges" / f"{knowledge_id}.json")
    if not challenge.get("promotion_ready"):
        raise PermissionError("implementation council requires a promotion-ready record")

    metadata = record.get("frontmatter", {})
    files = _repo_files(repo)
    freezer = _freezer_items(repo)
    terms = _terms(record)
    insertion = _insertion_candidates(files, repo, record, terms)

    related: list[str] = []
    for item in freezer:
        haystack = json.dumps(item, ensure_ascii=False).lower()
        if any(term in haystack for term in terms):
            related.append(f"{item['item_id']}:{item.get('_path', '')}")
    related = sorted(dict.fromkeys(related))[:8]

    missing: list[MissingPart] = []
    required_checks = (
        ("blocking", "rollback", "Rollback or safe-stop boundary is required before implementation."),
        ("blocking", "test_plan", "A test plan is required before implementation."),
        ("blocking", "acceptance_criteria", "Observable completion criteria are required."),
        ("recommended", "observability", "Operational logs or evidence capture reduce debugging cost."),
        ("recommended", "migration_plan", "A migration plan reduces rework when existing state is affected."),
    )
    for category, key, reason in required_checks:
        if not metadata.get(key):
            missing.append(MissingPart(category, key, reason))

    dependencies = metadata.get("dependencies", [])
    if isinstance(dependencies, str):
        dependencies = [dependencies]
    blocking = any(part.category == "blocking" for part in missing)

    if not insertion:
        missing.append(MissingPart("blocking", "insertion_boundary", "No code boundary could be justified from paths, symbols, or source content; architecture clarification is required."))
        blocking = True

    if blocking:
        recommendation = "APPROVE_AFTER_FOUNDATION"
        confidence = 0.9
    elif related:
        recommendation = "BUNDLE_WITH_OTHER_ITEMS"
        confidence = 0.8
    else:
        recommendation = "APPROVE_NOW"
        confidence = 0.78

    reasons_for = [
        "The Devil's Advocate gate is promotion-ready.",
        f"{len(insertion)} ranked code insertion candidate(s) were found from paths, symbols, and source content.",
        f"{len(related)} related FREEZER item(s) were found.",
    ]
    if dependencies:
        reasons_for.append(f"Declared dependencies: {', '.join(str(item) for item in dependencies)}")

    opposing = [
        "A locally clean implementation may still increase system-wide complexity.",
        "Deferring can be cheaper when a shared foundation is likely to emerge.",
    ]
    if related:
        opposing.append("Existing FREEZER items may represent a better implementation order or bundle boundary.")
    if insertion:
        opposing.append("A high-scoring insertion candidate is evidence, not authority; module ownership must still be confirmed by a human.")

    questions = [
        "Is the requested timing more important than avoiding future migration cost?",
        "Should this be implemented alone, bundled, or held until its foundation exists?",
        "Does the highest-ranked insertion boundary preserve current module responsibilities?",
    ]

    result = CouncilReport(
        knowledge_id=knowledge_id,
        recommendation=recommendation,
        confidence=confidence,
        codebase_files_considered=len(files),
        freezer_items_considered=len(freezer),
        insertion_candidates=tuple(insertion),
        related_freezer_items=tuple(related),
        missing_parts=tuple(missing),
        reasons_for=tuple(reasons_for),
        opposing_view=tuple(opposing),
        human_questions=tuple(questions),
        human_decision_required=True,
        status="AWAITING_HUMAN_DECISION",
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(asdict(result), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown = output.with_suffix(".md")
    markdown.write_text(_markdown(result), encoding="utf-8")
    return result


def _markdown(report: CouncilReport) -> str:
    missing = "\n".join(f"- **{item.category} / {item.name}**: {item.reason}" for item in report.missing_parts) or "- None detected"
    insertion = "\n".join(f"- `{item}`" for item in report.insertion_candidates) or "- No clear candidate"
    related = "\n".join(f"- `{item}`" for item in report.related_freezer_items) or "- None detected"
    reasons = "\n".join(f"- {item}" for item in report.reasons_for)
    opposing = "\n".join(f"- {item}" for item in report.opposing_view)
    questions = "\n".join(f"- {item}" for item in report.human_questions)
    return f"""# Implementation Council Report\n\n## Recommendation\n\n**{report.recommendation}** (confidence: {report.confidence:.2f})\n\nStatus: `{report.status}`\n\n## Reasons\n\n{reasons}\n\n## Missing Parts\n\n{missing}\n\n## Ranked insertion candidates\n\n{insertion}\n\n## Related FREEZER items\n\n{related}\n\n## Opposing view\n\n{opposing}\n\n## Human discussion questions\n\n{questions}\n\nNo approval or implementation was executed.\n"""

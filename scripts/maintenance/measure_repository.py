#!/usr/bin/env python3
"""Measure repository shape without mutating repository content.

The tool uses only the Python standard library. It walks a checkout, records
size and line-count facts, and emits deterministic JSON and Markdown reports.
Classification buckets are descriptive and may overlap; they do not decide
which files may be deleted, moved, or treated as generated.
"""

from __future__ import annotations

import argparse
import json
import os
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable


IGNORED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "node_modules",
    "vendor",
}

TEXT_SUFFIXES = {
    ".c", ".cc", ".cfg", ".conf", ".cpp", ".css", ".csv", ".go",
    ".h", ".hpp", ".html", ".ini", ".java", ".js", ".json", ".jsx",
    ".md", ".mjs", ".py", ".rb", ".rst", ".rs", ".sh", ".sql",
    ".toml", ".ts", ".tsx", ".txt", ".xml", ".yaml", ".yml",
}

SOURCE_SUFFIXES = {
    ".c", ".cc", ".cpp", ".go", ".java", ".js", ".jsx", ".mjs",
    ".py", ".rb", ".rs", ".sh", ".ts", ".tsx",
}

DOC_SUFFIXES = {".md", ".rst", ".txt"}
DATA_SUFFIXES = {".csv", ".json", ".toml", ".xml", ".yaml", ".yml"}
GOVERNED_COMPONENTS = {
    "artifacts", "freezer", "incidents", "logs", "memory", "runs", "sessions"
}


@dataclass(frozen=True)
class FileFact:
    path: str
    suffix: str
    size_bytes: int
    lines: int
    is_text: bool


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--json", dest="json_path", type=Path, required=True)
    parser.add_argument("--markdown", dest="markdown_path", type=Path, required=True)
    parser.add_argument("--commit", default="UNKNOWN")
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="Repository-relative path to exclude from the baseline.",
    )
    return parser.parse_args()


def normalized_path(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def iter_files(root: Path, excluded: set[str]) -> Iterable[Path]:
    for current_root, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(name for name in dirnames if name not in IGNORED_DIRS)
        current = Path(current_root)
        for filename in sorted(filenames):
            path = current / filename
            relative = normalized_path(path, root)
            if relative in excluded:
                continue
            if path.is_symlink() or not path.is_file():
                continue
            yield path


def read_line_count(path: Path) -> tuple[bool, int]:
    suffix = path.suffix.lower()
    if suffix not in TEXT_SUFFIXES and path.name not in {
        "Dockerfile", "Makefile", "LICENSE", "NOTICE"
    }:
        return False, 0
    try:
        raw = path.read_bytes()
    except OSError:
        return False, 0
    if b"\x00" in raw:
        return False, 0
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return False, 0
    if not text:
        return True, 0
    return True, text.count("\n") + (0 if text.endswith("\n") else 1)


def classify(fact: FileFact) -> set[str]:
    path = PurePosixPath(fact.path)
    parts = set(path.parts)
    name = path.name.lower()
    labels: set[str] = set()

    if fact.suffix in SOURCE_SUFFIXES:
        labels.add("runtime_source")
    if fact.suffix in DOC_SUFFIXES or "docs" in parts:
        labels.add("documentation")
    if fact.suffix in DATA_SUFFIXES:
        labels.add("structured_data")
    if "schemas" in parts or ".schema." in name:
        labels.add("schemas_and_contracts")
    if "tests" in parts or name.startswith("test_") or name.endswith("_test.py"):
        labels.add("tests")
    if path.parts[:2] == (".github", "workflows"):
        labels.add("ci_workflows")
    if parts.intersection(GOVERNED_COMPONENTS):
        labels.add("governed_records_and_history")
    if any(token in name for token in ("current", "index", "manifest", "checkpoint")):
        labels.add("pointer_index_manifest_candidates")
    return labels


def aggregate(facts: list[FileFact], commit: str, excluded: list[str]) -> dict[str, object]:
    by_extension: dict[str, dict[str, int]] = defaultdict(lambda: {"files": 0, "lines": 0, "bytes": 0})
    by_top_level: dict[str, dict[str, int]] = defaultdict(lambda: {"files": 0, "text_files": 0, "lines": 0, "bytes": 0})
    by_category: dict[str, dict[str, int]] = defaultdict(lambda: {"files": 0, "lines": 0, "bytes": 0})

    for fact in facts:
        extension = fact.suffix or "[no extension]"
        top_level = fact.path.split("/", 1)[0]
        by_extension[extension]["files"] += 1
        by_extension[extension]["lines"] += fact.lines
        by_extension[extension]["bytes"] += fact.size_bytes
        by_top_level[top_level]["files"] += 1
        by_top_level[top_level]["text_files"] += int(fact.is_text)
        by_top_level[top_level]["lines"] += fact.lines
        by_top_level[top_level]["bytes"] += fact.size_bytes
        for category in classify(fact):
            by_category[category]["files"] += 1
            by_category[category]["lines"] += fact.lines
            by_category[category]["bytes"] += fact.size_bytes

    suffix_counts = Counter(fact.suffix or "[no extension]" for fact in facts)
    return {
        "schema_version": "RTS-REPOSITORY-INVENTORY-V1",
        "measurement_scope": "repository checkout excluding declared paths and tool caches",
        "baseline_commit": commit,
        "excluded_paths": sorted(excluded),
        "totals": {
            "files": len(facts),
            "bytes": sum(fact.size_bytes for fact in facts),
            "text_files": sum(fact.is_text for fact in facts),
            "text_lines": sum(fact.lines for fact in facts),
            "top_level_entries": len(by_top_level),
            "extensions": len(suffix_counts),
        },
        "categories": dict(sorted(by_category.items())),
        "top_level": dict(sorted(by_top_level.items())),
        "extensions": dict(sorted(by_extension.items())),
        "largest_files": [
            {
                "path": fact.path,
                "bytes": fact.size_bytes,
                "lines": fact.lines,
                "is_text": fact.is_text,
            }
            for fact in sorted(facts, key=lambda item: (-item.size_bytes, item.path))[:25]
        ],
        "notes": [
            "Category counts may overlap.",
            "The pointer/index/manifest bucket is a naming heuristic, not a generated-file decision.",
            "No deletion, movement, canonical-source decision, or architecture change is implied.",
        ],
    }


def markdown_table(rows: list[tuple[str, int, int, int]], heading: str) -> list[str]:
    output = [f"## {heading}", "", "| Name | Files | Lines | Bytes |", "|---|---:|---:|---:|"]
    output.extend(f"| `{name}` | {files:,} | {lines:,} | {size:,} |" for name, files, lines, size in rows)
    output.append("")
    return output


def render_markdown(report: dict[str, object]) -> str:
    totals = report["totals"]
    assert isinstance(totals, dict)
    categories = report["categories"]
    top_level = report["top_level"]
    extensions = report["extensions"]
    assert isinstance(categories, dict)
    assert isinstance(top_level, dict)
    assert isinstance(extensions, dict)

    lines = [
        "# RTS Repository Inventory Baseline v1",
        "",
        "> Measurement only. This report authorizes no deletion, movement, consolidation, or runtime change.",
        "",
        f"- Baseline commit: `{report['baseline_commit']}`",
        f"- Files: **{totals['files']:,}**",
        f"- Repository bytes measured: **{totals['bytes']:,}**",
        f"- UTF-8 text files: **{totals['text_files']:,}**",
        f"- UTF-8 text lines: **{totals['text_lines']:,}**",
        f"- Top-level entries: **{totals['top_level_entries']:,}**",
        f"- File-extension groups: **{totals['extensions']:,}**",
        "",
        "The categories below overlap intentionally. They describe repository shape and do not decide canonical ownership or removal eligibility.",
        "",
    ]

    category_rows = [
        (name, value["files"], value["lines"], value["bytes"])
        for name, value in categories.items()
    ]
    lines.extend(markdown_table(category_rows, "Descriptive category totals"))

    top_rows = sorted(
        ((name, value["files"], value["lines"], value["bytes"]) for name, value in top_level.items()),
        key=lambda row: (-row[2], -row[1], row[0]),
    )[:30]
    lines.extend(markdown_table(top_rows, "Largest top-level areas by text lines"))

    extension_rows = sorted(
        ((name, value["files"], value["lines"], value["bytes"]) for name, value in extensions.items()),
        key=lambda row: (-row[2], -row[1], row[0]),
    )[:20]
    lines.extend(markdown_table(extension_rows, "Largest extension groups by text lines"))

    lines.extend([
        "## Interpretation boundary",
        "",
        "This baseline answers how large the repository is and where material is concentrated. It does not yet answer which files are authoritative, generated, historical, duplicated, or safely removable. Those decisions belong to the next shape-up stage after explicit classification and reference analysis.",
        "",
        "## Declared exclusions",
        "",
    ])
    exclusions = report["excluded_paths"]
    assert isinstance(exclusions, list)
    lines.extend(f"- `{path}`" for path in exclusions)
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    excluded = {PurePosixPath(path).as_posix() for path in args.exclude}
    facts: list[FileFact] = []
    for path in iter_files(root, excluded):
        is_text, line_count = read_line_count(path)
        facts.append(
            FileFact(
                path=normalized_path(path, root),
                suffix=path.suffix.lower(),
                size_bytes=path.stat().st_size,
                lines=line_count,
                is_text=is_text,
            )
        )

    report = aggregate(facts, args.commit, sorted(excluded))
    args.json_path.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_path.parent.mkdir(parents=True, exist_ok=True)
    args.json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.markdown_path.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report["totals"], sort_keys=True))
    print(f"JSON_REPORT={args.json_path}")
    print(f"MARKDOWN_REPORT={args.markdown_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

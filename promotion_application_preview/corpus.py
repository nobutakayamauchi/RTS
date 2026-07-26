from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from .common import PromotionApplicationPreviewError, load_json, pretty_json, sha256_file
from .generation import (
    BASELINE_PATH,
    CANDIDATE_PATH,
    LEDGER_CURRENT_PATH,
    LEDGER_MANIFEST_PATH,
    PENDING_REVIEW_PATH,
    PROPOSAL_PATH,
    REGRESSION_RESULT_PATH,
    ROLLBACK_PATH,
    generate_preview,
)
from .models import SCHEMA_VERSION, validate_preview

PACKAGE_DIR = Path(__file__).resolve().parent
DEFAULT_ROOT = PACKAGE_DIR.parent
PREVIEW_PATH = "promotion_application_preview/previews/current.json"
SCHEMA_PATH = "promotion_application_preview/schemas/preview.schema.json"
FORBIDDEN_IMPORTS = {"subprocess", "socket", "requests", "urllib", "http", "ftplib"}


def _verify_forbidden_imports(root: Path) -> None:
    package = root / "promotion_application_preview"
    for path in sorted(package.glob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            raise PromotionApplicationPreviewError(f"invalid Python syntax: {path}: {exc}") from exc
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                names.append(node.module)
            for name in names:
                if name.split(".", 1)[0] in FORBIDDEN_IMPORTS:
                    raise PromotionApplicationPreviewError(
                        f"forbidden external-action import in {path}: {name}"
                    )


def source_paths(root: Path) -> list[Path]:
    relatives = [
        PROPOSAL_PATH,
        PENDING_REVIEW_PATH,
        LEDGER_CURRENT_PATH,
        LEDGER_MANIFEST_PATH,
        REGRESSION_RESULT_PATH,
        ROLLBACK_PATH,
        BASELINE_PATH,
        CANDIDATE_PATH,
        SCHEMA_PATH,
    ]
    return sorted((root / relative for relative in relatives), key=lambda path: path.as_posix())


def verify_all(root: Path = DEFAULT_ROOT) -> dict[str, Any]:
    root = root.resolve()
    _verify_forbidden_imports(root)
    schema = load_json(root / SCHEMA_PATH)
    if not isinstance(schema, dict) or schema.get("$id") != SCHEMA_VERSION:
        raise PromotionApplicationPreviewError("preview schema identifier mismatch")
    before = {path: sha256_file(path) for path in source_paths(root)}
    committed = load_json(root / PREVIEW_PATH)
    if not isinstance(committed, dict):
        raise PromotionApplicationPreviewError("committed preview must be an object")
    validate_preview(committed)
    first = generate_preview(root)
    second = generate_preview(root)
    if pretty_json(first) != pretty_json(second):
        raise PromotionApplicationPreviewError("preview generation is not deterministic")
    if pretty_json(first) != pretty_json(committed):
        raise PromotionApplicationPreviewError("committed preview is stale")
    after = {path: sha256_file(path) for path in source_paths(root)}
    if before != after:
        raise PromotionApplicationPreviewError("read-only verification changed a governed source")
    return {
        "preview_id": committed["preview_id"],
        "preview_fingerprint": committed["preview_fingerprint"],
        "state": committed["state"],
        "blocker_count": len(committed["blockers"]),
        "approval_status": committed["authority"]["approval_status"],
        "application_status": committed["authority"]["application_status"],
        "target_write_authorized": committed["authority"]["target_write_authorized"],
        "adjacent_repository_write_authorized": committed["authority"]["adjacent_repository_write_authorized"],
    }

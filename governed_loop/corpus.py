from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from .common import GovernedLoopError, load_json, pretty_json, sha256_file
from .generation import generate_run, source_paths
from .models import SCHEMA_VERSION, validate_record

PACKAGE_DIR = Path(__file__).resolve().parent
DEFAULT_ROOT = PACKAGE_DIR.parent
RUN_PATH = "governed_loop/runs/current.json"
SCHEMA_PATH = "governed_loop/schemas/loop_run.schema.json"
FORBIDDEN_IMPORTS = {
    "subprocess",
    "socket",
    "requests",
    "urllib",
    "http",
    "ftplib",
    "schedule",
}


def _verify_forbidden_imports(root: Path) -> None:
    package = root / "governed_loop"
    for path in sorted(package.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                names.append(node.module)
            for name in names:
                if name.split(".", 1)[0] in FORBIDDEN_IMPORTS:
                    raise GovernedLoopError(
                        f"forbidden external-action import in {path}: {name}"
                    )


def verify_all(root: Path = DEFAULT_ROOT, *, require_committed: bool = True) -> dict[str, Any]:
    root = root.resolve()
    schema_path = root / SCHEMA_PATH
    governed = source_paths(root) + [schema_path]
    run_path = root / RUN_PATH
    if run_path.exists():
        governed.append(run_path)
    before = {path: sha256_file(path) for path in governed}

    _verify_forbidden_imports(root)
    schema = load_json(schema_path)
    if not isinstance(schema, dict) or schema.get("$id") != SCHEMA_VERSION:
        raise GovernedLoopError("loop-run schema identifier mismatch")

    first = generate_run(root)
    second = generate_run(root)
    if pretty_json(first) != pretty_json(second):
        raise GovernedLoopError("governed loop generation is not deterministic")
    validate_record(first)

    if run_path.exists():
        committed = load_json(run_path)
        validate_record(committed)
        if pretty_json(committed) != pretty_json(first):
            raise GovernedLoopError("committed governed loop run is stale")
    elif require_committed:
        raise GovernedLoopError("committed governed loop run is missing")

    after = {path: sha256_file(path) for path in governed}
    if before != after:
        raise GovernedLoopError("read-only verification failed: governed file changed")

    return {
        "run_id": first["run_id"],
        "run_fingerprint": first["run_fingerprint"],
        "mode": first["mode"],
        "status": first["status"],
        "active_item_ids": first["components"]["read_only_loop"]["active_item_ids"],
        "proposal_status": first["components"]["learning_proposal"]["proposal_status"],
        "approval_status": first["authority"]["approval_status"],
        "application_status": first["authority"]["application_status"],
    }

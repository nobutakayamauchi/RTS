from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

PACKAGE_DIR = Path(__file__).resolve().parent
SOURCE_PATH = PACKAGE_DIR / "source" / "prs_242_261.json"
RUN_PATH = PACKAGE_DIR / "runs" / "p3_run_0001.json"
ALLOWED_EVIDENCE = {"VERIFIED", "INFERRED", "SELF_REPORTED", "UNVERIFIED", "CONFLICTED"}


class ProofEngineError(RuntimeError):
    pass


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def fingerprint(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise ProofEngineError(f"invalid or missing JSON: {path}") from exc
    if not isinstance(value, dict):
        raise ProofEngineError("JSON root must be an object")
    return value


def verify_source(source: dict) -> dict:
    material = copy.deepcopy(source)
    actual = material.pop("source_fingerprint", None)
    if actual != fingerprint(material):
        raise ProofEngineError("source fingerprint mismatch")
    numbers = [item.get("number") for item in source.get("prs", [])]
    if numbers != list(range(242, 262)):
        raise ProofEngineError("source PR range mismatch")
    if source.get("repository") != "nobutakayamauchi/RTS" or source.get("visibility") != "PUBLIC":
        raise ProofEngineError("source boundary widened")
    return source


def generate_run() -> dict:
    source = verify_source(load(SOURCE_PATH))
    committed = load(RUN_PATH)
    if committed.get("source_fingerprint") != source["source_fingerprint"]:
        raise ProofEngineError("run/source mismatch")
    return committed


def verify_run(run: dict | None = None) -> dict:
    source = verify_source(load(SOURCE_PATH))
    run = load(RUN_PATH) if run is None else run
    material = copy.deepcopy(run)
    actual = material.pop("run_fingerprint", None)
    if actual != fingerprint(material):
        raise ProofEngineError("run fingerprint mismatch")
    if run.get("source_fingerprint") != source["source_fingerprint"]:
        raise ProofEngineError("source drift")
    candidates = run.get("candidates")
    if not isinstance(candidates, list) or len(candidates) < 10:
        raise ProofEngineError("at least ten candidates required")
    source_numbers = {item["number"] for item in source["prs"]}
    ids = set()
    for candidate in candidates:
        cid = candidate.get("candidate_id")
        if not isinstance(cid, str) or cid in ids:
            raise ProofEngineError("duplicate or invalid candidate ID")
        ids.add(cid)
        cmat = copy.deepcopy(candidate)
        cfp = cmat.pop("candidate_fingerprint", None)
        if cfp != fingerprint(cmat):
            raise ProofEngineError(f"candidate fingerprint mismatch: {cid}")
        if candidate.get("evidence_label") not in ALLOWED_EVIDENCE:
            raise ProofEngineError("unknown evidence label")
        refs = candidate.get("evidence_prs")
        if not refs or not set(refs) <= source_numbers:
            raise ProofEngineError("candidate evidence escapes source boundary")
        if candidate.get("status") != "REVIEW_REQUIRED":
            raise ProofEngineError("candidate status must remain REVIEW_REQUIRED")
    review = run.get("review_queue", {})
    if review.get("state") != "HUMAN_REVIEW_REQUIRED" or review.get("decisions") != []:
        raise ProofEngineError("human decisions were manufactured")
    output = run.get("output_asset", {})
    if output.get("state") != "BLOCKED" or output.get("publication_status") != "NOT_PUBLISHED":
        raise ProofEngineError("output authority widened")
    for field, value in run.get("authority", {}).items():
        if value is not False:
            raise ProofEngineError(f"authority widened: {field}")
    return run

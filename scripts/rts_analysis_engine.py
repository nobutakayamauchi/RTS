#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
RTS Analysis Engine (Unified)

- Reads incidents/*.md (and incidents/**.md if needed)
- Extracts evidence pointers:
  - evidence_pack
  - run_url
  - snapshot_ref
  - snapshot_hash_sha256
  - python_script
- Auto-classifies Evidence Level (0-2):
  Level 0: none
  Level 1: run_url or evidence_pack
  Level 2: snapshot_hash_sha256 (snapshot integrity)
- Writes analysis/index.md (GitHub Pages friendly)

Design:
- Evidence-first
- No inference
- Show what exists, don't invent
"""

from __future__ import annotations

import re
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional


ROOT = Path(__file__).resolve().parents[1]
INCIDENTS_DIR = ROOT / "incidents"
OUTPUT = ROOT / "analysis" / "index.md"


# -------------------------
# Utils
# -------------------------

def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def md_link(text: str, href: str) -> str:
    # keep it simple & safe
    return f"[{text}]({href})"


def rel_to_repo(p: Path) -> str:
    try:
        return str(p.relative_to(ROOT)).replace("\\", "/")
    except Exception:
        return str(p).replace("\\", "/")


# -------------------------
# Frontmatter (tiny parser)
# -------------------------

_FRONTMATTER_RE = re.compile(r"(?s)^\s*---\s*\n(.*?)\n---\s*\n")


def parse_frontmatter(text: str) -> Dict[str, str]:
    """
    Very small YAML-ish parser for key: value pairs.
    (Good enough for RTS templates.)
    """
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return {}
    block = m.group(1)
    out: Dict[str, str] = {}
    for line in block.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        k = k.strip()
        v = v.strip()
        # normalize null-like
        if v.lower() in ("null", "none", "nil"):
            v = ""
        # strip quotes
        if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
            v = v[1:-1]
        out[k] = v
    return out


def find_bullet_value(text: str, key: str) -> str:
    """
    Extracts either:
      - key: value
    or
      - key:
          value
    anywhere in the file.
    """
    # inline:  - key: value   or   key: value
    m = re.search(rf"(?m)^\s*(?:-\s*)?{re.escape(key)}\s*:\s*(.+?)\s*$", text)
    if m:
        return m.group(1).strip()

    # block style: - key:\n    value
    m = re.search(rf"(?m)^\s*(?:-\s*)?{re.escape(key)}\s*:\s*$", text)
    if m:
        after = text[m.end():]
        for line in after.splitlines():
            if not line.strip():
                continue
            # stop if next key-ish line
            if re.match(r"^\s*(?:-+\s*)?[A-Za-z0-9_]+\s*:\s*", line):
                break
            return line.strip()
    return ""


# -------------------------
# Incident parsing
# -------------------------

def extract_fields(path: Path) -> Dict[str, str]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    fm = parse_frontmatter(text)

    def get(key: str) -> str:
        # priority: frontmatter -> bullets
        return fm.get(key, "") or find_bullet_value(text, key)

    return {
        "file": rel_to_repo(path),
        "schema_version": get("schema_version"),
        "evidence_level": get("evidence_level"),
        "analysis_status": get("analysis_status"),
        "evidence_pack": get("evidence_pack"),
        "run_url": get("run_url"),
        "snapshot_ref": get("snapshot_ref"),
        "snapshot_hash_sha256": get("snapshot_hash_sha256"),
        "python_script": get("python_script"),
    }


def collect_incident_files() -> List[Path]:
    if not INCIDENTS_DIR.exists():
        return []
    # incidents/*.md を基本。必要なら incidents/**/*.md に拡張OK
    files = sorted(INCIDENTS_DIR.glob("*.md"))
    # DRAFTやINC_TEMPLATEも含めたいならこのままでOK
    return [p for p in files if p.is_file()]


# -------------------------
# Evidence Level (0-2)
# -------------------------

def classify_level(fields: Dict[str, str]) -> int:
    """
    Level 2: snapshot_hash_sha256 present (integrity anchored)
    Level 1: run_url or evidence_pack present (external pointer exists)
    Level 0: none
    """
    if fields.get("snapshot_hash_sha256", "").strip():
        return 2
    if fields.get("run_url", "").strip() or fields.get("evidence_pack", "").strip():
        return 1
    return 0


# -------------------------
# Output
# -------------------------

def write_index(rows: List[Dict[str, str]]) -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    generated_at = now_utc_iso()
    incidents_count = len(rows)

    # summary counts by computed level
    c0 = sum(1 for r in rows if int(r.get("level", "0")) == 0)
    c1 = sum(1 for r in rows if int(r.get("level", "0")) == 1)
    c2 = sum(1 for r in rows if int(r.get("level", "0")) == 2)

    lines: List[str] = []
    lines.append("# RTS Analysis Index")
    lines.append("")
    lines.append(f"- generated_at_utc: `{generated_at}`")
    lines.append(f"- incidents_count: `{incidents_count}`")
    lines.append("")
    lines.append("RTS generates evidence-first operational memory. It does not infer causes beyond what is recorded.")
    lines.append("")
    lines.append("## Evidence Level Summary")
    lines.append("")
    lines.append(f"- Level0 (no pointer): `{c0}`")
    lines.append(f"- Level1 (run/evidence pack): `{c1}`")
    lines.append(f"- Level2 (snapshot hash anchored): `{c2}`")
    lines.append("")
    lines.append("## Incidents")
    lines.append("")
    lines.append("| Incident file | Level | run | pack | snap | hash | script |")
    lines.append("|---|---:|---|---|---|---|---|")

    for r in rows:
        f = r["file"]
        level = r["level"]

        # Link targets
        incident_href = f"../{f}"
        run_url = r.get("run_url", "").strip()
        evidence_pack = r.get("evidence_pack", "").strip()
        snapshot_ref = r.get("snapshot_ref", "").strip()
        snapshot_hash = r.get("snapshot_hash_sha256", "").strip()
        py_script = r.get("python_script", "").strip()

        f_cell = md_link(Path(f).name, incident_href)

        run_cell = md_link("run", run_url) if run_url else ""
        pack_cell = md_link("pack", f"../{evidence_pack}") if evidence_pack else ""
        snap_cell = md_link("snap", f"../{snapshot_ref}") if snapshot_ref else ""
        hash_cell = (snapshot_hash[:12] + "…") if snapshot_hash else ""
        py_cell = md_link("script", f"../{py_script}") if py_script else ""

        lines.append(f"| {f_cell} | `{level}` | {run_cell} | {pack_cell} | {snap_cell} | `{hash_cell}` | {py_cell} |")

    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append("- This report is evidence-first. It does not infer causes beyond what is recorded.")
    lines.append("- Level2 means: a snapshot file exists and its SHA256 is recorded.")
    lines.append("- Operator judgement remains final.")
    lines.append("")

    OUTPUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    files = collect_incident_files()
    rows: List[Dict[str, str]] = []

    for p in files:
        fields = extract_fields(p)
        fields["sha256"] = sha256_file(p)
        fields["level"] = str(classify_level(fields))
        rows.append(fields)

    write_index(rows)
    print(f"[OK] analysis index written: {rel_to_repo(OUTPUT)} (incidents={len(rows)})")


if __name__ == "__main__":
    main()

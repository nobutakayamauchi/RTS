from __future__ import annotations

import html
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

_ALLOWED = {"AS_BUILT", "BROKEN", "STALE"}
_TRACKED_TYPES = {"feature", "implementation_target", "missing_part"}


@dataclass(frozen=True)
class DebugLinkResult:
    bundle_path: str
    observations_path: str
    lifecycle_path: str
    html_path: str
    request_id: str
    project_id: str
    planned_count: int
    as_built_count: int
    broken_count: int
    stale_count: int
    unobserved_count: int
    status: str


def _load(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object in {path}")
    return value


def link_debug_observations(
    bundle_path: str | Path,
    observations_path: str | Path,
    output_path: str | Path,
) -> DebugLinkResult:
    bundle = Path(bundle_path).expanduser().resolve()
    observations_file = Path(observations_path).expanduser().resolve()
    output = Path(output_path).expanduser().resolve()
    html_path = output.with_suffix(".html")
    if output.exists() or html_path.exists():
        raise FileExistsError(f"refusing to overwrite lifecycle output: {output}")

    translation = _load(bundle / "translation.json")
    summary = _load(bundle / "summary.json")
    observations = _load(observations_file)

    request_id = translation.get("request_id")
    project_id = translation.get("project_id")
    if observations.get("request_id") != request_id:
        raise ValueError("observation request_id does not match bundle")
    if observations.get("project_id") != project_id:
        raise ValueError("observation project_id does not match bundle")
    if summary.get("status") != "AWAITING_HUMAN_DECISION":
        raise PermissionError("debug linking requires a human-decision-gated bundle")

    nodes = translation.get("planned_structure", {}).get("nodes", [])
    planned = {
        str(node["id"]): node
        for node in nodes
        if isinstance(node, dict) and node.get("type") in _TRACKED_TYPES and node.get("id")
    }
    observed_by_node: dict[str, list[dict[str, Any]]] = {node_id: [] for node_id in planned}
    orphans: list[dict[str, Any]] = []

    raw_observations = observations.get("observations", [])
    if not isinstance(raw_observations, list):
        raise ValueError("observations must be an array")
    for index, item in enumerate(raw_observations):
        if not isinstance(item, dict):
            raise ValueError(f"observations[{index}] must be an object")
        node_id = str(item.get("node_id", "")).strip()
        state = str(item.get("status", "")).upper()
        if not node_id:
            raise ValueError(f"observations[{index}].node_id is required")
        if state not in _ALLOWED:
            raise ValueError(f"observations[{index}].status is unsupported: {state}")
        normalized = {
            "node_id": node_id,
            "status": state,
            "artifact": str(item.get("artifact", "")),
            "source": str(item.get("source", "debug-system")),
            "details": str(item.get("details", "")),
            "observed_at": str(item.get("observed_at", "")),
        }
        if node_id in observed_by_node:
            observed_by_node[node_id].append(normalized)
        else:
            orphans.append(normalized)

    lifecycle_items: list[dict[str, Any]] = []
    counts = {"AS_BUILT": 0, "BROKEN": 0, "STALE": 0, "UNOBSERVED": 0}
    for node_id, node in planned.items():
        entries = observed_by_node[node_id]
        states = {entry["status"] for entry in entries}
        if "BROKEN" in states:
            effective = "BROKEN"
        elif "STALE" in states:
            effective = "STALE"
        elif "AS_BUILT" in states:
            effective = "AS_BUILT"
        else:
            effective = "UNOBSERVED"
        counts[effective] += 1
        lifecycle_items.append(
            {
                "node_id": node_id,
                "node_type": node.get("type"),
                "label": node.get("label", node.get("title", node_id)),
                "planned": True,
                "effective_status": effective,
                "observations": entries,
            }
        )

    model = {
        "schema_version": "1.0",
        "view": "rts-planned-observed-lifecycle",
        "request_id": request_id,
        "project_id": project_id,
        "identity": {"request_id": request_id, "project_id": project_id, "title": translation.get("title", "Untitled")},
        "counts": {"planned": len(planned), "as_built": counts["AS_BUILT"], "broken": counts["BROKEN"], "stale": counts["STALE"], "unobserved": counts["UNOBSERVED"], "orphan": len(orphans)},
        "items": lifecycle_items,
        "orphan_observations": orphans,
        "approval": {"status": "AWAITING_HUMAN_DECISION", "implementation_executed": False},
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    html_path.write_text(_render(model), encoding="utf-8")
    return DebugLinkResult(
        bundle_path=str(bundle), observations_path=str(observations_file), lifecycle_path=str(output), html_path=str(html_path),
        request_id=str(request_id), project_id=str(project_id), planned_count=len(planned), as_built_count=counts["AS_BUILT"],
        broken_count=counts["BROKEN"], stale_count=counts["STALE"], unobserved_count=counts["UNOBSERVED"],
        status="AWAITING_HUMAN_DECISION",
    )


def _render(model: dict[str, Any]) -> str:
    cards = []
    for item in model["items"]:
        observations = "".join(
            f"<li><strong>{html.escape(o['status'])}</strong> {html.escape(o['artifact'])} — {html.escape(o['details'])}</li>"
            for o in item["observations"]
        ) or "<li>観測なし</li>"
        cards.append(
            f"<article class='card {item['effective_status'].lower()}'><h2>{html.escape(str(item['label']))}</h2>"
            f"<div class='status'>{html.escape(item['effective_status'])}</div><code>{html.escape(item['node_id'])}</code><ul>{observations}</ul></article>"
        )
    orphan = "".join(f"<li>{html.escape(o['node_id'])}: {html.escape(o['status'])}</li>" for o in model["orphan_observations"]) or "<li>なし</li>"
    c = model["counts"]
    return f"""<!doctype html><html lang='ja'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>{html.escape(str(model['identity']['title']))} — Planned / Observed</title><style>
:root{{font-family:system-ui,sans-serif;background:#101522;color:#edf2f8}}body{{margin:0;padding:20px;max-width:1100px;margin-inline:auto}}
.summary{{display:flex;flex-wrap:wrap;gap:8px;margin:14px 0}}.summary span,.status{{padding:4px 9px;border-radius:999px;background:#26334b}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));gap:12px}}.card{{background:#171e2e;border:1px solid #33405a;border-radius:14px;padding:14px}}
.card h2{{font-size:1rem;margin:0 0 8px}}.broken{{border-color:#d85b5b}}.stale{{border-color:#d89a3a}}.as_built{{border-color:#50a879}}.unobserved{{border-color:#68758b}}
code,li{{overflow-wrap:anywhere}}.safe{{margin-top:16px;padding:12px;background:#202a3d;border-radius:10px}}</style></head><body>
<h1>Planned / As Built / Broken / Stale</h1><p>{html.escape(model['identity']['request_id'])} · {html.escape(model['identity']['project_id'])}</p>
<div class='summary'><span>Planned {c['planned']}</span><span>As Built {c['as_built']}</span><span>Broken {c['broken']}</span><span>Stale {c['stale']}</span><span>Unobserved {c['unobserved']}</span></div>
<main class='grid'>{''.join(cards)}</main><h2>計画外の観測</h2><ul>{orphan}</ul>
<div class='safe'>観測結果は判断材料です。承認・コード変更・修復は自動実行されていません。</div></body></html>"""

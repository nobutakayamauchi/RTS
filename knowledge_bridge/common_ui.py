from __future__ import annotations

import html
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CommonUIViewResult:
    bundle_path: str
    view_model_path: str
    html_path: str
    request_id: str
    project_id: str
    status: str
    human_decision_required: bool


def _load(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object in {path}")
    return value


def _feature_lines(translation: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {
            "label": str(item.get("feature", "Unnamed feature")),
            "state": str(item.get("decision", "CLARIFY")),
            "detail": str(item.get("reason", "")),
        }
        for item in translation.get("feature_decisions", [])
        if isinstance(item, dict)
    ]


def _missing_lines(summary: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {
            "label": str(item.get("name", "Unnamed missing part")),
            "state": str(item.get("category", "missing")),
            "detail": str(item.get("reason", "")),
        }
        for item in summary.get("missing_parts", [])
        if isinstance(item, dict)
    ]


def build_common_view_model(bundle_path: str | Path, output_path: str | Path) -> CommonUIViewResult:
    bundle = Path(bundle_path).expanduser().resolve()
    output = Path(output_path).expanduser().resolve()
    html_path = output.with_suffix(".html")
    if output.exists() or html_path.exists():
        raise FileExistsError(f"refusing to overwrite shared UI output: {output}")

    translation = _load(bundle / "translation.json")
    summary = _load(bundle / "summary.json")
    council = _load(bundle / "council.json")

    if translation.get("request_id") != summary.get("request_id"):
        raise ValueError("translation and summary request_id do not match")
    if translation.get("project_id") != summary.get("project_id"):
        raise ValueError("translation and summary project_id do not match")
    if summary.get("status") != "AWAITING_HUMAN_DECISION":
        raise PermissionError("shared UI may only render a human-decision-gated bundle")
    if summary.get("implementation_executed") is not False:
        raise PermissionError("shared UI refuses bundles that report implementation execution")

    plan_nodes = translation.get("planned_structure", {}).get("nodes", [])
    plan_edges = translation.get("planned_structure", {}).get("edges", [])
    view_model = {
        "schema_version": "1.0",
        "view": "rts-common-ui",
        "identity": {
            "request_id": translation["request_id"],
            "project_id": translation["project_id"],
            "title": translation.get("title", "Untitled request"),
            "domain": translation.get("domain", "unknown"),
            "target_user": translation.get("target_user", "unknown"),
        },
        "sections": {
            "request": {
                "title": "要望",
                "items": [
                    {"label": goal, "state": "goal", "detail": ""}
                    for goal in translation.get("inferred_goals", [])
                ],
            },
            "plan": {
                "title": "計画",
                "items": _feature_lines(translation),
                "graph": {"nodes": plan_nodes, "edges": plan_edges},
            },
            "missing": {
                "title": "不足",
                "items": _missing_lines(summary),
            },
            "connections": {
                "title": "接続先",
                "items": [
                    {"label": item, "state": "candidate", "detail": "implementation insertion candidate"}
                    for item in summary.get("insertion_candidates", [])
                ]
                + [
                    {"label": item, "state": "freezer", "detail": "related FREEZER item"}
                    for item in summary.get("related_freezer_items", [])
                ],
            },
            "approval": {
                "title": "承認",
                "status": summary["status"],
                "human_decision_required": True,
                "implementation_executed": False,
                "questions": list(summary.get("human_questions", [])),
                "recommendation": council.get("recommendation", "DISCUSS"),
                "implementation_strategy": council.get("implementation_strategy", "HOLD"),
            },
        },
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(view_model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    html_path.write_text(_render_html(view_model), encoding="utf-8")
    return CommonUIViewResult(
        bundle_path=str(bundle),
        view_model_path=str(output),
        html_path=str(html_path),
        request_id=translation["request_id"],
        project_id=translation["project_id"],
        status=summary["status"],
        human_decision_required=True,
    )


def _cards(items: list[dict[str, Any]]) -> str:
    if not items:
        return '<p class="empty">項目なし</p>'
    rendered = []
    for item in items:
        rendered.append(
            '<article class="item">'
            f'<div class="item-head"><strong>{html.escape(str(item.get("label", "")))}</strong>'
            f'<span>{html.escape(str(item.get("state", "")))}</span></div>'
            f'<p>{html.escape(str(item.get("detail", "")))}</p>'
            '</article>'
        )
    return "".join(rendered)


def _render_html(model: dict[str, Any]) -> str:
    identity = model["identity"]
    sections = model["sections"]
    approval = sections["approval"]
    questions = "".join(f"<li>{html.escape(str(item))}</li>" for item in approval["questions"]) or "<li>なし</li>"
    node_count = len(sections["plan"]["graph"]["nodes"])
    edge_count = len(sections["plan"]["graph"]["edges"])
    return f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(str(identity['title']))} — RTS Common UI</title>
<style>
:root{{font-family:system-ui,sans-serif;color:#e9eef5;background:#101522}}
body{{margin:0;padding:20px;max-width:1200px;margin-inline:auto}}
header{{margin-bottom:18px}} h1{{font-size:1.5rem;margin:.2rem 0}} .meta{{color:#9eabc0;font-size:.9rem}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:14px}}
section{{background:#171e2e;border:1px solid #2b354a;border-radius:14px;padding:14px}}
section h2{{margin:0 0 12px;font-size:1.05rem}} .item{{border-top:1px solid #2b354a;padding:10px 0}}
.item:first-of-type{{border-top:0}} .item-head{{display:flex;gap:8px;justify-content:space-between}}
.item-head span{{font-size:.72rem;padding:2px 7px;border-radius:999px;background:#26334b;color:#b9c8dd}}
.item p,.empty{{margin:.35rem 0 0;color:#aeb9ca;font-size:.85rem;white-space:pre-wrap}}
.approval{{border-color:#a37822}} .status{{font-weight:700;color:#ffd778;overflow-wrap:anywhere}}
ul{{padding-left:1.2rem;color:#c1cad8}} .safe{{margin-top:12px;padding:10px;border-radius:10px;background:#202a3d}}
</style>
</head>
<body>
<header>
<div class="meta">RTS Common UI / {html.escape(str(identity['request_id']))} / {html.escape(str(identity['project_id']))}</div>
<h1>{html.escape(str(identity['title']))}</h1>
<div class="meta">{html.escape(str(identity['domain']))} · {html.escape(str(identity['target_user']))}</div>
</header>
<main class="grid">
<section><h2>要望</h2>{_cards(sections['request']['items'])}</section>
<section><h2>計画</h2><p class="meta">Planned Map: {node_count} nodes / {edge_count} edges</p>{_cards(sections['plan']['items'])}</section>
<section><h2>不足</h2>{_cards(sections['missing']['items'])}</section>
<section><h2>接続先</h2>{_cards(sections['connections']['items'])}</section>
<section class="approval"><h2>承認</h2><div class="status">{html.escape(str(approval['status']))}</div>
<p>Recommendation: {html.escape(str(approval['recommendation']))}</p>
<p>Strategy: {html.escape(str(approval['implementation_strategy']))}</p>
<ul>{questions}</ul>
<div class="safe">人間の承認が必要です。コード変更・実装は実行されていません。</div></section>
</main>
</body>
</html>
"""

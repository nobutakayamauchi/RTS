from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import html
import json
from pathlib import Path
import re
from urllib.parse import urlencode


class PublicationBridgeError(ValueError):
    pass


X_INTENT_BASE = "https://x.com/intent/tweet"
NOTE_EDITOR_URL = "https://note.com/new"
REQUIRED_HANDOFF_STATE = "APPROVED_FOR_HANDOFF"
REQUIRED_HUMAN_MODE = "/human"


@dataclass(frozen=True)
class HandoffAction:
    channel: str
    action: str
    label: str
    url: str | None = None
    text: str | None = None
    requires_user_action: bool = True


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_humanization_record(
    drafts: dict[str, str],
    *,
    reviewer: str,
    evidence_preserved: bool,
    notes: str = "",
) -> dict:
    """Create the attestation consumed by Publication Bridge.

    This function does not perform /human rewriting. The caller must first run
    the external-facing copy through the /human pass, preserving verified facts,
    prices, terms, URLs and scope. The record binds the reviewed result by hash.
    """
    reviewer = reviewer.strip()
    if not reviewer:
        raise PublicationBridgeError("/human reviewer must be recorded")
    if evidence_preserved is not True:
        raise PublicationBridgeError("/human cannot pass without evidence preservation")
    supported = {channel: text for channel, text in drafts.items() if channel in {"x", "note"} and text}
    if not supported:
        raise PublicationBridgeError("/human has no supported external drafts")
    return {
        "required": True,
        "mode": REQUIRED_HUMAN_MODE,
        "passed": True,
        "reviewer": reviewer,
        "evidence_preserved": True,
        "reviewed_channels": sorted(supported),
        "output_sha256": {channel: _sha256_text(text) for channel, text in sorted(supported.items())},
        "notes": notes.strip(),
    }


def _require_approved(manifest: dict, drafts: dict[str, str]) -> None:
    state = manifest.get("human_review_state")
    if state != REQUIRED_HANDOFF_STATE:
        raise PublicationBridgeError(
            f"source must complete /human and be APPROVED_FOR_HANDOFF, got: {state!r}"
        )
    if manifest.get("external_publication_performed") is not False:
        raise PublicationBridgeError("source manifest publication boundary is invalid")
    if manifest.get("verification_warnings"):
        raise PublicationBridgeError("cannot hand off a bundle with verification warnings")

    humanization = manifest.get("humanization")
    if not isinstance(humanization, dict):
        raise PublicationBridgeError("external handoff requires a /human attestation")
    if humanization.get("required") is not True:
        raise PublicationBridgeError("/human must be marked required")
    if humanization.get("mode") != REQUIRED_HUMAN_MODE:
        raise PublicationBridgeError("external handoff requires mode=/human")
    if humanization.get("passed") is not True:
        raise PublicationBridgeError("/human has not passed")
    if humanization.get("evidence_preserved") is not True:
        raise PublicationBridgeError("/human evidence-preservation check did not pass")

    reviewed_channels = humanization.get("reviewed_channels")
    output_hashes = humanization.get("output_sha256")
    if not isinstance(reviewed_channels, list) or not isinstance(output_hashes, dict):
        raise PublicationBridgeError("/human attestation is incomplete")

    for channel in ("x", "note"):
        text = drafts.get(channel)
        if not text:
            continue
        if channel not in reviewed_channels:
            raise PublicationBridgeError(f"{channel} draft did not pass /human")
        expected = output_hashes.get(channel)
        actual = _sha256_text(text)
        if expected != actual:
            raise PublicationBridgeError(
                f"{channel} draft changed after /human; rerun /human before handoff"
            )


def parse_x_blocks(text: str) -> list[str]:
    marker = re.compile(r"^\[X POST \d+/\d+\]\s*$", re.MULTILINE)
    if not marker.search(text):
        clean = text.strip()
        return [clean] if clean else []
    return [part.strip() for part in marker.split(text) if part.strip()]


def x_actions(text: str) -> list[HandoffAction]:
    blocks = parse_x_blocks(text)
    if not blocks:
        raise PublicationBridgeError("x draft contains no post bodies")
    actions: list[HandoffAction] = []
    for index, block in enumerate(blocks, start=1):
        actions.append(
            HandoffAction(
                channel="x",
                action="OPEN_COMPOSER",
                label=f"Xで確認 {index}/{len(blocks)}",
                url=X_INTENT_BASE + "?" + urlencode({"text": block}),
                text=block,
            )
        )
    return actions


def parse_note(text: str) -> tuple[str, str]:
    lines = text.strip().splitlines()
    if not lines:
        raise PublicationBridgeError("note draft is empty")
    title = lines[0].lstrip("#").strip() if lines[0].startswith("#") else ""
    body = "\n".join(lines[1:] if title else lines).strip()
    if not title:
        raise PublicationBridgeError("note draft must start with a markdown H1 title")
    if not body:
        raise PublicationBridgeError("note draft body is empty")
    return title, body


def note_actions(text: str) -> list[HandoffAction]:
    title, body = parse_note(text)
    return [
        HandoffAction("note", "COPY_TITLE", "タイトルをコピー", text=title),
        HandoffAction("note", "COPY_BODY", "本文をコピー", text=body),
        HandoffAction("note", "OPEN_EDITOR", "noteを開く", url=NOTE_EDITOR_URL),
    ]


def build_handoff(manifest: dict, drafts: dict[str, str]) -> dict:
    _require_approved(manifest, drafts)
    actions: list[HandoffAction] = []
    if drafts.get("x"):
        actions.extend(x_actions(drafts["x"]))
    if drafts.get("note"):
        actions.extend(note_actions(drafts["note"]))
    if not actions:
        raise PublicationBridgeError("no supported handoff drafts supplied")
    return {
        "schema_version": "0.2",
        "source_bundle_id": manifest.get("bundle_id"),
        "state": "APPROVED_FOR_HANDOFF",
        "humanization_mode": REQUIRED_HUMAN_MODE,
        "humanization_verified": True,
        "publication_authority": "USER_ONLY",
        "automatic_publication": False,
        "credential_storage": False,
        "private_api_usage": False,
        "actions": [asdict(action) for action in actions],
    }


def render_handoff_html(handoff: dict) -> str:
    cards: list[str] = []
    for action in handoff["actions"]:
        label = html.escape(action["label"])
        channel = html.escape(action["channel"].upper())
        text = action.get("text") or ""
        preview = html.escape(text)
        if action["action"].startswith("COPY_"):
            payload = html.escape(json.dumps(text, ensure_ascii=False), quote=True)
            control = f'<button data-copy="{payload}" onclick="copyText(this)">{label}</button>'
        elif action.get("url"):
            control = f'<a class="button" target="_blank" rel="noopener noreferrer" href="{html.escape(action["url"], quote=True)}">{label}</a>'
        else:
            control = ""
        cards.append(f'<section><h2>{channel}</h2><pre>{preview}</pre>{control}</section>')
    return """<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Publication Bridge</title><style>body{font-family:system-ui,sans-serif;max-width:860px;margin:auto;padding:20px;background:#f6f7f9;color:#111}section{background:#fff;padding:18px;border-radius:16px;margin:16px 0;box-shadow:0 4px 18px #0001}pre{white-space:pre-wrap;word-break:break-word;background:#f3f4f6;padding:12px;border-radius:10px}button,.button{display:inline-block;border:0;background:#111;color:#fff;padding:11px 15px;border-radius:10px;text-decoration:none;font-weight:700}small{color:#666}</style></head><body><h1>Publication Bridge</h1><p><small>/human 済み最終稿のみ。自動公開なし。内容を確認してから各サービス側で最終操作してください。</small></p>""" + "".join(cards) + """<script>async function copyText(el){await navigator.clipboard.writeText(JSON.parse(el.dataset.copy));}</script></body></html>"""


def load_bundle(bundle_dir: Path) -> tuple[dict, dict[str, str]]:
    manifest = json.loads((bundle_dir / "manifest.json").read_text(encoding="utf-8"))
    drafts: dict[str, str] = {}
    for channel in ("x", "note"):
        path = bundle_dir / f"{channel}.md"
        if path.exists():
            drafts[channel] = path.read_text(encoding="utf-8")
    return manifest, drafts

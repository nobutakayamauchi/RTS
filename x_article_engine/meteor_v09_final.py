from __future__ import annotations

import re
import unicodedata

from . import meteor_v09 as _round1
from .core import XArticleEngineError


DATE_RE = re.compile(
    r"(?:20\d{2}[年/-](?:0?[1-9]|1[0-2])(?:[月/-](?:0?[1-9]|[12]\d|3[01])日?)?|"
    r"20\d{2}年(?:0?[1-9]|1[0-2])月時点|20\d{2}年時点)"
)

NEGATION_OR_WARNING = (
    "使わない",
    "使用しない",
    "しない",
    "しないで",
    "ないで",
    "ないでください",
    "禁止",
    "避け",
    "危険",
    "やめ",
    "ダメ",
    "してはいけ",
    "無効にしない",
    "スキップしない",
    "共有しない",
    "渡さない",
    "貼り付けない",
)

IMPERATIVE_SAFETY_MARKERS = (
    "確認してください",
    "確認する",
    "共有しない",
    "渡さない",
    "貼り付けない",
    "停止してください",
    "停止する",
    "戻してください",
    "戻す",
    "守って",
    "守る",
    "禁止",
    "対象外",
    "使わない",
    "しないで",
)

OUTCOME_OR_PROMISE_MARKERS = (
    "できる",
    "できます",
    "終わる",
    "終わります",
    "完了",
    "成功",
    "売れる",
    "伸びる",
    "稼げる",
    "増える",
    "安全です",
    "大丈夫",
    "保証",
    "無料",
    "追加料金",
    "返金",
)

SECRET_RE = re.compile(
    r"(?:API\s*キー|API\s*key|シークレット|secret|アクセストークン|トークン|パスワード|認証情報|クレジットカード)",
    re.I,
)

MODEL_DESTINATION_RE = re.compile(
    r"(?:(?:AI|Claude|ChatGPT|Codex)(?:に|へ)|プロンプト|チャット|会話|メッセージ)",
    re.I,
)

TRANSFER_RE = re.compile(r"(?:貼り付け|貼って|送信|送って|渡して|コピペ|入力して)")

UNSAFE_ACTION_PATTERNS = (
    re.compile(r"--dangerously-skip-permissions", re.I),
    re.compile(r"(?:権限|確認|承認)[^。\n]{0,25}(?:スキップ|飛ば|省略)[^。\n]{0,20}(?:して|する|してください|で進)"),
    re.compile(r"認証[^。\n]{0,18}(?:無効|none|なし)[^。\n]{0,18}(?:にして|に設定|を選|で進)", re.I),
    re.compile(r"サンドボックス[^。\n]{0,18}(?:無効|off)[^。\n]{0,18}(?:にして|に設定|で進)", re.I),
)

CTA_ACTION_PATTERNS = {
    "purchase": re.compile(r"購入(?:して|する|はこちら|できます|へ)"),
    "apply": re.compile(r"申し込(?:んで|む|み|はこちら|めます)"),
    "join": re.compile(r"参加(?:して|する|はこちら|できます|へ)"),
    "register": re.compile(r"登録(?:して|する|はこちら|できます|へ)"),
    "add_friend": re.compile(r"友だち追加(?:して|する|はこちら|へ)"),
    "follow": re.compile(r"フォロー(?:して|する|お願いします|してください)"),
    "reply": re.compile(r"リプ(?:して|する|してください|ください)"),
    "dm": re.compile(r"DM(?:して|する|ください|してください)"),
    "consult": re.compile(r"無料相談(?:して|する|はこちら|へ)"),
    "fit_check": re.compile(r"無料適合確認(?:を使|はこちら|へ|して)"),
    "request": re.compile(r"資料請求(?:して|する|はこちら|へ)"),
}

GUARANTEE_RE = re.compile(r"(?:保証します|保証できます|保証する|確実にできます|確実に終わります)")
ABSOLUTE_SAFETY_RE = re.compile(r"(?:完全に安全|絶対安全|安全です|安心です)")
OUTCOME_PROMISE_RE = re.compile(r"(?:売れます|売れるようになります|必ず伸びる|伸びます|稼げます|稼げるようになります)")

STEP_RE = re.compile(r"(?:\bSTEP\s*[0-9０-９]+\b|ステップ\s*[0-9０-９一二三四五六七八九十]+|手順\s*[0-9０-９一二三四五六七八九十]+)", re.I)

SUCCESS_MARKERS = (
    "成功",
    "完了",
    "表示されたら",
    "表示されれば",
    "確認してください",
    "確認でき",
    "できていれば",
    "見えれば",
    "表示されます",
)

RECOVERY_MARKERS = (
    "エラー",
    "失敗",
    "うまくいかな",
    "困った",
    "場合は",
    "やり直",
    "戻",
    "停止",
    "再試行",
)

LOCAL_MITIGATION_MARKERS = (
    "停止",
    "戻",
    "バックアップ",
    "確認",
    "権限",
    "テスト",
    "サンドボックス",
    "対象外",
    "人間",
    "復旧",
)


def _norm(value: str) -> str:
    return unicodedata.normalize("NFKC", value)


def _sentences(text: str) -> list[str]:
    return [
        item.strip()
        for item in re.split(r"(?<=[。！？!?])|\n+", _norm(text))
        if item.strip()
    ]


def _is_negative_or_warning(sentence: str) -> bool:
    normalized = _norm(sentence)
    return any(marker in normalized for marker in NEGATION_OR_WARNING)


def _has_verified_dated_evidence(packet: dict) -> bool:
    for item in packet.get("verified_evidence", []):
        if item.get("kind") == "TIMING":
            return True
        if DATE_RE.search(_norm(item.get("claim", ""))):
            return True
    return False


def _only_safety_imperative_usage(draft: str, marker: str) -> bool:
    matched = [sentence for sentence in _sentences(draft) if marker in sentence]
    if not matched:
        return False
    for sentence in matched:
        if any(item in sentence for item in OUTCOME_OR_PROMISE_MARKERS):
            return False
        if not any(item in sentence for item in IMPERATIVE_SAFETY_MARKERS):
            return False
    return True


def _refined_secret_findings(draft: str) -> list[dict]:
    findings = []
    for sentence in _sentences(draft):
        if _is_negative_or_warning(sentence):
            continue
        if SECRET_RE.search(sentence) and TRANSFER_RE.search(sentence) and MODEL_DESTINATION_RE.search(sentence):
            findings.append(
                {
                    "code": "SECRET_TRANSFER_TO_MODEL_RISK",
                    "severity": "BLOCK",
                    "detail": sentence,
                }
            )
    return findings


def _refined_bypass_findings(draft: str) -> list[dict]:
    findings = []
    for sentence in _sentences(draft):
        if _is_negative_or_warning(sentence):
            continue
        if any(pattern.search(sentence) for pattern in UNSAFE_ACTION_PATTERNS):
            findings.append(
                {
                    "code": "UNSAFE_PERMISSION_OR_SECURITY_BYPASS",
                    "severity": "BLOCK",
                    "detail": sentence,
                }
            )
    return findings


def _refined_cta_findings(draft: str) -> list[dict]:
    normalized = _norm(draft)
    present = sorted(name for name, pattern in CTA_ACTION_PATTERNS.items() if pattern.search(normalized))
    if len(present) < 2:
        return []
    return [
        {
            "code": "MULTIPLE_COMMERCIAL_ACTIONS_RISK",
            "severity": "REVIEW",
            "detail": ", ".join(present),
        }
    ]


def _guarantee_findings(draft: str, packet: dict) -> list[dict]:
    normalized = _norm(draft)
    commercial = _norm(
        "\n".join(
            [packet.get("offer", ""), packet.get("cta", "")]
            + [
                item.get("claim", "")
                for item in packet.get("verified_evidence", [])
                if item.get("kind") in {"COMMERCIAL", "POLICY", "SCOPE", "TIMING"}
            ]
        )
    )
    findings = []
    for match in GUARANTEE_RE.finditer(normalized):
        phrase = match.group(0)
        if phrase not in commercial:
            findings.append(
                {
                    "code": "UNBOUND_GUARANTEE_LANGUAGE",
                    "severity": "BLOCK",
                    "detail": phrase,
                }
            )
    return findings


def _safety_language_findings(draft: str) -> list[dict]:
    findings = []
    for sentence in _sentences(draft):
        if _is_negative_or_warning(sentence):
            continue
        if ABSOLUTE_SAFETY_RE.search(sentence):
            findings.append(
                {
                    "code": "ABSOLUTE_SAFETY_LANGUAGE",
                    "severity": "REVIEW",
                    "detail": sentence,
                }
            )
    return findings


def _outcome_promise_findings(draft: str) -> list[dict]:
    findings = []
    for sentence in _sentences(draft):
        if OUTCOME_PROMISE_RE.search(sentence):
            findings.append(
                {
                    "code": "OUTCOME_PROMISE_LANGUAGE",
                    "severity": "REVIEW",
                    "detail": sentence,
                }
            )
    return findings


def _local_self_responsibility_findings(draft: str) -> list[dict]:
    normalized = _norm(draft)
    findings = []
    for match in re.finditer("自己責任", normalized):
        start = max(0, match.start() - 220)
        end = min(len(normalized), match.end() + 220)
        window = normalized[start:end]
        if not any(marker in window for marker in LOCAL_MITIGATION_MARKERS):
            findings.append(
                {
                    "code": "SELF_RESPONSIBILITY_WITHOUT_MITIGATION",
                    "severity": "REVIEW",
                    "detail": window[:180],
                }
            )
    return findings


def _refined_procedure_findings(draft: str, packet: dict) -> list[dict]:
    if packet.get("topic_mode") != "PROCEDURAL":
        return []
    normalized = _norm(draft)
    step_count = len(STEP_RE.findall(normalized))
    if step_count < 3:
        return []
    findings = []
    if not any(marker in normalized for marker in SUCCESS_MARKERS):
        findings.append(
            {
                "code": "PROCEDURE_WITHOUT_SUCCESS_SIGNAL",
                "severity": "REVIEW",
                "detail": f"{step_count} steps but no clear observable completion/success signal",
            }
        )
    if not any(marker in normalized for marker in RECOVERY_MARKERS):
        findings.append(
            {
                "code": "PROCEDURE_WITHOUT_RECOVERY_PATH",
                "severity": "REVIEW",
                "detail": f"{step_count} steps but no visible error/recovery path",
            }
        )
    if "なぜ" not in normalized and "理由" not in normalized:
        findings.append(
            {
                "code": "PROCEDURE_WITHOUT_WHY",
                "severity": "REVIEW",
                "detail": f"{step_count} steps but no rationale marker",
            }
        )
    return findings


def build_generation_packet(source: dict, *, trusted_source_refs: list[dict]) -> dict:
    packet = _round1.build_generation_packet(source, trusted_source_refs=trusted_source_refs)

    freshness_mode = packet.get("freshness", {}).get("mode", "EVERGREEN")
    if freshness_mode in {"CURRENT", "UPDATE"} and not _has_verified_dated_evidence(packet):
        raise XArticleEngineError(
            "CURRENT/UPDATE articles require verified dated/TIMING evidence; as_of alone does not establish current truth"
        )

    packet["schema_version"] = "0.9-meteor"
    packet["freshness"]["evidence_rule"] = (
        "as_of is only a scope label. It never makes a claim current by itself; CURRENT/UPDATE mode also requires verified dated/TIMING evidence."
    )
    packet["knowledge_conflict_rules"].extend(
        [
            "Safety imperatives such as '必ず確認する' are not commercial guarantees; do not over-sanitize necessary safety language.",
            "Mentioning a dangerous option in order to forbid it must not be mistaken for recommending it.",
            "Source/reference links are not commercial CTAs; CTA review should look for reader action requests rather than raw URL count.",
        ]
    )
    packet["human_gate"]["checks"].extend(
        [
            "Is as_of backed by dated verified evidence, or is it merely a date label attached to an unverified current claim?",
            "Did the safety checker mistake a prohibition ('do not share the API key') for an instruction to do the dangerous thing?",
            "Did a necessary safety imperative such as '必ず確認してください' get flattened because it contains strong wording?",
        ]
    )
    return packet


def audit_draft(draft: str, packet: dict) -> dict:
    result = _round1.audit_draft(draft, packet)

    filtered = []
    for item in result.get("findings", []):
        code = item.get("code")
        detail = str(item.get("detail", ""))

        # Round-1 CTA detector intentionally used broad tokens; replace it with action-shaped detection.
        if code == "MULTIPLE_COMMERCIAL_ACTIONS_RISK":
            continue

        # Round-1 secret/bypass detectors can see a forbidden string inside a warning. Recompute below.
        if code in {"SECRET_TRANSFER_TO_MODEL_RISK", "UNSAFE_PERMISSION_OR_SECURITY_BYPASS"}:
            if _is_negative_or_warning(detail):
                continue
            # Recomputed below with tighter patterns, so drop all round-1 copies to avoid stale false positives.
            continue

        # Round-1 self-responsibility check is article-global; replace with a local mitigation window.
        if code == "SELF_RESPONSIBILITY_WITHOUT_MITIGATION":
            continue

        # v0.2 treated every 必ず/絶対 token as a commercial strengthening. Keep the block only for outcome/promise use.
        if code == "UNBOUND_STRONG_CLAIM" and detail in {"必ず", "絶対"}:
            if _only_safety_imperative_usage(draft, detail):
                continue

        # Round-1 procedure detector only recognized STEP; replace with broader Japanese/English detection.
        if code in {"PROCEDURE_WITHOUT_SUCCESS_SIGNAL", "PROCEDURE_WITHOUT_RECOVERY_PATH", "PROCEDURE_WITHOUT_WHY"}:
            continue

        filtered.append(item)

    findings = [
        *filtered,
        *_refined_secret_findings(draft),
        *_refined_bypass_findings(draft),
        *_refined_cta_findings(draft),
        *_guarantee_findings(draft, packet),
        *_safety_language_findings(draft),
        *_outcome_promise_findings(draft),
        *_local_self_responsibility_findings(draft),
        *_refined_procedure_findings(draft, packet),
    ]

    deduped = []
    seen = set()
    for item in findings:
        key = (str(item.get("code")), str(item.get("severity")), str(item.get("detail")))
        if key not in seen:
            seen.add(key)
            deduped.append(item)

    blocked = any(item.get("severity") == "BLOCK" for item in deduped)
    review_count = sum(1 for item in deduped if item.get("severity") == "REVIEW")
    result["findings"] = deduped
    result["status"] = "BLOCKED" if blocked else "HUMAN_REVIEW_REQUIRED"
    result["meteor_v09_review_count"] = review_count
    result["meteor_v09_block_count"] = sum(1 for item in deduped if item.get("severity") == "BLOCK")
    result["meteor_v09_gate"] = "BLOCK" if blocked else ("REVIEW" if review_count else "CLEAN_BY_HEURISTIC")
    return result

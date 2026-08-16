from __future__ import annotations

import re
import unicodedata

from . import depth_market as _v08
from .core import XArticleEngineError


FRESHNESS_MARKERS = (
    "最新",
    "現在",
    "現時点",
    "最新版",
    "今の仕様",
    "今使える",
)

DATE_RE = re.compile(
    r"(?:20\d{2}[年/-](?:0?[1-9]|1[0-2])(?:[月/-](?:0?[1-9]|[12]\d|3[01])日?)?|"
    r"20\d{2}年(?:0?[1-9]|1[0-2])月時点|20\d{2}年時点)"
)

PAIN_OPENING_KINDS = {"PAIN", "FAILURE"}
CONTRARIAN_HUMAN_KINDS = {"BELIEF", "OPINION"}
RISK_EVIDENCE_KINDS = {"RISK", "SAFETY", "POLICY"}

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

OUTCOME_CONTEXT = (
    "できます",
    "できる",
    "終わります",
    "終わる",
    "完了",
    "成功",
    "売れ",
    "伸び",
    "稼げ",
    "増え",
    "安全",
    "大丈夫",
    "保証",
    "無料",
    "返金",
    "追加料金",
)

UNSAFE_ACTION_PATTERNS = (
    re.compile(r"--dangerously-skip-permissions", re.I),
    re.compile(r"(?:権限|確認|承認)[^。\n]{0,25}(?:スキップ|飛ば|省略)[^。\n]{0,20}(?:して|する|してください|で進)"),
    re.compile(r"認証[^。\n]{0,18}(?:無効|none|なし)[^。\n]{0,18}(?:にして|に設定|を選|で進)", re.I),
    re.compile(r"サンドボックス[^。\n]{0,18}(?:無効|off)[^。\n]{0,18}(?:にして|に設定|で進)", re.I),
)

AUTOMATION_OVERREACH_PATTERNS = (
    re.compile(r"ユーザーに質問せず[^。\n]{0,40}(?:全部|全て|すべて)?[^。\n]{0,20}自動"),
    re.compile(r"(?:全部|全て|すべて)[^。\n]{0,20}自動で判断"),
    re.compile(r"確認なしで[^。\n]{0,30}(?:実行|進め|操作)"),
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

ABSOLUTE_FREE_MARKERS = ("完全無料", "ずっと無料", "永久無料")
SUPERLATIVE_MARKERS = ("世界一", "唯一", "最強", "何でもでき", "全部でき")
GUARANTEE_RE = re.compile(r"(?:保証します|保証できます|保証する|確実にできます|確実に終わります)")
ABSOLUTE_SAFETY_RE = re.compile(r"(?:完全に安全|絶対安全|安全です|安心です)")
OUTCOME_PROMISE_RE = re.compile(r"(?:売れます|売れるようになります|必ず伸びる|伸びます|稼げます|稼げるようになります)")
UNIVERSAL_CAPABILITY_RE = re.compile(
    r"(?:誰でも|全員|どんな人でも|初心者でも)[^。\n]{0,35}(?:できます|できる|使えます|使える|完了できます)"
)

HARDCODED_SECRET_RE = re.compile(r"\bsk-[A-Za-z0-9_-]{8,}\b", re.I)
HARDCODED_SECRET_USE_RE = re.compile(
    r"(?:API\s*キー|key|認証)[^。\n]{0,50}(?:sk-[A-Za-z0-9_-]{8,})[^。\n]{0,40}(?:使|入力|設定|このまま)",
    re.I,
)

STEP_RE = re.compile(
    r"(?:\bSTEP\s*[0-9０-９]+\b|ステップ\s*[0-9０-９一二三四五六七八九十]+|手順\s*[0-9０-９一二三四五六七八九十]+)",
    re.I,
)
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

RISK_FRONT_MARKERS = (
    "警告",
    "危険",
    "リスク",
    "対象外",
    "進めない",
    "使わないで",
    "やめて",
    "停止",
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

ABSTRACT_MARKERS = ("構造", "設計", "本質", "重要です", "大切です", "最適化")
GENERIC_SUBJECT_MARKERS = ("多くの人は", "多くの人が", "現代人は", "誰もが", "みんなが", "一般的に")

EVASION_MARKERS = (
    "BAN回避",
    "ステルス配信",
    "判定を回避",
    "検知を回避",
    "規制を回避",
    "ゼロ幅文字",
)
EVASION_OPERATION_RE = re.compile(
    r"(?:BAN回避|ステルス配信|判定を回避|検知を回避|規制を回避|ゼロ幅文字)"
    r"[^。\n]{0,80}(?:使う|使います|入れる|実装|構築|設定|送信|配信|追加|挿入|有効化)"
)
EVASION_NEGATION_FORMS = (
    "推奨しない",
    "推奨しません",
    "推奨していない",
    "推奨していません",
    "教えない",
    "教えません",
    "扱わない",
    "扱いません",
    "使わない",
    "実行しない",
    "避ける",
    "禁止",
    "問題がある",
    "危険",
    "規約",
    "ポリシー",
)


def _norm(value: str) -> str:
    return unicodedata.normalize("NFKC", value)


def _sentences(text: str) -> list[str]:
    return [
        item.strip()
        for item in re.split(r"(?<=[。！？!?])|\n+", _norm(text))
        if item.strip()
    ]


def _commercial_text(packet: dict) -> str:
    chunks = [packet.get("offer", ""), packet.get("cta", "")]
    chunks.extend(
        item.get("claim", "")
        for item in packet.get("verified_evidence", [])
        if item.get("kind") in {"COMMERCIAL", "TIMING", "SCOPE", "POLICY"}
    )
    return "\n".join(chunks)


def _has_dated_verified_evidence(packet: dict) -> bool:
    return any(
        item.get("kind") == "TIMING" or DATE_RE.search(_norm(item.get("claim", "")))
        for item in packet.get("verified_evidence", [])
    )


def _has_risk_evidence(packet: dict) -> bool:
    return any(item.get("kind") in RISK_EVIDENCE_KINDS for item in packet.get("verified_evidence", []))


def _is_negative_or_warning(sentence: str) -> bool:
    normalized = _norm(sentence)
    return any(marker in normalized for marker in NEGATION_OR_WARNING)


def _only_safety_imperative_usage(draft: str, marker: str) -> bool:
    matched = [sentence for sentence in _sentences(draft) if marker in sentence]
    if not matched:
        return False
    for sentence in matched:
        if any(item in sentence for item in OUTCOME_CONTEXT):
            return False
        if not any(item in sentence for item in IMPERATIVE_SAFETY_MARKERS):
            return False
    return True


def _contrarian_basis_is_valid(source: dict, packet: dict) -> bool:
    basis = source.get("counterpoint_basis")
    if not isinstance(basis, dict):
        return False
    kind = str(basis.get("kind", "")).strip().upper()
    source_ref = str(basis.get("source_ref", "")).strip()
    if not source_ref:
        return False
    if kind == "HUMAN_OPINION":
        return any(
            item.get("source_ref") == source_ref and item.get("kind") in CONTRARIAN_HUMAN_KINDS
            for item in packet.get("verified_primary_info", [])
        )
    if kind == "EVIDENCE":
        return any(item.get("source_ref") == source_ref for item in packet.get("verified_evidence", []))
    return False


def _freshness_findings(draft: str, packet: dict) -> list[dict]:
    normalized = _norm(draft)
    if not any(marker in normalized for marker in FRESHNESS_MARKERS):
        return []
    if _has_dated_verified_evidence(packet):
        return []
    return [
        {
            "code": "FRESHNESS_CLAIM_WITHOUT_DATED_EVIDENCE",
            "severity": "REVIEW",
            "detail": "current/latest wording requires dated verified evidence; an as_of label alone is not evidence",
        }
    ]


def _unsafe_bypass_findings(draft: str) -> list[dict]:
    findings: list[dict] = []
    for sentence in _sentences(draft):
        if _is_negative_or_warning(sentence):
            continue
        if any(pattern.search(sentence) for pattern in UNSAFE_ACTION_PATTERNS):
            findings.append(
                {"code": "UNSAFE_PERMISSION_OR_SECURITY_BYPASS", "severity": "BLOCK", "detail": sentence}
            )
    return findings


def _automation_overreach_findings(draft: str) -> list[dict]:
    findings: list[dict] = []
    for sentence in _sentences(draft):
        if _is_negative_or_warning(sentence):
            continue
        if any(pattern.search(sentence) for pattern in AUTOMATION_OVERREACH_PATTERNS):
            findings.append(
                {"code": "AUTOMATION_WITHOUT_HUMAN_CHECKPOINT", "severity": "REVIEW", "detail": sentence}
            )
    return findings


def _secret_transfer_findings(draft: str) -> list[dict]:
    findings: list[dict] = []
    for sentence in _sentences(draft):
        if _is_negative_or_warning(sentence):
            continue
        if SECRET_RE.search(sentence) and TRANSFER_RE.search(sentence) and MODEL_DESTINATION_RE.search(sentence):
            findings.append({"code": "SECRET_TRANSFER_TO_MODEL_RISK", "severity": "BLOCK", "detail": sentence})
    return findings


def _cta_findings(draft: str) -> list[dict]:
    normalized = _norm(draft)
    present = sorted(name for name, pattern in CTA_ACTION_PATTERNS.items() if pattern.search(normalized))
    if len(present) < 2:
        return []
    return [
        {"code": "MULTIPLE_COMMERCIAL_ACTIONS_RISK", "severity": "REVIEW", "detail": ", ".join(present)}
    ]


def _warning_fatigue_findings(draft: str) -> list[dict]:
    normalized = _norm(draft)
    count = normalized.count("超重要") + normalized.count("警告")
    if count < 6:
        return []
    return [
        {"code": "WARNING_FATIGUE_RISK", "severity": "REVIEW", "detail": f"strong warning markers repeated {count} times"}
    ]


def _self_responsibility_findings(draft: str) -> list[dict]:
    normalized = _norm(draft)
    findings: list[dict] = []
    for match in re.finditer("自己責任", normalized):
        start = max(0, match.start() - 220)
        end = min(len(normalized), match.end() + 220)
        window = normalized[start:end]
        if not any(marker in window for marker in LOCAL_MITIGATION_MARKERS):
            findings.append(
                {"code": "SELF_RESPONSIBILITY_WITHOUT_MITIGATION", "severity": "REVIEW", "detail": window[:180]}
            )
    return findings


def _absolute_free_findings(draft: str, packet: dict) -> list[dict]:
    normalized = _norm(draft)
    bound = _norm(_commercial_text(packet))
    return [
        {"code": "UNBOUND_ABSOLUTE_FREE_CLAIM", "severity": "BLOCK", "detail": marker}
        for marker in ABSOLUTE_FREE_MARKERS
        if marker in normalized and marker not in bound
    ]


def _superlative_findings(draft: str) -> list[dict]:
    normalized = _norm(draft)
    present = sorted({marker for marker in SUPERLATIVE_MARKERS if marker in normalized})
    if not present:
        return []
    return [
        {"code": "SUPERLATIVE_OR_TOTALIZING_LANGUAGE", "severity": "REVIEW", "detail": ", ".join(present)}
    ]


def _guarantee_findings(draft: str, packet: dict) -> list[dict]:
    normalized = _norm(draft)
    commercial = _norm(_commercial_text(packet))
    return [
        {"code": "UNBOUND_GUARANTEE_LANGUAGE", "severity": "BLOCK", "detail": match.group(0)}
        for match in GUARANTEE_RE.finditer(normalized)
        if match.group(0) not in commercial
    ]


def _safety_language_findings(draft: str) -> list[dict]:
    findings: list[dict] = []
    for sentence in _sentences(draft):
        if _is_negative_or_warning(sentence):
            continue
        if ABSOLUTE_SAFETY_RE.search(sentence):
            findings.append({"code": "ABSOLUTE_SAFETY_LANGUAGE", "severity": "REVIEW", "detail": sentence})
    return findings


def _outcome_promise_findings(draft: str) -> list[dict]:
    return [
        {"code": "OUTCOME_PROMISE_LANGUAGE", "severity": "REVIEW", "detail": sentence}
        for sentence in _sentences(draft)
        if OUTCOME_PROMISE_RE.search(sentence)
    ]


def _universal_capability_findings(draft: str) -> list[dict]:
    return [
        {"code": "UNIVERSAL_CAPABILITY_PROMISE", "severity": "REVIEW", "detail": match.group(0)}
        for match in UNIVERSAL_CAPABILITY_RE.finditer(_norm(draft))
    ]


def _hardcoded_secret_findings(draft: str) -> list[dict]:
    findings: list[dict] = []
    for sentence in _sentences(draft):
        if not HARDCODED_SECRET_RE.search(sentence):
            continue
        if any(token in sentence for token in ("例", "ダミー", "placeholder", "プレースホルダー", "使わない", "禁止")):
            continue
        if HARDCODED_SECRET_USE_RE.search(sentence):
            findings.append({"code": "HARDCODED_SECRET_LITERAL_RISK", "severity": "BLOCK", "detail": sentence})
    return findings


def _procedure_findings(draft: str, packet: dict) -> list[dict]:
    if packet.get("topic_mode") != "PROCEDURAL":
        return []
    normalized = _norm(draft)
    step_count = len(STEP_RE.findall(normalized))
    if step_count < 3:
        return []
    findings: list[dict] = []
    if not any(marker in normalized for marker in SUCCESS_MARKERS):
        findings.append(
            {"code": "PROCEDURE_WITHOUT_SUCCESS_SIGNAL", "severity": "REVIEW", "detail": f"{step_count} steps but no clear observable completion/success signal"}
        )
    if not any(marker in normalized for marker in RECOVERY_MARKERS):
        findings.append(
            {"code": "PROCEDURE_WITHOUT_RECOVERY_PATH", "severity": "REVIEW", "detail": f"{step_count} steps but no visible error/recovery path"}
        )
    if "なぜ" not in normalized and "理由" not in normalized:
        findings.append(
            {"code": "PROCEDURE_WITHOUT_WHY", "severity": "REVIEW", "detail": f"{step_count} steps but no rationale marker"}
        )
    return findings


def _high_risk_front_findings(draft: str, packet: dict) -> list[dict]:
    if packet.get("risk_policy", {}).get("risk_level") != "HIGH":
        return []
    front = _norm(draft)[:700]
    if any(marker in front for marker in RISK_FRONT_MARKERS):
        return []
    return [
        {
            "code": "HIGH_RISK_WITHOUT_FRONT_STOP_GATE",
            "severity": "BLOCK",
            "detail": "high-risk guide begins without a visible risk/stop boundary near the front",
        }
    ]


def _generic_abstract_collision_findings(draft: str) -> list[dict]:
    findings: list[dict] = []
    for sentence in _sentences(draft):
        subjects = [marker for marker in GENERIC_SUBJECT_MARKERS if marker in sentence]
        abstracts = [marker for marker in ABSTRACT_MARKERS if marker in sentence]
        if subjects and abstracts:
            findings.append(
                {
                    "code": "ABSTRACT_WORD_WITHOUT_PAYLOAD",
                    "severity": "REVIEW",
                    "detail": sentence,
                    "markers": abstracts,
                }
            )
    return findings


def _evasion_findings(draft: str) -> list[dict]:
    findings: list[dict] = []
    for sentence in _sentences(draft):
        if not any(marker in sentence for marker in EVASION_MARKERS):
            continue
        if any(marker in sentence for marker in EVASION_NEGATION_FORMS):
            findings.append({"code": "PLATFORM_EVASION_LANGUAGE", "severity": "REVIEW", "detail": sentence})
            continue
        if EVASION_OPERATION_RE.search(sentence):
            findings.append(
                {"code": "PLATFORM_EVASION_OPERATIONAL_INSTRUCTION", "severity": "BLOCK", "detail": sentence}
            )
        else:
            findings.append({"code": "PLATFORM_EVASION_LANGUAGE", "severity": "REVIEW", "detail": sentence})
    return findings


def _absolute_generalization_findings(draft: str, markers: set[str]) -> list[dict]:
    findings: list[dict] = []
    for marker in markers:
        for sentence in _sentences(draft):
            if marker not in sentence:
                continue
            if any(context in sentence for context in OUTCOME_CONTEXT):
                continue
            findings.append({"code": "ABSOLUTE_GENERALIZATION_LANGUAGE", "severity": "REVIEW", "detail": sentence})
    return findings


def build_generation_packet(source: dict, *, trusted_source_refs: list[dict]) -> dict:
    if not isinstance(source, dict):
        raise XArticleEngineError("source must be an object")

    risk_level = str(source.get("risk_level", "STANDARD")).strip().upper()
    if risk_level not in {"STANDARD", "ELEVATED", "HIGH"}:
        raise XArticleEngineError("risk_level must be STANDARD, ELEVATED, or HIGH")

    freshness_mode = str(source.get("freshness_mode", "EVERGREEN")).strip().upper()
    if freshness_mode not in {"EVERGREEN", "CURRENT", "UPDATE"}:
        raise XArticleEngineError("freshness_mode must be EVERGREEN, CURRENT, or UPDATE")
    as_of = source.get("as_of")
    if freshness_mode in {"CURRENT", "UPDATE"} and (not isinstance(as_of, str) or not as_of.strip()):
        raise XArticleEngineError("CURRENT/UPDATE articles require a non-empty as_of boundary")

    explicit_opening = source.get("opening_mode")
    packet = _v08.build_generation_packet(source, trusted_source_refs=trusted_source_refs)

    packet["freshness"] = {
        "mode": freshness_mode,
        "as_of": as_of.strip() if isinstance(as_of, str) else None,
        "rule": "Current product/platform facts decay; preserve date/scope and re-verify them.",
        "evidence_rule": "as_of is only a scope label; CURRENT/UPDATE also requires verified dated/TIMING evidence.",
        "supersession_rule": "For UPDATE articles, say what changed, what survives, what is obsolete, and whether migration is needed.",
    }
    if freshness_mode in {"CURRENT", "UPDATE"} and not _has_dated_verified_evidence(packet):
        raise XArticleEngineError(
            "CURRENT/UPDATE articles require verified dated/TIMING evidence; as_of alone does not establish current truth"
        )

    packet["risk_policy"] = {
        "risk_level": risk_level,
        "front_gate_rule": "For HIGH-risk material, state verified risk, who should not proceed, and the stop/safer path before operational instructions.",
        "evidence_rule": "HIGH-risk mode requires verified RISK/SAFETY/POLICY evidence.",
        "anti_disclaimer_rule": "A disclaimer or 自己責任 sentence is not a substitute for concrete mitigation.",
        "safety_asset_rule": "Safety-critical information may not be hidden behind registration, payment, or another CTA.",
    }
    if risk_level == "HIGH" and not _has_risk_evidence(packet):
        raise XArticleEngineError(
            "HIGH-risk articles require at least one verified RISK/SAFETY/POLICY evidence claim; warning tone alone is not evidence"
        )

    pain_anchors = [
        item for item in packet.get("verified_primary_info", []) if item.get("kind") in PAIN_OPENING_KINDS
    ]
    if packet.get("opening_mode") == "LIVED_PAIN" and not pain_anchors:
        if explicit_opening is not None:
            raise XArticleEngineError(
                "LIVED_PAIN in v0.9 requires human-attested PAIN or FAILURE; ORIGIN alone cannot authorize a pain opening"
            )
        packet["opening_mode"] = "RELATABLE"
        packet["lived_pain_anchors"] = []
        packet["narrative"]["sequence"] = [
            "reader_state",
            "evidence_if_available",
            "anticipated_objection",
            "cause",
            "solution",
            "stumbling_point",
            "one_action_today",
            "single_cta",
        ]
        packet["narrative"]["opening_doctrine"] = (
            "An attested origin may explain why the article exists, but do not manufacture pain from origin alone."
        )

    if packet.get("opening_mode") == "CONTRARIAN" and not _contrarian_basis_is_valid(source, packet):
        raise XArticleEngineError(
            "CONTRARIAN opening requires counterpoint_basis bound to verified evidence or a human-attested BELIEF/OPINION"
        )

    packet["schema_version"] = "0.9"
    packet["decision_then_path_policy"] = {
        "principle": "Compare only material differences before a consequential choice; after a safe choice, collapse to one main path.",
        "anti_overchoice": "Do not hand beginners a menu of equivalent methods when one safe default is enough.",
        "anti_hidden_tradeoff": "Do not hide a material risk or trade-off merely to preserve a one-path experience.",
    }
    packet["completion_design_policy"] = {
        "step_schema": ["GOAL", "ACTION", "EXPECTED_SIGNAL", "RECOVERY", "WHY_WHEN_NEEDED"],
        "progress_rule": "Show current position, observable success, and what remains in long procedures.",
        "micro_completion_rule": "Use real completion signals, not fake praise or gamification.",
        "first_real_win_rule": "After setup, move quickly to one small meaningful use.",
    }
    packet["human_automation_boundary"] = {
        "human_only_or_human_confirmed": [
            "secrets/credentials",
            "permission expansion/security bypass",
            "irreversible or high-impact actions",
            "final high-risk judgment",
            "publication authority",
        ],
        "rule": "Automation may reduce repetition but must preserve human authorization, verification, stop, and recovery points.",
    }
    packet["pain_to_promise_policy"] = {
        "principle": "Let an attested frustration shape the article promise, but do not upgrade it into an unverified guarantee.",
        "mapping": "friction -> concrete promise -> mechanism -> evidence/conditions -> next action",
    }
    packet["strong_language_policy"] = {
        "outcome_absolute": "BLOCK when unbound.",
        "general_absolute": "REVIEW broad predictions/generalizations.",
        "safety_imperative": "ALLOW genuinely protective strong wording.",
    }
    packet["opening_integrity_policy"] = {
        "lived_pain_rule": "LIVED_PAIN requires actual attested PAIN or FAILURE; ORIGIN alone is not pain.",
        "contrarian_rule": "CONTRARIAN requires explicit evidence-bound or human-attested counterpoint_basis.",
        "anti_forcing_rule": "Opening mode follows available material; successful reference patterns do not authorize forced drama/proof/contrarianism.",
    }
    packet["security_content_policy"] = {
        "hardcoded_secret_rule": "Do not normalize a reusable secret literal as a default public credential.",
        "platform_evasion_rule": "Discussion of evasion requires review; operational evasion instructions are blocked.",
        "evasion_negation_rule": "Recognize Japanese negative forms including polite forms before classifying discussion as operational instruction.",
    }
    packet["anti_ai_smell_policy"]["generic_abstract_collision_rule"] = (
        "A generic subject such as 多くの人 must not make 構造/設計/本質 look concrete."
    )
    packet["knowledge_conflict_rules"] = [
        "Specificity never overrides evidence binding.",
        "Beginner simplicity never hides a material trade-off or risk.",
        "One-path guidance begins after the decision that matters.",
        "Long-form depth never justifies padding.",
        "Strong voice never authorizes fabricated certainty, biography, or guarantees.",
        "CTA usefulness never authorizes fake scarcity, fear, or competing actions.",
        "Currentness never survives its evidence date automatically.",
        "Safety information outranks CTA optimization.",
        "Human authorization outranks automation convenience.",
        "ORIGIN alone does not authorize LIVED_PAIN.",
        "Contrarianism requires an explicit basis.",
    ]

    packet["generation_constraints"].extend(
        [
            "For time-sensitive product/platform claims, preserve as_of and re-verify currentness; do not recycle old UI, price, model, availability, limit, or recommendation claims as timeless truth.",
            "Before a consequential choice, show material differences; after the choice, use one primary path unless a new material risk requires branching.",
            "For procedures, pair important actions with observable success and nearby recovery; explain WHY where it affects judgment, safety, transfer, or troubleshooting.",
            "Do not instruct readers to bypass permission/security controls or paste secrets/credentials into model chat as a normal workflow.",
            "Do not use 自己責任 or fear language as substitutes for mitigation, stop conditions, least privilege, or recovery.",
            "For HIGH-risk tutorials, put verified risk/stop boundaries before operational steps; never hide safety-critical information behind a CTA.",
            "A CTA may appear at the next predictable wall but must remain one coherent continuation rather than multiple competing actions.",
            "Classify 必ず/絶対 by meaning: unbound outcome guarantees block; broad predictions review; genuine safety imperatives may stay strong.",
            "Do not use reusable hard-coded secret/API keys as the normal public setup path.",
            "Do not provide operational instructions for BAN/detection/enforcement evasion.",
            "Do not treat ORIGIN as pain unless the human also attested PAIN or FAILURE.",
            "Do not manufacture a contrarian opening; require an explicit evidence-bound or human-attested counterpoint basis.",
            "Do not count generic words such as 人 as concrete payload for an otherwise empty 構造/設計/本質 sentence.",
        ]
    )
    packet["human_gate"]["checks"].extend(
        [
            "If this article says 最新・現在・現時点, what dated verified evidence makes that true now?",
            "Did I reuse an old UI path, plan, price, model, comparison, or recommendation after the product changed?",
            "Before the path became one-way, did I expose the material choice/risk that required a decision?",
            "For each important procedure, can the reader tell what success looks like and what to do if it does not happen?",
            "Did any instruction ask the reader to bypass permissions, weaken security, or give a secret/credential to an AI model for convenience?",
            "If I wrote 自己責任 or a warning, did I also give concrete mitigation, a stop condition, and a recovery path?",
            "Is any safety-critical information being withheld until after signup/payment/CTA?",
            "How many different commercial actions does the draft ask for? Can they be reduced to the single intended next step?",
            "Does the CTA appear at a real next wall, or was a wall manufactured to justify it?",
            "Does automation stop where a human must authorize, verify, judge, or recover?",
            "Is a strong 必ず/絶対 sentence an outcome guarantee, a broad prediction, or a necessary safety prohibition?",
            "Does any tutorial publish a reusable secret literal or predictable default credential?",
            "Does any advice rely on platform-evasion behavior rather than compliant operation?",
            "For HIGH-risk content, which verified evidence supports the actual risk?",
            "Is the opening emotion actually present in PAIN/FAILURE, or did the draft turn neutral origin into drama?",
            "If the opening is contrarian, what exact evidence or human belief/opinion is it based on?",
            "権限・安全・自動化の説明で、禁止や停止条件を危険な実行指示として誤読していないか？",
        ]
    )
    return packet


def audit_draft(draft: str, packet: dict) -> dict:
    result = _v08.audit_draft(draft, packet)
    filtered: list[dict] = []
    downgraded_absolute_markers: set[str] = set()

    for item in result.get("findings", []):
        code = item.get("code")
        detail = str(item.get("detail", ""))
        if code == "UNBOUND_STRONG_CLAIM" and detail in {"必ず", "絶対"}:
            if _only_safety_imperative_usage(draft, detail):
                continue
            matching_sentences = [sentence for sentence in _sentences(draft) if detail in sentence]
            if matching_sentences and not any(
                any(context in sentence for context in OUTCOME_CONTEXT) for sentence in matching_sentences
            ):
                downgraded_absolute_markers.add(detail)
                continue
        filtered.append(item)

    findings = [
        *filtered,
        *_freshness_findings(draft, packet),
        *_unsafe_bypass_findings(draft),
        *_automation_overreach_findings(draft),
        *_secret_transfer_findings(draft),
        *_cta_findings(draft),
        *_warning_fatigue_findings(draft),
        *_self_responsibility_findings(draft),
        *_absolute_free_findings(draft, packet),
        *_superlative_findings(draft),
        *_guarantee_findings(draft, packet),
        *_safety_language_findings(draft),
        *_outcome_promise_findings(draft),
        *_universal_capability_findings(draft),
        *_hardcoded_secret_findings(draft),
        *_procedure_findings(draft, packet),
        *_high_risk_front_findings(draft, packet),
        *_generic_abstract_collision_findings(draft),
        *_evasion_findings(draft),
        *_absolute_generalization_findings(draft, downgraded_absolute_markers),
    ]

    deduped: list[dict] = []
    seen: set[tuple[str, str, str]] = set()
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

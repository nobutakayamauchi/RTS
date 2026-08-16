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

DATED_EVIDENCE_RE = re.compile(
    r"(?:20\d{2}[年/-](?:0?[1-9]|1[0-2])(?:[月/-](?:0?[1-9]|[12]\d|3[01])日?)?|"
    r"20\d{2}年(?:0?[1-9]|1[0-2])月時点|"
    r"20\d{2}年時点)"
)

WARNING_CONTEXT_MARKERS = (
    "使わない",
    "使用しない",
    "しないで",
    "禁止",
    "避け",
    "危険",
    "やめ",
    "ダメ",
    "してはいけ",
    "無効にしない",
    "スキップしない",
)

UNSAFE_BYPASS_PATTERNS = (
    re.compile(r"--dangerously-skip-permissions", re.I),
    re.compile(r"(?:権限|確認|承認)[^。\n]{0,25}(?:スキップ|飛ば|省略)"),
    re.compile(r"認証[^。\n]{0,20}(?:無効|なし|none)", re.I),
    re.compile(r"サンドボックス[^。\n]{0,20}(?:無効|off)", re.I),
)

AUTOMATION_OVERREACH_PATTERNS = (
    re.compile(r"ユーザーに質問せず[^。\n]{0,40}(?:全部|全て|すべて)?[^。\n]{0,20}自動"),
    re.compile(r"(?:全部|全て|すべて)[^。\n]{0,20}自動で判断"),
    re.compile(r"確認なしで[^。\n]{0,30}(?:実行|進め|操作)"),
)

SECRET_MARKERS = (
    "APIキー",
    "API key",
    "シークレット",
    "secret",
    "アクセストークン",
    "トークン",
    "パスワード",
    "認証情報",
    "クレジットカード",
)

SECRET_TRANSFER_MARKERS = (
    "貼り付け",
    "貼って",
    "送信",
    "送って",
    "渡して",
    "コピペ",
    "入力して",
)

AI_TARGET_MARKERS = (
    "AI",
    "Claude",
    "ChatGPT",
    "Codex",
    "プロンプト",
    "チャット",
)

CTA_MARKERS = (
    "購入",
    "申し込",
    "参加",
    "登録",
    "友だち追加",
    "フォロー",
    "リプ",
    "DM",
    "無料相談",
    "無料確認",
    "無料適合確認",
    "資料請求",
)

ABSOLUTE_FREE_MARKERS = (
    "完全無料",
    "ずっと無料",
    "永久無料",
)

SUPERLATIVE_MARKERS = (
    "世界一",
    "唯一",
    "最強",
    "何でもでき",
    "全部でき",
)

PROGRESS_SIGNAL_MARKERS = (
    "成功",
    "完了",
    "表示されたら",
    "表示されれば",
    "確認してください",
    "確認でき",
    "できていれば",
    "見えれば",
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

MITIGATION_MARKERS = (
    "停止",
    "戻",
    "バックアップ",
    "確認",
    "権限",
    "テスト",
    "サンドボックス",
    "対象外",
    "人間",
)


def _norm(value: str) -> str:
    return unicodedata.normalize("NFKC", value)


def _sentences(text: str) -> list[str]:
    return [
        item.strip()
        for item in re.split(r"(?<=[。！？!?])|\n+", _norm(text))
        if item.strip()
    ]


def _is_warning_context(sentence: str) -> bool:
    normalized = _norm(sentence)
    return any(marker in normalized for marker in WARNING_CONTEXT_MARKERS)


def _commercial_text(packet: dict) -> str:
    chunks = [packet.get("offer", ""), packet.get("cta", "")]
    chunks.extend(
        item.get("claim", "")
        for item in packet.get("verified_evidence", [])
        if item.get("kind") in {"COMMERCIAL", "TIMING", "SCOPE", "POLICY"}
    )
    return "\n".join(chunks)


def _has_dated_evidence(packet: dict) -> bool:
    for item in packet.get("verified_evidence", []):
        if item.get("kind") == "TIMING":
            return True
        if DATED_EVIDENCE_RE.search(_norm(item.get("claim", ""))):
            return True
    return bool(packet.get("freshness", {}).get("as_of"))


def _freshness_findings(draft: str, packet: dict) -> list[dict]:
    normalized = _norm(draft)
    if not any(marker in normalized for marker in FRESHNESS_MARKERS):
        return []
    if _has_dated_evidence(packet):
        return []
    return [
        {
            "code": "FRESHNESS_CLAIM_WITHOUT_DATED_EVIDENCE",
            "severity": "REVIEW",
            "detail": "draft uses current/latest language but packet has no dated/timing evidence or as_of boundary",
        }
    ]


def _unsafe_bypass_findings(draft: str) -> list[dict]:
    findings: list[dict] = []
    for sentence in _sentences(draft):
        if _is_warning_context(sentence):
            continue
        for pattern in UNSAFE_BYPASS_PATTERNS:
            if pattern.search(sentence):
                findings.append(
                    {
                        "code": "UNSAFE_PERMISSION_OR_SECURITY_BYPASS",
                        "severity": "BLOCK",
                        "detail": sentence,
                    }
                )
                break
    return findings


def _automation_overreach_findings(draft: str) -> list[dict]:
    findings: list[dict] = []
    for sentence in _sentences(draft):
        if _is_warning_context(sentence):
            continue
        if any(pattern.search(sentence) for pattern in AUTOMATION_OVERREACH_PATTERNS):
            findings.append(
                {
                    "code": "AUTOMATION_WITHOUT_HUMAN_CHECKPOINT",
                    "severity": "REVIEW",
                    "detail": sentence,
                }
            )
    return findings


def _secret_transfer_findings(draft: str) -> list[dict]:
    findings: list[dict] = []
    for sentence in _sentences(draft):
        if _is_warning_context(sentence):
            continue
        normalized = _norm(sentence)
        if not any(marker.lower() in normalized.lower() for marker in SECRET_MARKERS):
            continue
        if not any(marker in normalized for marker in SECRET_TRANSFER_MARKERS):
            continue
        if not any(marker.lower() in normalized.lower() for marker in AI_TARGET_MARKERS):
            continue
        findings.append(
            {
                "code": "SECRET_TRANSFER_TO_MODEL_RISK",
                "severity": "BLOCK",
                "detail": sentence,
            }
        )
    return findings


def _multi_cta_findings(draft: str) -> list[dict]:
    normalized = _norm(draft)
    present = sorted({marker for marker in CTA_MARKERS if marker in normalized})
    if len(present) < 3:
        return []
    return [
        {
            "code": "MULTIPLE_COMMERCIAL_ACTIONS_RISK",
            "severity": "REVIEW",
            "detail": ", ".join(present),
        }
    ]


def _warning_fatigue_findings(draft: str) -> list[dict]:
    normalized = _norm(draft)
    count = normalized.count("超重要") + normalized.count("警告")
    if count < 6:
        return []
    return [
        {
            "code": "WARNING_FATIGUE_RISK",
            "severity": "REVIEW",
            "detail": f"strong warning markers repeated {count} times",
        }
    ]


def _self_responsibility_findings(draft: str) -> list[dict]:
    normalized = _norm(draft)
    if "自己責任" not in normalized:
        return []
    if any(marker in normalized for marker in MITIGATION_MARKERS):
        return []
    return [
        {
            "code": "SELF_RESPONSIBILITY_WITHOUT_MITIGATION",
            "severity": "REVIEW",
            "detail": "自己責任 appears without a concrete stop, recovery, permission, test, or mitigation path",
        }
    ]


def _absolute_free_findings(draft: str, packet: dict) -> list[dict]:
    normalized = _norm(draft)
    bound = _norm(_commercial_text(packet))
    findings: list[dict] = []
    for marker in ABSOLUTE_FREE_MARKERS:
        if marker in normalized and marker not in bound:
            findings.append(
                {
                    "code": "UNBOUND_ABSOLUTE_FREE_CLAIM",
                    "severity": "BLOCK",
                    "detail": marker,
                }
            )
    return findings


def _superlative_findings(draft: str) -> list[dict]:
    normalized = _norm(draft)
    present = sorted({marker for marker in SUPERLATIVE_MARKERS if marker in normalized})
    if not present:
        return []
    return [
        {
            "code": "SUPERLATIVE_OR_TOTALIZING_LANGUAGE",
            "severity": "REVIEW",
            "detail": ", ".join(present),
        }
    ]


def _procedural_completion_findings(draft: str, packet: dict) -> list[dict]:
    if packet.get("topic_mode") != "PROCEDURAL":
        return []
    normalized = _norm(draft)
    step_count = len(re.findall(r"\bSTEP\s*\d+\b", normalized, flags=re.I))
    if step_count < 3:
        return []
    findings: list[dict] = []
    if not any(marker in normalized for marker in PROGRESS_SIGNAL_MARKERS):
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


def _risk_front_gate_findings(draft: str, packet: dict) -> list[dict]:
    if packet.get("risk_policy", {}).get("risk_level") != "HIGH":
        return []
    front = _norm(draft)[:700]
    if any(marker in front for marker in RISK_FRONT_MARKERS):
        return []
    return [
        {
            "code": "HIGH_RISK_WITHOUT_FRONT_STOP_GATE",
            "severity": "BLOCK",
            "detail": "high-risk guide begins procedural/persuasive content without a visible risk/stop boundary near the front",
        }
    ]


def _semantic_attack_findings(draft: str, packet: dict) -> list[dict]:
    return [
        *_freshness_findings(draft, packet),
        *_unsafe_bypass_findings(draft),
        *_automation_overreach_findings(draft),
        *_secret_transfer_findings(draft),
        *_multi_cta_findings(draft),
        *_warning_fatigue_findings(draft),
        *_self_responsibility_findings(draft),
        *_absolute_free_findings(draft, packet),
        *_superlative_findings(draft),
        *_procedural_completion_findings(draft, packet),
        *_risk_front_gate_findings(draft, packet),
    ]


def build_generation_packet(source: dict, *, trusted_source_refs: list[dict]) -> dict:
    """Synthesize v0.9 knowledge and METEOR hardening on top of v0.8."""
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

    packet = _v08.build_generation_packet(source, trusted_source_refs=trusted_source_refs)
    packet["schema_version"] = "0.9-candidate"

    packet["freshness"] = {
        "mode": freshness_mode,
        "as_of": as_of.strip() if isinstance(as_of, str) else None,
        "rule": (
            "Current product/platform instructions, prices, UI locations, model names, availability, limits, and comparisons decay. "
            "Preserve an as-of boundary and re-verify them instead of reusing an old article's answer."
        ),
        "supersession_rule": (
            "For UPDATE articles, say what changed, which old steps still survive, which old steps are obsolete, and whether an existing reader must migrate."
        ),
    }

    packet["decision_then_path_policy"] = {
        "principle": (
            "Before a consequential choice, compare only the differences needed to decide. After a safe choice is made, collapse the tutorial to one main path."
        ),
        "pre_decision": "Show material trade-offs, scope, reader fit, and migration cost when they affect the choice.",
        "post_decision": "Do not keep reopening alternatives inside a zero-to-first-success path unless a new material risk appears.",
        "anti_overchoice": "Do not hand a beginner a menu of equivalent methods when the article can safely recommend one default.",
        "anti_hidden_tradeoff": "Do not hide an important risk or limitation merely to preserve a one-path experience.",
    }

    packet["completion_design_policy"] = {
        "step_schema": ["GOAL", "ACTION", "EXPECTED_SIGNAL", "RECOVERY", "WHY_WHEN_NEEDED"],
        "progress_rule": "Show where the reader is, what success looks like, and what remains when the procedure is long.",
        "micro_completion_rule": "Use real completion signals and small wins, not fake gamification or praise disconnected from an observable result.",
        "first_real_win_rule": "After setup, move quickly to one small meaningful use so the reader experiences capability rather than merely installation.",
    }

    packet["risk_policy"] = {
        "risk_level": risk_level,
        "front_gate_rule": (
            "For HIGH-risk material, state the meaningful risk, who should not proceed, and the stop/safer path before operational instructions."
        ),
        "minimum_safe_path": [
            "scope/exclusion before action",
            "least-privilege or smallest safe test where applicable",
            "observable confirmation",
            "human checkpoint for permissions, secrets, irreversible actions, and high-impact judgment",
            "stop/recovery path before or next to the dangerous step",
        ],
        "anti_disclaimer_rule": "A disclaimer or 自己責任 sentence is not a substitute for concrete mitigation.",
        "safety_asset_rule": "Safety-critical information may not be hidden behind registration, payment, or another CTA.",
    }

    packet["human_automation_boundary"] = {
        "human_only_or_human_confirmed": [
            "sharing or entering secrets/credentials into a model",
            "permission expansion or security-control bypass",
            "irreversible/high-impact actions",
            "final high-risk judgment",
            "publication authority",
        ],
        "good_automation_candidates": [
            "bounded transformation",
            "repetitive setup with verified inputs and observable outputs",
            "checks that can fail closed",
            "drafting where a human retains final judgment",
        ],
        "rule": (
            "Automation should reduce repetitive work without erasing the point where a human must authorize, verify, stop, or recover."
        ),
    }

    packet["pain_to_promise_policy"] = {
        "principle": (
            "When the writer has an attested frustration or failure, let the article promise directly answer that friction. "
            "Do not turn that promise into an unverified guarantee."
        ),
        "mapping": "reader/writer friction -> concrete promise -> mechanism -> evidence/conditions -> next action",
    }

    packet["article_component_roles"] = {
        "title_and_feed_preview": "earn the tap without an unbound outcome promise",
        "opening": "make the intended reader's reason to continue legible using evidence or attested experience",
        "body": "create understanding, usable progress, and decision logic",
        "cta": "offer one coherent continuation rather than retrofitting an unrelated promotion",
        "status": "heuristic, not a rigid universal template",
    }

    packet["knowledge_conflict_rules"] = [
        "Specificity never overrides evidence binding.",
        "Beginner simplicity never hides a material trade-off or risk.",
        "One-path guidance begins after a necessary decision, not before it.",
        "Long-form depth never justifies padding.",
        "Strong voice never authorizes fabricated certainty, biography, or guarantees.",
        "A useful desire peak never authorizes fake scarcity, fear, or multiple competing commercial actions.",
        "Currentness never survives its evidence date automatically; re-verify time-sensitive claims.",
        "Safety information outranks CTA optimization.",
        "Human authorization outranks automation convenience.",
    ]

    packet["generation_constraints"].extend(
        [
            "For time-sensitive product/platform claims, state or preserve an as-of boundary and re-verify currentness; do not recycle an old article's model names, prices, UI, availability, limits, or recommended path as timeless truth.",
            "When a reader must choose between materially different paths, compare only the differences needed for the decision; after the choice, use one primary path to first success unless a material risk requires branching.",
            "For procedural articles, pair important actions with an observable success signal and a nearby recovery path; explain WHY where it affects judgment, safety, transfer, or troubleshooting.",
            "Do not instruct readers to bypass permission/security controls merely to reduce friction. Do not tell them to paste secrets or credentials into a model/chat as a normal workflow.",
            "Do not use 自己責任, disclaimers, or fear language as substitutes for concrete mitigation, stop conditions, least-privilege handling, or recovery.",
            "For high-risk tutorials, put the risk/stop boundary before operational steps and give an easier/safer alternative when appropriate.",
            "Do not hide safety-critical instructions behind a LINE signup, paid download, bonus, or other CTA.",
            "A CTA may appear at the next predictable wall, but it must remain a continuation of the article and must not compete with multiple follow/register/reply/buy actions.",
            "If a strong frustration or failure defines the article, make the article promise answer that frustration directly without upgrading it into an absolute completion or outcome guarantee.",
            "Treat superlatives such as 世界一, 唯一, 最強, 何でも, or 全部 as claims/opinions that need human judgment and, when factual, evidence; they are not default style tokens.",
        ]
    )

    packet["human_gate"]["checks"].extend(
        [
            "If this article says 最新・現在・現時点, what dated evidence or as-of boundary makes that true now?",
            "Did I accidentally reuse an old product comparison, UI path, plan, price, model, or recommendation after the product changed?",
            "Before a beginner path becomes one-way, did I expose the material choice/risk that actually needed a decision?",
            "For each important procedure, can the reader tell what success looks like and what to do if it does not happen?",
            "Did any instruction ask the reader to bypass permissions, weaken security, or give a secret/credential to an AI model for convenience?",
            "If I wrote 自己責任 or a warning, did I also give concrete mitigation, a stop condition, and a recovery path?",
            "Is any safety-critical information being withheld until after signup/payment/CTA? If yes, move it into the article.",
            "How many different commercial actions does the draft ask for? Can they be reduced to the single intended next step?",
            "Does the CTA appear at a real next wall created by the article, or was a wall manufactured to justify the CTA?",
            "Did the writer's pain shape the article promise without becoming an unsupported guarantee?",
            "Does automation stop where a human must authorize, verify, judge, or recover?",
        ]
    )
    return packet


def audit_draft(draft: str, packet: dict) -> dict:
    """Run v0.8 audits plus v0.9 METEOR attack heuristics."""
    result = _v08.audit_draft(draft, packet)
    findings = [*result.get("findings", []), *_semantic_attack_findings(draft, packet)]

    # De-duplicate identical findings from stacked gates.
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

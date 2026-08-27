from __future__ import annotations

import hashlib
import html
import json
import re
import socket
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Any, Callable, Iterable

from model_transition_intelligence.core import SCHEMA_VERSION as H_SCHEMA_VERSION
from model_transition_intelligence.core import validate_bundle


class IntakeError(ValueError):
    pass


REPORT_SCHEMA_VERSION = "official-docs-intake-report/v1"
MAX_DOCUMENTS = 8
MAX_DISCOVERY_LINKS = 256
MAX_RAW_BYTES = 2_000_000
MAX_NORMALIZED_CHARS = 240_000
MAX_BLOCKS = 4096
MAX_AMBIGUOUS_FINDINGS = 64
DEFAULT_TIMEOUT_SECONDS = 12.0

AUTHORITY_NONE = {
    "execution_authority": "NONE",
    "profile_application_authority": "NONE",
    "promotion_authority": "NONE",
}

PROVIDER_POLICIES: dict[str, dict[str, Any]] = {
    "openai": {
        "display_name": "OpenAI",
        "official_hosts": (
            "developers.openai.com",
            "platform.openai.com",
            "openai.com",
        ),
        "index_urls": (
            "https://developers.openai.com/api/llms.txt",
            "https://developers.openai.com/llms.txt",
        ),
        "seed_urls": (
            "https://developers.openai.com/api/docs/models",
            "https://developers.openai.com/api/docs/guides/latest-model.md",
        ),
    },
    "anthropic": {
        "display_name": "Anthropic",
        "official_hosts": (
            "platform.claude.com",
            "docs.anthropic.com",
            "anthropic.com",
        ),
        "index_urls": (
            "https://platform.claude.com/llms.txt",
        ),
        "seed_urls": (
            "https://platform.claude.com/docs/en/about-claude/models/overview.md",
            "https://platform.claude.com/docs/en/about-claude/models/migration-guide.md",
        ),
    },
    "google": {
        "display_name": "Google",
        "official_hosts": (
            "ai.google.dev",
            "cloud.google.com",
        ),
        "index_urls": (
            "https://ai.google.dev/gemini-api/docs/models",
        ),
        "seed_urls": (
            "https://ai.google.dev/gemini-api/docs/models",
        ),
    },
}


CONTRACT_SIGNAL_RE = re.compile(
    r"\b(?:must|required|requires|unsupported|supports?|available|deprecated|deprecation|"
    r"limit|maximum|max(?:imum)?|minimum|error|retry|rate\s+limit|tool|cache|context|"
    r"reasoning|thinking|agent|state|stream|schema|permission|pricing|price|cost|token|"
    r"request|response|runtime|execution|delegate|orchestrat|supervis|worker|sandbox|"
    r"model\s+id|alias|snapshot|endpoint|new|now|changed)\b",
    re.IGNORECASE,
)

MARKETING_RE = re.compile(
    r"\b(?:state[- ]of[- ]the[- ]art|frontier[- ]class|most capable|most intelligent|"
    r"best in the world|flagship capability|powerful|cutting[- ]edge)\b",
    re.IGNORECASE,
)

NUMERIC_CONTRACT_RE = re.compile(
    r"(?:\b\d[\d,.]*\s*(?:k|m|b)?\s*(?:tokens?|requests?|seconds?|minutes?|hours?)\b|\$\s*\d)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ClaimRule:
    area: str
    key: str
    kind: str
    patterns: tuple[str, ...]
    multiple: bool = False


CLAIM_RULES: tuple[ClaimRule, ...] = (
    ClaimRule("other", "deprecation", "DEPRECATION", (r"\bdeprecated\b", r"\bdeprecation\b", r"\bshut down\b", r"\bsunset\b"), True),
    ClaimRule("context", "context_window", "LIMIT", (r"\bcontext window\b", r"\bcontext length\b")),
    ClaimRule("limits", "max_output_tokens", "LIMIT", (r"\bmax(?:imum)? output(?: tokens?)?\b", r"\boutput token limit\b")),
    ClaimRule("reasoning", "reasoning_effort", "CONTRACT", (r"\breasoning[ ._-]*effort\b", r"\beffort levels?\b")),
    ClaimRule("reasoning", "adaptive_thinking", "CONTRACT", (r"\badaptive thinking\b",)),
    ClaimRule("reasoning", "extended_thinking", "CONTRACT", (r"\bextended thinking\b",)),
    ClaimRule("reasoning", "thinking_mode", "CONTRACT", (r"\bthinking\b",), True),
    ClaimRule("delegation", "multi_agent", "CAPABILITY", (r"\bmulti[- ]agent\b", r"\bsubagents?\b")),
    ClaimRule("delegation", "delegation_model", "CONTRACT", (r"\bdelegat(?:e|es|ed|ion|ing)\b", r"\borchestrat(?:e|es|ed|ion|ing)\b", r"\bsupervis(?:or|ory|e|es|ed|ing)\b"), True),
    ClaimRule("memory_cache", "prompt_caching", "CONTRACT", (r"\bprompt cach(?:e|ing)\b",)),
    ClaimRule("memory_cache", "context_caching", "CONTRACT", (r"\bcontext cach(?:e|ing)\b",)),
    ClaimRule("memory_cache", "cache_contract", "CONTRACT", (r"\bcach(?:e|ed|ing)\b",), True),
    ClaimRule("tools", "programmatic_tool_calling", "CAPABILITY", (r"\bprogrammatic tool calling\b",)),
    ClaimRule("tools", "function_calling", "CAPABILITY", (r"\bfunction calling\b",)),
    ClaimRule("tools", "web_search", "CAPABILITY", (r"\bweb search\b",)),
    ClaimRule("tools", "file_search", "CAPABILITY", (r"\bfile search\b",)),
    ClaimRule("tools", "computer_use", "CAPABILITY", (r"\bcomputer use\b",)),
    ClaimRule("tools", "code_execution", "CAPABILITY", (r"\bcode interpreter\b", r"\bcode execution\b")),
    ClaimRule("tools", "mcp", "CAPABILITY", (r"\bmodel context protocol\b", r"\bmcp\b")),
    ClaimRule("tools", "tool_use", "CAPABILITY", (r"\btool use\b", r"\btool calling\b", r"\btools? supported\b"), True),
    ClaimRule("sandbox", "sandbox_model", "CONTRACT", (r"\bsandbox\b", r"\bhosted runtime\b", r"\bisolated linux\b"), True),
    ClaimRule("response_schema", "structured_output", "CONTRACT", (r"\bstructured outputs?\b", r"\bjson schema\b", r"\bresponse schema\b"), True),
    ClaimRule("streaming", "streaming", "CONTRACT", (r"\bstreaming\b", r"\bstream(?:ed|s)? responses?\b"), True),
    ClaimRule("state", "state_model", "CONTRACT", (r"\bconversation state\b", r"\bsession state\b", r"\bstateful\b"), True),
    ClaimRule("instructions", "system_prompt", "CONTRACT", (r"\bsystem prompt\b",), True),
    ClaimRule("instructions", "instruction_guidance", "CONTRACT", (r"\binstructions?\b", r"\bprompt engineering\b", r"\bprompting best practices\b"), True),
    ClaimRule("errors_retries", "rate_limits", "LIMIT", (r"\brate limits?\b", r"\b429\b"), True),
    ClaimRule("errors_retries", "errors_retries", "CONTRACT", (r"\berrors?\b", r"\bretr(?:y|ies|ied)\b", r"\b5\d\d\b"), True),
    ClaimRule("auth_permissions", "authentication", "CONTRACT", (r"\bauthentication\b", r"\bapi key\b"), True),
    ClaimRule("auth_permissions", "permissions", "CONTRACT", (r"\bpermissions?\b", r"\brbac\b"), True),
    ClaimRule("pricing_usage", "pricing", "PRICING", (r"\bpricing\b", r"\binput price\b", r"\boutput price\b", r"\bcached input\b", r"\$\s*\d"), True),
    ClaimRule("pricing_usage", "performance", "PERFORMANCE", (r"\blatency\b", r"\bthroughput\b", r"\btoken[- ]efficient\b", r"\bperformance\b", r"\bfaster\b"), True),
    ClaimRule("model_identity", "model_id", "CONTRACT", (r"\bmodel id\b", r"\bmodel ids\b"), True),
    ClaimRule("model_identity", "alias", "CONTRACT", (r"\balias\b", r"\bsnapshot\b"), True),
    ClaimRule("model_identity", "endpoint", "CONTRACT", (r"\bendpoint\b",), True),
    ClaimRule("limits", "general_limit", "LIMIT", (r"\blimits?\b", r"\bmaximum\b", r"\bminimum\b", r"\bmax\b.{0,80}\btokens?\b"), True),
)


ROLE_HINTS = (
    "model",
    "migration",
    "upgrade",
    "release",
    "what's new",
    "whats-new",
    "pricing",
    "context",
    "reasoning",
    "thinking",
    "tool",
    "function",
    "cache",
    "deprecation",
    "limit",
    "stream",
    "agent",
    "sandbox",
)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _normalize_space(text: str) -> str:
    return " ".join(text.split())


def provider_policy(provider: str) -> dict[str, Any]:
    key = provider.strip().lower()
    if key not in PROVIDER_POLICIES:
        raise IntakeError(f"unsupported provider: {provider!r}")
    return PROVIDER_POLICIES[key]


def _hostname(url: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    return (parsed.hostname or "").lower().rstrip(".")


def validate_official_url(provider: str, url: str) -> str:
    if not isinstance(url, str) or not url:
        raise IntakeError("url must be a non-empty string")
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme.lower() != "https":
        raise IntakeError("official docs fetch requires HTTPS")
    if parsed.username or parsed.password:
        raise IntakeError("userinfo in documentation URL is forbidden")
    host = _hostname(url)
    if not host:
        raise IntakeError("documentation URL is missing host")
    policy = provider_policy(provider)
    if host not in policy["official_hosts"]:
        raise IntakeError(f"host is not allowlisted for {provider}: {host}")
    try:
        socket.inet_pton(socket.AF_INET, host)
        raise IntakeError("literal IP documentation hosts are forbidden")
    except OSError:
        pass
    try:
        socket.inet_pton(socket.AF_INET6, host)
        raise IntakeError("literal IP documentation hosts are forbidden")
    except OSError:
        pass
    clean = urllib.parse.urlunsplit(("https", parsed.netloc, parsed.path or "/", parsed.query, ""))
    return clean


class _AllowlistedRedirectHandler(urllib.request.HTTPRedirectHandler):
    def __init__(self, provider: str):
        super().__init__()
        self.provider = provider

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[override]
        validate_official_url(self.provider, newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class _VisibleTextParser(HTMLParser):
    IGNORE_TAGS = {"script", "style", "noscript", "svg", "canvas", "nav", "header", "footer", "aside"}
    BLOCK_TAGS = {"p", "li", "h1", "h2", "h3", "h4", "h5", "h6", "pre", "blockquote", "td", "th", "dt", "dd"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self._ignore_depth = 0
        self._buffer: list[str] = []
        self.blocks: list[str] = []

    def _flush(self) -> None:
        text = _normalize_space(" ".join(self._buffer))
        self._buffer = []
        if text:
            self.blocks.append(text)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in self.IGNORE_TAGS:
            self._ignore_depth += 1
            return
        if self._ignore_depth == 0 and tag in self.BLOCK_TAGS:
            self._flush()

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in self.IGNORE_TAGS:
            if self._ignore_depth:
                self._ignore_depth -= 1
            return
        if self._ignore_depth == 0 and tag in self.BLOCK_TAGS:
            self._flush()

    def handle_data(self, data: str) -> None:
        if self._ignore_depth == 0:
            text = _normalize_space(data)
            if text:
                self._buffer.append(text)

    def close(self) -> None:
        super().close()
        self._flush()


class _LinkParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[str, str]] = []
        self._href: str | None = None
        self._label: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        values = dict(attrs)
        self._href = values.get("href")
        self._label = []

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            text = _normalize_space(data)
            if text:
                self._label.append(text)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self._href is not None:
            self.links.append((_normalize_space(" ".join(self._label)), self._href))
            self._href = None
            self._label = []


def normalize_visible_text(body: str, content_type: str) -> str:
    if not isinstance(body, str) or not body:
        raise IntakeError("document body must be non-empty text")
    media_type = content_type.split(";", 1)[0].strip().lower()
    blocks: list[str]
    if media_type in {"text/html", "application/xhtml+xml"} or "<html" in body[:500].lower():
        parser = _VisibleTextParser()
        parser.feed(body)
        parser.close()
        blocks = parser.blocks
    else:
        blocks = []
        for line in body.splitlines():
            value = _normalize_space(html.unescape(line))
            if value:
                blocks.append(value)
    deduped: list[str] = []
    for block in blocks:
        if deduped and deduped[-1] == block:
            continue
        deduped.append(block)
        if len(deduped) > MAX_BLOCKS:
            raise IntakeError(f"normalized document exceeds {MAX_BLOCKS} blocks")
    content = "\n".join(deduped).strip()
    if not content:
        raise IntakeError("document has no visible normalized text")
    if len(content) > MAX_NORMALIZED_CHARS:
        raise IntakeError(f"normalized document exceeds {MAX_NORMALIZED_CHARS} characters")
    return content


def _decode_body(raw: bytes, content_type: str) -> str:
    charset = "utf-8"
    match = re.search(r"charset=([A-Za-z0-9._-]+)", content_type, re.IGNORECASE)
    if match:
        charset = match.group(1)
    try:
        return raw.decode(charset)
    except (LookupError, UnicodeDecodeError):
        return raw.decode("utf-8", errors="replace")


def http_fetch(provider: str, url: str, *, max_bytes: int = MAX_RAW_BYTES, timeout: float = DEFAULT_TIMEOUT_SECONDS) -> dict[str, Any]:
    initial_url = validate_official_url(provider, url)
    if not isinstance(max_bytes, int) or not 1 <= max_bytes <= MAX_RAW_BYTES:
        raise IntakeError(f"max_bytes must be between 1 and {MAX_RAW_BYTES}")
    if not isinstance(timeout, (int, float)) or timeout <= 0 or timeout > 30:
        raise IntakeError("timeout must be >0 and <=30 seconds")
    opener = urllib.request.build_opener(_AllowlistedRedirectHandler(provider))
    request = urllib.request.Request(
        initial_url,
        headers={"User-Agent": "RTS-OfficialDocsIntake/1.0", "Accept": "text/plain,text/markdown,text/html,application/json;q=0.8,*/*;q=0.1"},
        method="GET",
    )
    try:
        with opener.open(request, timeout=float(timeout)) as response:
            final_url = validate_official_url(provider, response.geturl())
            raw = response.read(max_bytes + 1)
            if len(raw) > max_bytes:
                raise IntakeError(f"document exceeds max_bytes={max_bytes}")
            content_type = response.headers.get("Content-Type", "text/plain")
            body = _decode_body(raw, content_type)
            return {
                "requested_url": initial_url,
                "final_url": final_url,
                "content_type": content_type,
                "body": body,
                "raw_sha256": hashlib.sha256(raw).hexdigest(),
                "etag": response.headers.get("ETag"),
                "last_modified": response.headers.get("Last-Modified"),
                "status": getattr(response, "status", 200),
            }
    except IntakeError:
        raise
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
        raise IntakeError(f"fetch failed for {initial_url}: {exc}") from exc


def _extract_links(body: str, content_type: str, base_url: str) -> list[tuple[str, str]]:
    media_type = content_type.split(";", 1)[0].strip().lower()
    links: list[tuple[str, str]] = []
    if media_type in {"text/html", "application/xhtml+xml"} or "<html" in body[:500].lower():
        parser = _LinkParser()
        parser.feed(body)
        parser.close()
        links.extend(parser.links)
    else:
        pattern = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)")
        links.extend((label, url) for label, url in pattern.findall(body))
    resolved: list[tuple[str, str]] = []
    for label, href in links[:MAX_DISCOVERY_LINKS]:
        url = urllib.parse.urljoin(base_url, href)
        resolved.append((_normalize_space(label), url))
    return resolved


def _score_candidate(label: str, url: str, query_terms: Iterable[str]) -> int:
    haystack = f"{label} {url}".lower()
    score = 0
    for term in query_terms:
        value = _normalize_space(str(term)).lower()
        if not value:
            continue
        if value in haystack:
            score += 12
        else:
            for token in re.findall(r"[a-z0-9][a-z0-9._-]+", value):
                if len(token) >= 3 and token in haystack:
                    score += 2
    for hint in ROLE_HINTS:
        if hint in haystack:
            score += 1
    if url.endswith(".md") or url.endswith(".txt"):
        score += 2
    return score


def discover_document_urls(
    provider: str,
    query_terms: Iterable[str],
    *,
    explicit_urls: Iterable[str] = (),
    max_documents: int = MAX_DOCUMENTS,
    fetcher: Callable[[str, str], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    policy = provider_policy(provider)
    if not isinstance(max_documents, int) or not 1 <= max_documents <= MAX_DOCUMENTS:
        raise IntakeError(f"max_documents must be between 1 and {MAX_DOCUMENTS}")
    fetch = fetcher or (lambda p, u: http_fetch(p, u))
    candidates: dict[str, dict[str, Any]] = {}
    failures: list[dict[str, str]] = []

    def add(url: str, score: int, origin: str, label: str = "") -> None:
        clean = validate_official_url(provider, url)
        current = candidates.get(clean)
        row = {"url": clean, "score": score, "origin": origin, "label": label}
        if current is None or score > current["score"]:
            candidates[clean] = row

    terms = tuple(_normalize_space(str(term)) for term in query_terms if _normalize_space(str(term)))
    for url in explicit_urls:
        add(url, 10_000, "EXPLICIT")
    for url in policy["seed_urls"]:
        add(url, 5 + _score_candidate("", url, terms), "SEED")
    for index_url in policy["index_urls"]:
        try:
            fetched = fetch(provider, index_url)
            final_url = validate_official_url(provider, fetched["final_url"])
            for label, link in _extract_links(fetched["body"], fetched.get("content_type", "text/plain"), final_url):
                try:
                    validate_official_url(provider, link)
                except IntakeError:
                    continue
                score = _score_candidate(label, link, terms)
                if score > 0:
                    add(link, score, "INDEX", label)
        except Exception as exc:
            failures.append({"url": index_url, "reason": str(exc)})

    ranked = sorted(candidates.values(), key=lambda row: (-row["score"], row["url"]))[:max_documents]
    return {
        "provider": provider.strip().lower(),
        "query_terms": list(terms),
        "max_documents": max_documents,
        "urls": [row["url"] for row in ranked],
        "candidates": ranked,
        "index_failures": failures,
    }


def _chunk_blocks(content: str) -> list[str]:
    chunks: list[str] = []
    for raw_block in content.splitlines():
        block = _normalize_space(raw_block)
        if not block:
            continue
        sentence_parts = [
            _normalize_space(part)
            for part in re.split(r"(?<=[.!?;])\s+(?=[A-Z0-9])", block)
            if _normalize_space(part)
        ]
        for sentence in sentence_parts:
            if len(sentence) <= 1800:
                chunks.append(sentence)
                continue
            remaining = sentence
            while len(remaining) > 1800:
                cut = max(remaining.rfind(". ", 0, 1800), remaining.rfind("; ", 0, 1800), remaining.rfind(" ", 0, 1800))
                if cut < 200:
                    cut = 1800
                piece = remaining[:cut].strip()
                if piece:
                    chunks.append(piece)
                remaining = remaining[cut:].strip()
            if remaining:
                chunks.append(remaining)
    return chunks


def _claim_key(rule: ClaimRule, anchor: str) -> str:
    if not rule.multiple:
        return rule.key
    suffix = _sha256_text(anchor.lower())[:10]
    return f"{rule.key}:{suffix}"


def extract_claims(content: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if not isinstance(content, str) or not content:
        raise IntakeError("content must be non-empty")
    claims: list[dict[str, Any]] = []
    ambiguous: list[dict[str, Any]] = []
    ignored_count = 0
    covered_count = 0
    seen: set[tuple[str, str, str]] = set()

    for anchor in _chunk_blocks(content):
        matched: list[tuple[ClaimRule, str]] = []
        for rule in CLAIM_RULES:
            for pattern in rule.patterns:
                if re.search(pattern, anchor, re.IGNORECASE):
                    matched.append((rule, pattern))
                    break
        if not matched and MARKETING_RE.search(anchor) and not NUMERIC_CONTRACT_RE.search(anchor):
            marketing_rule = ClaimRule("other", "marketing", "MARKETING", ("marketing",), True)
            matched.append((marketing_rule, "MARKETING_RE"))

        if matched:
            covered_count += 1
            for rule, pattern in matched:
                key = _claim_key(rule, anchor)
                fingerprint = (rule.area, key, anchor)
                if fingerprint in seen:
                    continue
                seen.add(fingerprint)
                claim_id = "c_" + _sha256_text(f"{rule.area}|{key}|{anchor}")[:20]
                claims.append({
                    "claim_id": claim_id,
                    "area": rule.area,
                    "key": key,
                    "kind": rule.kind,
                    "value": {"statement": anchor},
                    "anchor": anchor,
                    "extraction_method": "DETERMINISTIC_LEXICAL_V1",
                    "matched_pattern": pattern,
                    "behavior_status": "UNVERIFIED",
                })
            continue

        if CONTRACT_SIGNAL_RE.search(anchor):
            if len(ambiguous) < MAX_AMBIGUOUS_FINDINGS:
                ambiguous.append({
                    "anchor_sha256": _sha256_text(anchor),
                    "preview": anchor[:240],
                    "reason": "CONTRACT_SIGNAL_WITHOUT_EXTRACTION_RULE",
                })
        else:
            ignored_count += 1

    audit = {
        "coverage_state": "REVIEW_REQUIRED" if ambiguous else "COVERED",
        "claim_count": len(claims),
        "covered_block_count": covered_count,
        "ambiguous_block_count": len(ambiguous),
        "ambiguous": ambiguous,
        "ignored_block_count": ignored_count,
        "ambiguous_findings_truncated": len(ambiguous) >= MAX_AMBIGUOUS_FINDINGS,
    }
    return claims, audit


def infer_source_type(url: str) -> str:
    path = urllib.parse.urlsplit(url).path.lower()
    if "migration" in path or "upgrade" in path:
        return "MIGRATION_GUIDE"
    if "release" in path or "whats-new" in path or "what-is-new" in path:
        return "RELEASE_NOTES"
    if "deprecat" in path:
        return "DEPRECATION_NOTE"
    if "tool" in path or "function" in path or "mcp" in path:
        return "TOOL_DOCS"
    if "limit" in path or "context-window" in path or "rate-limit" in path:
        return "LIMITS_DOCS"
    if "api/reference" in path or "/api/" in path and path.endswith(".md"):
        return "API_DOCS"
    if "model" in path:
        return "MODEL_CARD"
    return "OTHER_OFFICIAL"


def stable_document_id(provider: str, url: str) -> str:
    parsed = urllib.parse.urlsplit(validate_official_url(provider, url))
    path = re.sub(r"[^a-z0-9]+", "-", parsed.path.lower()).strip("-") or "root"
    if len(path) > 100:
        path = path[:80] + "-" + _sha256_text(parsed.path)[:12]
    return f"{provider.strip().lower()}:{path}"


def build_source(
    provider: str,
    generation: str,
    fetched: dict[str, Any],
    *,
    document_id: str | None = None,
    source_type: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    final_url = validate_official_url(provider, fetched["final_url"])
    content_type = fetched.get("content_type", "text/plain")
    content = normalize_visible_text(fetched["body"], content_type)
    claims, extraction_audit = extract_claims(content)
    content_sha256 = _sha256_text(content)
    raw_sha256 = fetched.get("raw_sha256") or _sha256_text(fetched["body"])
    doc_id = document_id or stable_document_id(provider, final_url)
    src_type = source_type or infer_source_type(final_url)
    source_id = f"{provider.strip().lower()}:{generation}:{_sha256_text(doc_id + '|' + content_sha256)[:20]}"
    source = {
        "source_id": source_id,
        "document_id": doc_id,
        "source_type": src_type,
        "trust": "OFFICIAL",
        "url": final_url,
        "ref": f"{final_url}#sha256={content_sha256}",
        "content": content,
        "content_sha256": content_sha256,
        "claims": claims,
        "raw_content_sha256": raw_sha256,
        "requested_url": fetched.get("requested_url", final_url),
        "retrieved_content_type": content_type,
        "etag": fetched.get("etag"),
        "last_modified": fetched.get("last_modified"),
        "extraction_coverage_state": extraction_audit["coverage_state"],
        "behavior_status": "UNVERIFIED",
        **AUTHORITY_NONE,
    }
    audit = {
        "document_id": doc_id,
        "source_id": source_id,
        "url": final_url,
        "source_type": src_type,
        "content_sha256": content_sha256,
        "raw_content_sha256": raw_sha256,
        "extraction": extraction_audit,
    }
    return source, audit


def _validate_request(request: dict[str, Any]) -> None:
    if not isinstance(request, dict):
        raise IntakeError("request must be an object")
    required = {"provider", "product_surface", "generation", "captured_at"}
    missing = sorted(required - set(request))
    if missing:
        raise IntakeError(f"request missing fields: {missing}")
    for field in required:
        if not isinstance(request[field], str) or not request[field]:
            raise IntakeError(f"request.{field} must be a non-empty string")
    provider_policy(request["provider"])
    if "query_terms" in request and not isinstance(request["query_terms"], list):
        raise IntakeError("request.query_terms must be a list")
    if "explicit_urls" in request and not isinstance(request["explicit_urls"], list):
        raise IntakeError("request.explicit_urls must be a list")
    if "document_overrides" in request and not isinstance(request["document_overrides"], dict):
        raise IntakeError("request.document_overrides must be an object")


def build_intake_report(
    request: dict[str, Any],
    *,
    fetcher: Callable[[str, str], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    _validate_request(request)
    provider = request["provider"].strip().lower()
    fetch = fetcher or (lambda p, u: http_fetch(p, u))
    max_documents = int(request.get("max_documents", MAX_DOCUMENTS))
    discovery = discover_document_urls(
        provider,
        request.get("query_terms", [request["generation"], request["product_surface"]]),
        explicit_urls=request.get("explicit_urls", []),
        max_documents=max_documents,
        fetcher=fetch,
    )
    overrides = request.get("document_overrides", {})
    sources: list[dict[str, Any]] = []
    document_audits: list[dict[str, Any]] = []
    fetch_failures: list[dict[str, str]] = []

    for url in discovery["urls"]:
        try:
            fetched = fetch(provider, url)
            final_url = validate_official_url(provider, fetched["final_url"])
            override = overrides.get(url, overrides.get(final_url, {}))
            source, audit = build_source(
                provider,
                request["generation"],
                fetched,
                document_id=override.get("document_id"),
                source_type=override.get("source_type"),
            )
            if any(existing["document_id"] == source["document_id"] for existing in sources):
                source["document_id"] = source["document_id"] + ":" + _sha256_text(final_url)[:8]
                audit["document_id"] = source["document_id"]
            sources.append(source)
            document_audits.append(audit)
        except Exception as exc:
            fetch_failures.append({"url": url, "reason": str(exc)})

    bundle: dict[str, Any] | None = None
    bundle_error: str | None = None
    if sources:
        candidate = {
            "schema_version": H_SCHEMA_VERSION,
            "provider": provider,
            "product_surface": request["product_surface"],
            "generation": request["generation"],
            "captured_at": request["captured_at"],
            "sources": sources,
            "intake_provenance": {
                "adapter_schema": REPORT_SCHEMA_VERSION,
                "provider_policy": provider,
                "docs_claim_status": "UNVERIFIED",
            },
            **AUTHORITY_NONE,
        }
        try:
            validate_bundle(candidate)
            bundle = candidate
        except Exception as exc:
            bundle_error = str(exc)

    ambiguous_count = sum(row["extraction"]["ambiguous_block_count"] for row in document_audits)
    index_failure_count = len(discovery["index_failures"])
    if bundle is None:
        status = "FAILED"
    elif fetch_failures or bundle_error:
        status = "REVIEW_REQUIRED"
    elif ambiguous_count:
        status = "REVIEW_REQUIRED"
    else:
        status = "READY_FOR_H"

    report = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "status": status,
        "provider": provider,
        "product_surface": request["product_surface"],
        "generation": request["generation"],
        "captured_at": request["captured_at"],
        "bundle": bundle,
        "audit": {
            "discovery": discovery,
            "documents": document_audits,
            "fetch_failures": fetch_failures,
            "bundle_validation_error": bundle_error,
            "ambiguous_block_count": ambiguous_count,
            "index_failure_count": index_failure_count,
            "ready_condition": "bundle valid AND no document fetch failure AND no ambiguous contract-like block",
        },
        "docs_claim_status": "UNVERIFIED",
        "hidden_architecture_claim": "NONE",
        **AUTHORITY_NONE,
    }
    return report


def verify_intake_report(report: dict[str, Any]) -> None:
    if not isinstance(report, dict):
        raise IntakeError("report must be an object")
    if report.get("schema_version") != REPORT_SCHEMA_VERSION:
        raise IntakeError(f"report schema must be {REPORT_SCHEMA_VERSION}")
    if report.get("status") not in {"READY_FOR_H", "REVIEW_REQUIRED", "FAILED"}:
        raise IntakeError("invalid report status")
    for key, value in AUTHORITY_NONE.items():
        if report.get(key) != value:
            raise IntakeError(f"report authority boundary violated: {key}")
    if report.get("docs_claim_status") != "UNVERIFIED":
        raise IntakeError("docs claims must remain UNVERIFIED")
    if report.get("hidden_architecture_claim") != "NONE":
        raise IntakeError("hidden architecture claim is forbidden")
    bundle = report.get("bundle")
    if bundle is not None:
        validate_bundle(bundle)
    audit = report.get("audit")
    if not isinstance(audit, dict):
        raise IntakeError("report audit missing")
    if report["status"] == "READY_FOR_H":
        if bundle is None:
            raise IntakeError("READY_FOR_H requires a valid bundle")
        if audit.get("fetch_failures"):
            raise IntakeError("READY_FOR_H cannot contain fetch failures")
        if audit.get("ambiguous_block_count"):
            raise IntakeError("READY_FOR_H cannot contain ambiguous contract-like blocks")
        if audit.get("bundle_validation_error"):
            raise IntakeError("READY_FOR_H cannot contain bundle validation errors")


def report_fingerprint(report: dict[str, Any]) -> str:
    verify_intake_report(report)
    return _sha256_text(_canonical(report))

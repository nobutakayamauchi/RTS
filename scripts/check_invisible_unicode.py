#!/usr/bin/env python3
from __future__ import annotations

import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path

SCANNER_VERSION = "unicode-intake-guard-v2"

FORBIDDEN_CODEPOINTS = {
    # Invisible / zero-width
    0x200B,  # ZERO WIDTH SPACE
    0x200C,  # ZERO WIDTH NON-JOINER
    0x200D,  # ZERO WIDTH JOINER
    0x2060,  # WORD JOINER
    0xFEFF,  # ZERO WIDTH NO-BREAK SPACE / BOM

    # Bidi controls (Trojan Source / review confusion)
    0x202A,  # LEFT-TO-RIGHT EMBEDDING
    0x202B,  # RIGHT-TO-LEFT EMBEDDING
    0x202C,  # POP DIRECTIONAL FORMATTING
    0x202D,  # LEFT-TO-RIGHT OVERRIDE
    0x202E,  # RIGHT-TO-LEFT OVERRIDE
    0x2066,  # LEFT-TO-RIGHT ISOLATE
    0x2067,  # RIGHT-TO-LEFT ISOLATE
    0x2068,  # FIRST STRONG ISOLATE
    0x2069,  # POP DIRECTIONAL ISOLATE
}

TARGET_EXTENSIONS = {
    ".py", ".js", ".ts", ".tsx", ".jsx",
    ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".env", ".lock",
    ".md", ".txt",
    ".sh", ".bash", ".zsh", ".html", ".css", ".xml",
}

PROSE_EXTENSIONS = {".md", ".txt"}

EXCLUDED_DIRS = {
    ".git", "node_modules", "dist", "build",
    ".venv", "venv", "__pycache__", ".mypy_cache"
}

BASIC_VS_START = 0xFE00
BASIC_VS_END = 0xFE0F
SUPPLEMENT_VS_START = 0xE0100
SUPPLEMENT_VS_END = 0xE01EF

# U+FE0F is commonly used for emoji presentation in prose. A high file-level
# count is still suspicious enough to fail closed. All other VS characters in
# prose are blocking because ordinary prose rarely needs them.
PROSE_FE0F_REVIEW_THRESHOLD = 16


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    column: int
    codepoint: int
    severity: str
    reason: str

    def render(self) -> str:
        name = unicodedata.name(chr(self.codepoint), "UNKNOWN")
        return (
            f"{self.path}:{self.line}:{self.column}: {self.severity} "
            f"U+{self.codepoint:04X} {name}: {self.reason}"
        )


def is_variation_selector(cp: int) -> bool:
    return (
        BASIC_VS_START <= cp <= BASIC_VS_END
        or SUPPLEMENT_VS_START <= cp <= SUPPLEMENT_VS_END
    )


def should_check(path: Path) -> bool:
    if not path.is_file() or path.is_symlink():
        return False
    if any(part in EXCLUDED_DIRS for part in path.parts):
        return False
    return path.suffix.lower() in TARGET_EXTENSIONS


def iter_files(args: list[str]) -> list[Path]:
    if args:
        files = []
        for arg in args:
            p = Path(arg)
            if should_check(p):
                files.append(p)
        return files

    return [p for p in Path(".").rglob("*") if should_check(p)]


def scan_text(path: Path, text: str) -> list[Finding]:
    findings: list[Finding] = []
    prose = path.suffix.lower() in PROSE_EXTENSIONS
    prose_fe0f_positions: list[tuple[int, int]] = []

    for line_no, line in enumerate(text.splitlines(), start=1):
        for col_no, ch in enumerate(line, start=1):
            cp = ord(ch)

            if cp in FORBIDDEN_CODEPOINTS:
                findings.append(
                    Finding(
                        str(path), line_no, col_no, cp, "BLOCK",
                        "forbidden invisible or bidi control"
                    )
                )
                continue

            if SUPPLEMENT_VS_START <= cp <= SUPPLEMENT_VS_END:
                findings.append(
                    Finding(
                        str(path), line_no, col_no, cp, "BLOCK",
                        "supplementary variation selector is not admitted"
                    )
                )
                continue

            if BASIC_VS_START <= cp <= BASIC_VS_END:
                if not prose:
                    findings.append(
                        Finding(
                            str(path), line_no, col_no, cp, "BLOCK",
                            "variation selector in executable/config surface"
                        )
                    )
                elif cp != 0xFE0F:
                    findings.append(
                        Finding(
                            str(path), line_no, col_no, cp, "BLOCK",
                            "non-emoji variation selector in prose"
                        )
                    )
                else:
                    prose_fe0f_positions.append((line_no, col_no))

    if prose and len(prose_fe0f_positions) >= PROSE_FE0F_REVIEW_THRESHOLD:
        line_no, col_no = prose_fe0f_positions[0]
        findings.append(
            Finding(
                str(path), line_no, col_no, 0xFE0F, "BLOCK",
                f"dense emoji-presentation selectors in prose "
                f"({len(prose_fe0f_positions)} >= {PROSE_FE0F_REVIEW_THRESHOLD})"
            )
        )

    return findings


def scan_file(path: Path) -> list[Finding]:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return []
    except Exception as exc:
        return [
            Finding(str(path), 0, 0, 0, "BLOCK", f"read error: {exc}")
        ]

    return scan_text(path, text)


def main() -> int:
    files = iter_files(sys.argv[1:])
    findings: list[Finding] = []

    for path in files:
        findings.extend(scan_file(path))

    if findings:
        print(f"Unicode intake guard ({SCANNER_VERSION}) detected dangerous content:\n")
        for finding in findings:
            print(finding.render())
        print("\nFAIL: commit / CI rejected.")
        return 1

    print(f"OK: unicode intake guard ({SCANNER_VERSION}) found no blocking content.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

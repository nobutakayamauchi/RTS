#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

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
    ".json", ".yaml", ".yml", ".md",
    ".sh", ".bash", ".zsh", ".html", ".css",
}

EXCLUDED_DIRS = {
    ".git", ".github", "node_modules", "dist", "build",
    ".venv", "venv", "__pycache__", ".mypy_cache"
}


def should_check(path: Path) -> bool:
    if not path.is_file():
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


def scan_file(path: Path) -> list[str]:
    errors: list[str] = []

    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return errors
    except Exception as exc:
        return [f"{path}: read error: {exc}"]

    for line_no, line in enumerate(text.splitlines(), start=1):
        for col_no, ch in enumerate(line, start=1):
            cp = ord(ch)
            if cp in FORBIDDEN_CODEPOINTS:
                errors.append(
                    f"{path}:{line_no}:{col_no}: forbidden unicode U+{cp:04X}"
                )

    return errors


def main() -> int:
    files = iter_files(sys.argv[1:])
    all_errors: list[str] = []

    for path in files:
        all_errors.extend(scan_file(path))

    if all_errors:
        print("Invisible / dangerous Unicode detected:\n")
        for err in all_errors:
            print(err)
        print("\nFAIL: commit / CI rejected.")
        return 1

    print("OK: no forbidden invisible Unicode found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

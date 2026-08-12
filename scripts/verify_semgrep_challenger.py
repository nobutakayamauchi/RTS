#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

RULES = Path(".semgrep/security-intake.yml")


def run_semgrep(path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "semgrep",
            "scan",
            "--config",
            str(RULES),
            "--error",
            "--strict",
            "--metrics=off",
            str(path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )


def assert_clean(path: Path) -> None:
    result = run_semgrep(path)
    if result.returncode != 0:
        raise SystemExit(
            "Semgrep challenger rejected clean fixture:\n"
            + result.stdout
            + result.stderr
        )


def assert_blocked(path: Path) -> None:
    result = run_semgrep(path)
    if result.returncode == 0:
        raise SystemExit(
            "Semgrep challenger failed to reject attack fixture:\n"
            + result.stdout
            + result.stderr
        )


def main() -> int:
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)

        clean = root / "clean.py"
        clean.write_text("print('ok')\n", encoding="utf-8")

        python_eval = root / "python_eval.py"
        python_eval.write_text("eval('1 + 1')\n", encoding="utf-8")

        python_shell = root / "python_shell.py"
        python_shell.write_text("import os\nos.system('echo unsafe')\n", encoding="utf-8")

        js_eval = root / "js_eval.js"
        js_eval.write_text("eval('1 + 1');\n", encoding="utf-8")

        assert_clean(clean)
        assert_blocked(python_eval)
        assert_blocked(python_shell)
        assert_blocked(js_eval)

    print("OK: independent Semgrep challenger accepts clean fixture and rejects attack fixtures.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

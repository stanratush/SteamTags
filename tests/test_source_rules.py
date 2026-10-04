"""Repository-wide rules from the Windows spike: explicit encodings, compiled bytecode."""

from __future__ import annotations

import ast
import subprocess
import sys

from conftest import REPO

SRC = REPO / "src" / "steamstudy"
TEXT_IO_CALLS = {"open", "read_text", "write_text", "TextIOWrapper"}


def _mode(call: ast.Call) -> str:
    for kw in call.keywords:
        if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
            return str(kw.value.value)
    # open(path, mode) / Path.open(mode) / gzip.open(path, mode)
    for arg in call.args:
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str) and set(arg.value) <= set("rwxabt+"):
            return arg.value
    return "r"


def _offenders(paths):
    found = []
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            name = func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else ""
            if name not in TEXT_IO_CALLS:
                continue
            if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name) and func.value.id == "webbrowser":
                continue  # webbrowser.open(url) opens a URL, not a file
            if name in ("open", "TextIOWrapper") and "b" in _mode(node):
                continue
            if not any(kw.arg == "encoding" for kw in node.keywords):
                found.append(f"{path.relative_to(REPO)}:{node.lineno} {name}()")
    return found


def test_every_text_read_and_write_passes_an_encoding():
    assert _offenders(sorted(SRC.rglob("*.py"))) == []


def test_nothing_disables_bytecode():
    hits = [p for p in SRC.rglob("*.py") if "PYTHONDONTWRITEBYTECODE" in p.read_text(encoding="utf-8")]
    assert hits == []
    pyproject = (REPO / "pyproject.toml").read_text(encoding="utf-8")
    assert "compile-bytecode = true" in pyproject


def test_cli_help_runs():
    out = subprocess.run(
        [sys.executable, "-m", "steamstudy.cli", "--help"], capture_output=True, text=True, encoding="utf-8"
    )
    assert out.returncode == 0
    for command in ("collect", "build", "app"):
        assert command in out.stdout

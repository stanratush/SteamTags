"""Lay out a `BuildResult` as `builds/<snapshot_id>/<build_id>/`, never overwriting a Build."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from steamstudy.build.core import BuildResult
from steamstudy.builds import builds_dir, resolve_build  # noqa: F401  (re-exported)
from steamstudy.export.writer import write_csv


class BuildExists(Exception):
    pass


def write_build(result: BuildResult, root: Path) -> Path:
    base = builds_dir(root) / result.snapshot_id
    folder = base / result.build_id
    if folder.exists():
        raise BuildExists(f"Build {folder} already exists; a Build is never overwritten")
    tmp = base / f".{result.build_id}.partial"
    tmp.mkdir(parents=True)
    for rel, (schema, rows) in sorted(result.tables.items()):
        write_csv(tmp / rel, schema, rows)
    for rel, text in sorted(result.texts.items()):
        path = tmp / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    write_json(tmp / "datasets" / "build.json", result.build_json)
    tmp.rename(folder)
    (base / "latest").write_text(result.build_id + "\n", encoding="utf-8")
    builds_dir(root).joinpath("latest").write_text(f"{result.snapshot_id}/{result.build_id}\n", encoding="utf-8")
    return folder


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_failed_parse_errors(root: Path, snapshot_id: str, build_id: str, rows: list[dict[str, Any]]) -> Path:
    """Where the parse errors of a refused Build go, outside any Build folder."""
    from steamstudy.export import schema as S

    path = builds_dir(root) / snapshot_id / "failed" / f"{build_id}-parse_errors.csv"
    write_csv(path, S.PARSE_ERRORS, rows)
    return path

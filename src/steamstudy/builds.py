"""Where Builds live: `<root>/builds/<snapshot_id>/<build_id>/`, with `latest` pointers.

Importable by the app without any pipeline module (the App Bundle installs only the app).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def builds_dir(root: Path) -> Path:
    return Path(root) / "builds"


def resolve_build(root: Path, build: str | None = None, snapshot: str | None = None) -> Path:
    """A Build folder from an id (or `<snapshot>/<build>`), defaulting to the latest."""
    base = builds_dir(root)
    if build and "/" in build:
        snapshot, build = build.split("/", 1)
    if build is None:
        pointer = (base / snapshot / "latest") if snapshot else (base / "latest")
        if not pointer.is_file():
            raise FileNotFoundError(f"no Build found under {base}")
        ref = pointer.read_text(encoding="utf-8").strip()
        return (base / snapshot / ref) if snapshot else (base / ref)
    if snapshot:
        return base / snapshot / build
    matches = [p for p in base.glob(f"*/{build}") if p.is_dir()]
    if len(matches) != 1:
        raise FileNotFoundError(f"Build {build} not found (or ambiguous) under {base}")
    return matches[0]


@dataclass(frozen=True)
class BuildInfo:
    """One Build on disk, as the Build tree and the lifecycle read it. Old `build.json` files have no name,
    description or parent: the name reads as the `build_id`."""

    source_id: str
    build_id: str
    path: Path
    name: str
    description: str | None
    parent_build_id: str | None  # "<source_id>/<build_id>"
    config_hash: str
    mode: str
    software_versions: dict[str, Any]

    @property
    def ref(self) -> str:
        return f"{self.source_id}/{self.build_id}"


def build_info(path: Path) -> BuildInfo:
    path = Path(path)
    bj = json.loads((path / "datasets" / "build.json").read_text(encoding="utf-8"))
    return BuildInfo(
        source_id=path.parent.name, build_id=path.name, path=path, name=bj.get("name") or path.name,
        description=bj.get("description"), parent_build_id=bj.get("parent_build_id"),
        config_hash=str(bj.get("build_config_hash", "")), mode=str(bj.get("mode", "")),
        software_versions=dict(bj.get("software_versions") or {}))


def list_builds(root: Path, source_id: str | None = None) -> list[BuildInfo]:
    """Every Build under `builds/` (or under one source), oldest `build_id` first."""
    base = builds_dir(root)
    sources = [base / source_id] if source_id else sorted(p for p in base.iterdir() if p.is_dir()) \
        if base.is_dir() else []
    found = [build_info(p) for s in sources if s.is_dir() for p in sorted(s.iterdir())
             if (p / "datasets" / "build.json").is_file()]
    return sorted(found, key=lambda b: (b.build_id, b.source_id))


class BuildFailed(Exception):
    """The Build must not be written (parse errors without --allow-parse-errors, invalid config entries, ...)."""

    def __init__(self, message: str, parse_errors: list[dict[str, Any]] | None = None):
        super().__init__(message)
        self.parse_errors = parse_errors or []


# A `bundle.json` entry's `parent_name` when the parent Build was deleted before the Bundle was made.
DELETED_PARENT = "deleted"


def ref_of(folder: str | Path) -> str:
    """A Build folder's ref, `<source_id>/<build_id>`."""
    folder = Path(folder)
    return f"{folder.parent.name}/{folder.name}"


def source_of(ref: str) -> str:
    """The source (Snapshot or Import) id of a ref `<source_id>/<build_id>`."""
    return ref.split("/", 1)[0]


def build_date(build_id: str) -> str:
    """The UTC date a `build_id` was made, as YYYY-MM-DD."""
    stamp = build_id.split("-", 1)[0]
    return f"{stamp[0:4]}-{stamp[4:6]}-{stamp[6:8]}"


LIGHT_SUFFIX = ".light.zip"


def light_path(snapshots_root: Path, snapshot_id: str) -> Path:
    """Where a Snapshot's lightweight form lives (`steamstudy.lightweight` makes and reads it)."""
    return Path(snapshots_root) / f"{snapshot_id}{LIGHT_SUFFIX}"

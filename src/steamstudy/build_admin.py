"""Build identity, Build Drafts and the Build lifecycle, without Dash.

A Build Draft is a Build's complete settings before it exists: the `build.json` `config` block plus a name,
description and parent, saved at `builds/<source_id>/drafts/<name-slug>.json`. Building a draft writes a Build and
uses the draft up; a failed run is not a Build, and its failure stays on the draft. `config/` is only read here.
The app and the Build menu call this module for every lifecycle action.
"""

from __future__ import annotations

import copy
import datetime as dt
import json
import os
import re
import shutil
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from steamstudy.build.core import BuildFailed, BuildIdentity, build, new_build_id
from steamstudy.builds import BuildInfo, build_info, builds_dir, list_builds
from steamstudy.config import (
    BUILD_FILES,
    COLLECTION_FILE,
    build_config,
    canonical_json,
    content_hash,
    exclusions_new_shape,
    load_config,
)
from steamstudy.versions import software_versions

__all__ = [
    "BuildCancelled", "BuildFailed", "DeleteRefused", "DeletionPlan", "Draft", "IdenticalBuild", "NameClash",
    "build_draft", "check_name", "delete_build", "deletion_plan", "discard_draft", "draft_config_hash", "duplicate",
    "identical_builds", "list_drafts", "new_shape", "parent_name", "save_draft", "start_draft",
]


class NameClash(ValueError):
    """Another Build or draft of the same source already has this name (ignoring case)."""


class DeleteRefused(ValueError):
    """The caller's open Build cannot be deleted: switch to another Build first."""


class BuildCancelled(Exception):
    """The run was stopped before the Build was written; the draft is unchanged."""


@dataclass
class Draft:
    source_id: str
    name: str
    description: str
    parent_build_id: str | None
    config: dict[str, dict[str, Any]]  # every Build config file, as in build.json's `config` block
    changelog: list[dict[str, str]]  # entries inherited from the starting point
    last_failure: dict[str, Any] | None = None
    saved_at: str | None = None
    stored_slug: str | None = field(default=None, compare=False)  # the file it was last saved as

    def to_json(self) -> dict[str, Any]:
        return {"source_id": self.source_id, "name": self.name, "description": self.description,
                "parent_build_id": self.parent_build_id, "config": self.config, "changelog": self.changelog,
                "last_failure": self.last_failure, "saved_at": self.saved_at}

    @classmethod
    def from_json(cls, data: dict[str, Any], slug: str) -> Draft:
        return cls(source_id=data["source_id"], name=data["name"], description=data.get("description", ""),
                   parent_build_id=data.get("parent_build_id"), config=data["config"],
                   changelog=list(data.get("changelog", [])), last_failure=data.get("last_failure"),
                   saved_at=data.get("saved_at"), stored_slug=slug)


# ----------------------------------------------------------------------------- names


def slug(name: str) -> str:
    """A draft's file name: the name case-folded, every run of other characters one '-'."""
    return re.sub(r"[\W_]+", "-", name.casefold()).strip("-") or "draft"


def _drafts_dir(root: Path, source_id: str) -> Path:
    return builds_dir(root) / source_id / "drafts"


def check_name(root: Path, source_id: str, name: str, *, ignore_slug: str | None = None) -> None:
    """Refuse an empty name, or one another Build or draft of this source has (ignoring case)."""
    if not name.strip():
        raise NameClash("a Build needs a name")
    folded = name.strip().casefold()
    for info in list_builds(root, source_id) if (builds_dir(root) / source_id).is_dir() else []:
        if info.name.casefold() == folded:
            raise NameClash(f"Build {info.ref} is already named {info.name!r}")
    for draft in list_drafts(root, source_id):
        if draft.stored_slug == ignore_slug:
            continue
        if draft.name.casefold() == folded or draft.stored_slug == slug(name):
            raise NameClash(f"a draft is already named {draft.name!r}")


def _unique_name(root: Path, source_id: str, base: str) -> str:
    candidates = [base] + [f"{base} {i}" for i in range(2, 1000)]
    for name in candidates:
        try:
            check_name(root, source_id, name)
            return name
        except NameClash:
            continue
    raise NameClash(f"no free name like {base!r}")


# ----------------------------------------------------------------------------- drafts


def new_shape(exclusions: dict[str, Any]) -> dict[str, Any]:
    """An `exclusions` file in the named-rule shape (old-shape Builds are converted, never rewritten)."""
    return exclusions_new_shape(exclusions)


def _build_settings(info: BuildInfo) -> tuple[dict[str, dict[str, Any]], list[dict[str, str]]]:
    bj = json.loads((info.path / "datasets" / "build.json").read_text(encoding="utf-8"))
    files = copy.deepcopy(dict(bj["config"]))
    if bj.get("source", "steam") == "steam":
        files["exclusions"] = new_shape(files["exclusions"])
    return files, list(bj.get("changelog", []))


def _info(root: Path, ref: str) -> BuildInfo:
    path = builds_dir(root) / ref
    if "/" not in ref or not (path / "datasets" / "build.json").is_file():
        raise FileNotFoundError(f"Build {ref} not found")
    return build_info(path)


def start_draft(root: Path, source_id: str, from_build: str | None = None, *, config_dir: Path = Path("config"),
                name: str | None = None) -> Draft:
    """A saved draft of complete settings: copied from `config/`, or from a Build (`<source_id>/<build_id>`),
    which becomes its parent."""
    from steamstudy.build.import_build import import_defaults, is_import, open_import

    if from_build is None and is_import(root, source_id):
        files = import_defaults(open_import(root, source_id), config_dir)
        changelog, parent, default = [], None, "Draft"
    elif from_build is None:
        config = load_config(config_dir)
        files = {k: copy.deepcopy(v) for k, v in config.files.items() if k != COLLECTION_FILE}
        changelog, parent, default = config.changelog_entries(), None, "Draft"
    else:
        info = _info(root, from_build)
        files, changelog = _build_settings(info)
        parent, default = info.ref, f"{info.name} (copy)"
    if name is None:
        name = _unique_name(root, source_id, default)
    draft = Draft(source_id=source_id, name=name, description="", parent_build_id=parent, config=files,
                  changelog=changelog)
    return save_draft(root, draft)


def duplicate(root: Path, build_ref: str, target_source_id: str, *, name: str | None = None) -> Draft:
    """A draft from a Build's settings, on its own source or another, with the Build as parent."""
    return start_draft(root, target_source_id, from_build=build_ref, name=name)


def save_draft(root: Path, draft: Draft) -> Draft:
    """Write the draft atomically; a renamed draft moves to its new file. Refuses a name clash."""
    draft.name = draft.name.strip()
    check_name(root, draft.source_id, draft.name, ignore_slug=draft.stored_slug)
    folder = _drafts_dir(root, draft.source_id)
    folder.mkdir(parents=True, exist_ok=True)
    new_slug = slug(draft.name)
    draft.saved_at = dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    target = folder / f"{new_slug}.json"
    tmp = folder / f".{new_slug}.json.partial"
    tmp.write_text(json.dumps(draft.to_json(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, target)
    if draft.stored_slug and draft.stored_slug != new_slug:
        (folder / f"{draft.stored_slug}.json").unlink(missing_ok=True)
    draft.stored_slug = new_slug
    return draft


def list_drafts(root: Path, source_id: str) -> list[Draft]:
    folder = _drafts_dir(root, source_id)
    if not folder.is_dir():
        return []
    return [Draft.from_json(json.loads(p.read_text(encoding="utf-8")), p.stem)
            for p in sorted(folder.glob("*.json"))]


def discard_draft(root: Path, draft: Draft) -> None:
    """Remove the draft and the `failed/` file of its last failure."""
    _remove_failure_file(root, draft)
    if draft.stored_slug:
        (_drafts_dir(root, draft.source_id) / f"{draft.stored_slug}.json").unlink(missing_ok=True)


def _remove_failure_file(root: Path, draft: Draft) -> None:
    failure = draft.last_failure or {}
    if failure.get("path"):
        (Path(root) / failure["path"]).unlink(missing_ok=True)


def draft_config_hash(draft: Draft) -> str:
    """The hash `build.json` will record for the draft's settings (as `Config.build_config_hash` takes it)."""
    files = json.loads(canonical_json(draft.config))
    return content_hash({name: files[name] for name in BUILD_FILES if name in files})


def build_draft(root: Path, draft: Draft, *, on_progress: Callable[[str], None] | None = None,
                should_stop: Callable[[], bool] | None = None, now: dt.datetime | None = None,
                from_raw: bool = False) -> Path:
    """Build the draft. Success: the Build is written (and becomes `latest`), the draft and its old `failed/` file
    are removed. Failure: `BuildFailed` is raised and the draft keeps it as `last_failure`."""
    from steamstudy.build.writer import write_build, write_failed_parse_errors
    from steamstudy.collect.run import snapshots_dir
    from steamstudy.config import ConfigError
    from steamstudy.lightweight import LightweightError, open_build_source

    from steamstudy.build.import_build import build_import, is_import, open_import

    progress = on_progress or (lambda stage: None)
    stop = should_stop or (lambda: False)
    root = Path(root)
    check_name(root, draft.source_id, draft.name, ignore_slug=draft.stored_slug)
    build_id = None
    identity = BuildIdentity(name=draft.name, description=draft.description or None,
                             parent_build_id=draft.parent_build_id, changelog=tuple(draft.changelog))
    try:
        build_id = new_build_id(draft_config_hash(draft), now)
        progress("open")
        if is_import(root, draft.source_id):
            source = open_import(root, draft.source_id)
            if stop():
                raise BuildCancelled("stopped before the Build ran")
            progress("build")
            result = build_import(source, draft.config, build_id, identity=identity)
        else:
            config = build_config(draft.config)
            opened = open_build_source(snapshots_dir(root), draft.source_id, from_raw=from_raw)
            if stop():
                raise BuildCancelled("stopped before the Build ran")
            progress("build")
            result = build(opened.source, config, build_id, identity=identity)
        if stop():
            raise BuildCancelled("stopped before the Build was written")
        progress("write")
        folder = write_build(result, root)
    except (BuildFailed, ConfigError, LightweightError) as exc:
        _remove_failure_file(root, draft)
        if isinstance(exc, BuildFailed) and exc.parse_errors and build_id:
            path = write_failed_parse_errors(root, draft.source_id, build_id, exc.parse_errors)
            draft.last_failure = {"kind": "parse_errors", "count": len(exc.parse_errors),
                                  "path": path.relative_to(root).as_posix(), "message": str(exc)}
        else:
            draft.last_failure = {"kind": "message", "message": str(exc)}
        save_draft(root, draft)
        if isinstance(exc, BuildFailed):
            raise
        raise BuildFailed(str(exc)) from exc
    discard_draft(root, draft)
    return folder


# ----------------------------------------------------------------------------- identical settings and parents


@dataclass(frozen=True)
class IdenticalBuild:
    ref: str
    name: str
    versions_differ: bool  # its software versions differ from this software's


def identical_builds(root: Path, source_id: str, config_hash: str) -> list[IdenticalBuild]:
    """Builds of this source with the same settings: allowed, but the menu warns, naming them."""
    if not (builds_dir(root) / source_id).is_dir():
        return []
    here = software_versions()
    return [IdenticalBuild(b.ref, b.name, b.software_versions != here)
            for b in list_builds(root, source_id) if b.config_hash == config_hash]


def parent_name(root: Path, parent_build_id: str | None) -> str | None:
    """The parent's name, or None when it was deleted ("from a deleted Build")."""
    if not parent_build_id:
        return None
    try:
        return _info(root, parent_build_id).name
    except FileNotFoundError:
        return None


# ----------------------------------------------------------------------------- delete


@dataclass
class DeletionPlan:
    """What the Delete confirmation lists. Informational: there is no protected Build."""

    ref: str
    name: str
    size_bytes: int
    app_cache_bytes: int
    bundles: list[str]  # zips in bundles/ whose name holds the build_id (they keep working)
    latest_moves: dict[str, str | None]  # "<source_id>" or "root" -> the Build it will name (None: removed)
    orphaned_builds: list[str]  # Builds that will show "from a deleted Build"
    orphaned_drafts: list[str]  # "<source_id>/<draft name>"


def _size(path: Path) -> int:
    return sum(p.stat().st_size for p in path.rglob("*") if p.is_file()) if path.is_dir() else 0


def _newest(builds: list[BuildInfo]) -> BuildInfo | None:
    return max(builds, key=lambda b: (b.build_id.split("-", 1)[0], b.build_id), default=None)


def deletion_plan(root: Path, ref: str, open_build: str | None) -> DeletionPlan:
    root = Path(root)
    info = _info(root, ref)
    if open_build and open_build == info.ref:
        raise DeleteRefused("this Build is open in this tab: switch to another Build first")
    base = builds_dir(root)
    rest = [b for b in list_builds(root) if b.ref != info.ref]
    moves: dict[str, str | None] = {}
    pointer = base / info.source_id / "latest"
    if pointer.is_file() and pointer.read_text(encoding="utf-8").strip() == info.build_id:
        newest = _newest([b for b in rest if b.source_id == info.source_id])
        moves[info.source_id] = newest.ref if newest else None
    root_pointer = base / "latest"
    if root_pointer.is_file() and root_pointer.read_text(encoding="utf-8").strip() == info.ref:
        newest = _newest(rest)
        moves["root"] = newest.ref if newest else None
    bundles = base.parent / "bundles"
    zips = sorted(p.name for p in bundles.glob("*.zip") if info.build_id in p.name) if bundles.is_dir() else []
    drafts = [f"{s.name}/{d.name}" for s in sorted(base.iterdir()) if s.is_dir()
              for d in list_drafts(root, s.name) if d.parent_build_id == info.ref]
    return DeletionPlan(ref=info.ref, name=info.name, size_bytes=_size(info.path),
                        app_cache_bytes=_size(info.path / "app_cache"), bundles=zips, latest_moves=moves,
                        orphaned_builds=[b.ref for b in rest if b.parent_build_id == info.ref],
                        orphaned_drafts=drafts)


def delete_build(root: Path, ref: str, open_build: str | None) -> DeletionPlan:
    """Remove the Build folder (cache included) and move the `latest` pointers that named it.
    Refuses the caller's open Build. Jobs running on it must be cancelled by the caller first."""
    plan = deletion_plan(root, ref, open_build)
    base = builds_dir(root)
    shutil.rmtree(base / plan.ref)
    for where, target in plan.latest_moves.items():
        pointer = base / "latest" if where == "root" else base / where / "latest"
        if target is None:
            pointer.unlink(missing_ok=True)
        else:
            pointer.write_text((target if where == "root" else target.split("/", 1)[1]) + "\n", encoding="utf-8")
    return plan

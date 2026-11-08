"""The Build tree: every source's Builds by lineage, with its drafts (the Build menu and Manage Builds…).

Dash-free, read from disk on each call. One tree per source (a Snapshot or an Import). In the repository the root is
`config/` (a Snapshot) or "Import defaults" (an Import), and drafts hang under the Build they started from. In an App
Bundle (`bundle=True`) there is no root row and no drafts: a Build whose parent is not in the Bundle sits at the top
"from <parent name> (not in this Bundle)".

A Build whose parent was deleted sits at the root, marked `orphan="deleted"`.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from steamstudy.build.core import build_date
from steamstudy.build_admin import Draft, list_drafts
from steamstudy.builds import BuildInfo, builds_dir, list_builds

ROOT_LABELS = {"snapshot": "config/", "import": "Import defaults"}


@dataclass
class BuildNode:
    info: BuildInfo
    latest: bool
    test: bool
    date: str
    top_n: str  # "Overall 100 · Puzzle 50 · 20 tags per game"
    size_bytes: int = 0
    app_cache_bytes: int = 0
    orphan: str | None = None  # "deleted", or (in a Bundle) "not in this Bundle"
    parent_name: str | None = None
    children: list[BuildNode] = field(default_factory=list)
    drafts: list[Draft] = field(default_factory=list)

    @property
    def ref(self) -> str:
        return self.info.ref


@dataclass
class SourceTree:
    source_id: str
    kind: str  # "snapshot" | "import"
    forms: tuple[str, ...]  # a Snapshot's ("raw", "lightweight"); an Import's ("import",)
    builds: list[BuildNode]  # top level: children of the root (or of nothing, in a Bundle)
    drafts: list[Draft]  # drafts started from the defaults (or from a Build that is gone)

    @property
    def root_label(self) -> str:
        return ROOT_LABELS[self.kind]


def is_bundle(root: Path) -> bool:
    """Whether the app runs from an App Bundle (no Snapshots, Imports or config to make Builds from)."""
    return (Path(root) / "bundle.json").is_file() or not (Path(root) / "config").is_dir()


def folder_bytes(path: Path) -> int:
    return sum(p.stat().st_size for p in path.rglob("*") if p.is_file()) if path.is_dir() else 0


def _top_n(build_json: dict[str, Any]) -> str:
    config = build_json.get("resolved_config") or build_json.get("config") or {}
    datasets = (config.get("datasets") or {})
    parts = [f"{d.get('label', d.get('key'))} {d.get('list_size', 100)}" for d in datasets.get("dataset", [])]
    depth = datasets.get("tag_depth", "all" if build_json.get("source") == "import" else 20)
    return " · ".join([*parts, f"{depth} tags per game"]) if parts else ""


def _pointer(path: Path) -> str | None:
    return path.read_text(encoding="utf-8").strip().replace("\\", "/") if path.is_file() else None


def _sources(root: Path, bundle: bool) -> list[tuple[str, str, tuple[str, ...]]]:
    from steamstudy.imports import imports_dir
    from steamstudy.lightweight import SUFFIX

    found: dict[str, tuple[str, tuple[str, ...]]] = {}
    base = builds_dir(root)
    if not bundle:
        snaps = root / "snapshots"
        for p in sorted(snaps.iterdir()) if snaps.is_dir() else []:
            if p.is_dir() and (p / "snapshot.json").is_file():
                forms = ("raw", "lightweight") if (snaps / f"{p.name}{SUFFIX}").is_file() else ("raw",)
                found[p.name] = ("snapshot", forms)
            elif p.name.endswith(SUFFIX) and p.name[: -len(SUFFIX)] not in found:
                found[p.name[: -len(SUFFIX)]] = ("snapshot", ("lightweight",))
        imps = imports_dir(root)
        for p in sorted(imps.iterdir()) if imps.is_dir() else []:
            if (p / "import.json").is_file():
                found[p.name] = ("import", ("import",))
    for p in sorted(base.iterdir()) if base.is_dir() else []:
        if p.is_dir() and p.name not in found and any((b / "datasets" / "build.json").is_file() for b in p.iterdir()):
            kind = "import" if any(json.loads((b / "datasets" / "build.json").read_text(encoding="utf-8"))
                                   .get("source") == "import" for b in p.iterdir()
                                   if (b / "datasets" / "build.json").is_file()) else "snapshot"
            found[p.name] = (kind, ())
    return [(sid, kind, forms) for sid, (kind, forms) in sorted(found.items())]


def build_tree(root: Path, *, bundle: bool | None = None, sizes: bool = False) -> list[SourceTree]:
    root = Path(root)
    bundle = is_bundle(root) if bundle is None else bundle
    base = builds_dir(root)
    root_latest = _pointer(base / "latest")
    every = {b.ref: b for b in list_builds(root)}
    trees = []
    for source_id, kind, forms in _sources(root, bundle):
        latest = _pointer(base / source_id / "latest")
        nodes: dict[str, BuildNode] = {}
        for info in sorted((b for b in every.values() if b.source_id == source_id), key=lambda b: b.build_id):
            bj = json.loads((info.path / "datasets" / "build.json").read_text(encoding="utf-8"))
            nodes[info.ref] = BuildNode(
                info=info, latest=info.build_id == latest or info.ref == root_latest, test=info.mode == "test",
                date=build_date(info.build_id), top_n=_top_n(bj),
                size_bytes=folder_bytes(info.path) if sizes else 0,
                app_cache_bytes=folder_bytes(info.path / "app_cache") if sizes else 0)
        top: list[BuildNode] = []
        for node in nodes.values():
            parent = node.info.parent_build_id
            if parent and parent in nodes:
                nodes[parent].children.append(node)
                continue
            if parent:
                node.parent_name = _parent_name_from_bundle(root, parent) if bundle else None
                node.orphan = "not in this Bundle" if bundle and node.parent_name != "deleted" else "deleted"
            top.append(node)
        root_drafts: list[Draft] = []
        if not bundle:
            for draft in list_drafts(root, source_id):
                if draft.parent_build_id and draft.parent_build_id in nodes:
                    nodes[draft.parent_build_id].drafts.append(draft)
                else:
                    root_drafts.append(draft)
        trees.append(SourceTree(source_id, kind, forms, top, root_drafts))
    return trees


def _parent_name_from_bundle(root: Path, parent_ref: str) -> str | None:
    """The parent's name the Bundle recorded at make time (`bundle.json`), when it did."""
    manifest = root / "bundle.json"
    if not manifest.is_file():
        return None
    for entry in json.loads(manifest.read_text(encoding="utf-8")).get("build_entries", []):
        if entry.get("parent_build_id") == parent_ref:
            return entry.get("parent_name")
    return None


def walk(nodes: list[BuildNode], depth: int = 0) -> list[tuple[int, BuildNode]]:
    """(depth, node) in display order: each Build, then its children."""
    out: list[tuple[int, BuildNode]] = []
    for node in nodes:
        out.append((depth, node))
        out.extend(walk(node.children, depth + 1))
    return out

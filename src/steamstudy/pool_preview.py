"""The Eligible Pool preview: what a draft's settings would put in each dataset, before it is built (issue 32).

Dash-free. `load_records` reads a source's records once: a Snapshot's lightweight form or an Import's normalised
tables (a raw-only Snapshot has none, and is not previewed). `preview` then runs the Build stage's own steps on them
(`core.apply_manual_metadata`, the list validation and `core.select_datasets`), so there is no second implementation:
each dataset's Eligible Pool against its List Size, the would-be Overall ranks of excluded games, and the games that
would enter and leave Overall compared with the draft's source Build (else the source's `latest`).

A preview is keyed by a hash of the settings plus the source's id and extract version (an Import: its sha256); the
dialog's Build button needs a preview of the current key.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from steamstudy.config import ConfigError, canonical_json


@dataclass
class Records:
    """A source's records as the Build stage reads them (games before Manual Metadata)."""

    source_id: str
    kind: str  # "snapshot" | "import"
    version: str  # the extract version, or an Import's sha256
    test: bool  # a test Snapshot: a short pool is a warning, as in the Build
    scores: dict[int, Any]
    games: dict[int, Any]
    source: Any = None  # the ImportSource (an Import's settings resolve against it)


@dataclass
class PoolPreview:
    key: str
    pools: dict[str, tuple[int, int]] = field(default_factory=dict)  # dataset key -> (eligible, List Size)
    tops: dict[str, list[int]] = field(default_factory=dict)  # dataset key -> its Top-N, in rank order
    ties: dict[str, list[int]] = field(default_factory=dict)  # dataset key -> the ties at its cutoff
    would_be: list[tuple[int, str, int, list[str]]] = field(default_factory=list)  # (id, name, rank, rules)
    entering: list[tuple[int, str]] = field(default_factory=list)
    leaving: list[tuple[int, str]] = field(default_factory=list)
    compared_with: str | None = None  # the Build entering/leaving compare with
    error: str | None = None  # cannot compute: the reason
    error_step: str | None = None
    not_previewed: bool = False  # a raw-only Snapshot
    short: list[str] = field(default_factory=list)  # "Overall: 87 eligible, List Size 100"
    test: bool = False

    @property
    def problems(self) -> list[str]:
        """What marks the draft red: a pool too small for its List Size (a test Snapshot only warns)."""
        return [] if self.test else list(self.short)

    @property
    def buildable(self) -> bool:
        return self.not_previewed or (self.error is None and not self.problems)


def preview_key(settings: dict[str, Any], source_id: str, version: str) -> str:
    return hashlib.sha256(f"{canonical_json(settings)}|{source_id}|{version}".encode("utf-8")).hexdigest()


def source_version(root: Path, source_id: str) -> tuple[str, str] | None:
    """(kind, version) of a source with a previewable form; None for a raw-only Snapshot or a missing source."""
    from steamstudy.build.import_build import is_import
    from steamstudy.lightweight import light_path, read_light_meta

    if is_import(root, source_id):
        import json

        from steamstudy.imports import imports_dir

        meta = json.loads((imports_dir(root) / source_id / "import.json").read_text(encoding="utf-8"))
        return "import", str(meta.get("sha256", ""))
    path = light_path(root / "snapshots", source_id)
    if not path.is_file():
        return None
    meta = read_light_meta(path)
    stat = path.stat()
    return "snapshot", f"{meta.get('extract_version')}:{stat.st_size}:{int(stat.st_mtime)}"


def load_records(root: Path, source_id: str) -> Records | None:
    """The source's records (about 2.8 s for the full Snapshot), or None when it cannot be previewed."""
    found = source_version(root, source_id)
    if found is None:
        return None
    kind, version = found
    if kind == "import":
        from steamstudy.build.import_build import import_records, open_import

        source = open_import(root, source_id)
        import_games, import_scores = import_records(source)
        return Records(source_id, kind, version, False, dict(import_scores), dict(import_games), source)
    from steamstudy.build.core import _read_histories
    from steamstudy.build.games import read_game
    from steamstudy.build.pool import listing_from_pages
    from steamstudy.build.score import Window
    from steamstudy.lightweight import open_build_source

    opened = open_build_source(root / "snapshots", source_id)
    src = opened.source
    meta = src.meta
    window = Window(meta["observation_window"]["first"], meta["observation_window"]["last"])
    errors: list[dict[str, Any]] = []
    listing = listing_from_pages(src.listing_pages())
    apps = _read_histories(src, listing, window, errors)
    scores = {a: r.score for a, r in apps.items() if r.score is not None}
    games = {a: read_game(src, a, apps[a].listing_name or "", errors) for a in scores}
    return Records(source_id, kind, version, meta.get("mode") == "test", scores, games)


def _step_of(message: str) -> str:
    from steamstudy.build_admin import STEP_OF_FILE

    file = message.split(".", 1)[0].split(":", 1)[0].split("[", 1)[0].strip()
    return STEP_OF_FILE.get(file.replace(".toml", ""), "top_n")


def preview(records: Records, settings: dict[str, Any], *, compare: list[int] | None = None,
            compared_with: str | None = None) -> PoolPreview:
    """The pools a draft's settings would give, on the Build stage's own code."""
    from steamstudy.build.core import (BuildFailed, apply_manual_metadata, select_datasets, steam_lists)
    from steamstudy.build.datasets import would_be_rank

    out = PoolPreview(preview_key(settings, records.source_id, records.version), test=records.test)
    try:
        if records.kind == "import":
            from steamstudy.build.import_build import import_config, import_lists, import_rank_key

            config = import_config(settings, records.source)
            games = records.games
            manual, overrides = import_lists(config)
            chosen = select_datasets(config, records.scores, games, manual, overrides, key=import_rank_key)
        else:
            from steamstudy.config import build_config

            config = build_config(settings)
            games, _ = apply_manual_metadata(config, records.games)
            manual, overrides = steam_lists(config)
            chosen = select_datasets(config, records.scores, games, manual, overrides)
    except (ConfigError, BuildFailed, ValueError, KeyError) as exc:
        out.error = str(exc)
        out.error_step = _step_of(str(exc))
        return out
    for key, r in chosen.ranked.items():
        n = r.definition.list_size
        out.pools[key] = (len(r.eligible), n)
        out.tops[key], out.ties[key] = list(r.top), list(r.ties)
        if len(r.eligible) < n:
            out.short.append(f"{r.definition.label}: {len(r.eligible)} eligible, List Size {n}")
    overall = chosen.ranked.get("overall") or next(iter(chosen.ranked.values()), None)
    if overall is not None:
        depth = config.depth_cut
        cut = overall.definition.list_size
        rows = []
        for a in sorted(chosen.excluded):
            rank = would_be_rank(overall, a, records.scores, games, depth)
            if rank is not None and rank <= cut:
                rows.append((a, games[a].name, rank, [m.rule for m in chosen.evaluations[a].matches]))
        out.would_be = sorted(rows, key=lambda r: r[2])
        if compare is not None:
            now, before = list(overall.top), set(compare)
            names = {a: games[a].name for a in now if a in games}
            out.entering = [(a, names.get(a, str(a))) for a in now if a not in before]
            out.leaving = [(a, games[a].name if a in games else str(a)) for a in compare if a not in set(now)]
            out.compared_with = compared_with
    return out

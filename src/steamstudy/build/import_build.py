"""The Build of an Import: `build_import(source, files, build_id) -> BuildResult`, one deterministic derivation.

An Import Build reads the reduced config set (`IMPORT_FILES`): attributes are named by `name` (numbered Imports) or
`{ id, name }` (Imports with `attributes.csv`), and Manual Exclusions and Exclusion Overrides are keyed by item `id`.
The settings are resolved against the Import's vocabulary into the Steam shape, so the Build's own exclusion,
ranking and analysis code runs unchanged; an attribute the Import does not have fails the Build. The Eligible Pool is
the whole Import minus its Exclusions; the rank is the Import's own (score descending, then file order).

Tables are assembled under their Steam names and converted to their Import variants (`export.schema.REGISTRY.variant`)
at the end, so an Import Build writes exactly the files the registry lists for its kind.
"""

from __future__ import annotations

import dataclasses
import json
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from steamstudy.analysis.templates import wording
from steamstudy.build import assemble as A
from steamstudy.build.assemble import GameTable
from steamstudy.build.core import BuildFailed, BuildIdentity, BuildResult, build_date
from steamstudy.build.datasets import RankedDataset, rank_pool, slice_top
from steamstudy.build.exclusion import ExclusionListError, content_flags, evaluate, validate_manual_exclusions
from steamstudy.build.games import Game
from steamstudy.build.parse import StoreTag
from steamstudy.config import (
    COLLECTION_FILE,
    MINIMAL_COLLECTION,
    Config,
    ConfigError,
    canonical_json,
    config_from_data,
    load_config,
)
from steamstudy.export import schema as S
from steamstudy.export.schema import FileSchema
from steamstudy.imports import ImportTables, imports_dir, load_import
from steamstudy.versions import software_versions

IMPORT_FILES = ("datasets", "exclusions", "exclusion_overrides", "manual_exclusions", "genres", "analysis", "network")
_NOT_FOR_IMPORTS = {
    "exclusions": ("allowed_app_types", "per_tag_rank_limit", "content_flags", "adult_content", "software_tag",
                   "dating_sim_tag"),
    "genres": ("genre_kind",),
}
_STEAM_SIGNALS = ("tags", "name_only", "content_descriptor_ids", "adult_only_notice")


@dataclass(frozen=True)
class ImportSource:
    """A stored Import, as a Build reads it."""

    import_id: str
    meta: dict[str, Any]  # import.json
    tables: ImportTables

    @property
    def longest_list(self) -> int:
        return max(len(i.attribute_ids) for i in self.tables.items)


def open_import(root: Path, import_id: str) -> ImportSource:
    folder = imports_dir(root) / import_id
    if not (folder / "import.json").is_file():
        raise FileNotFoundError(f"Import {import_id} not found under {imports_dir(root)}")
    meta = json.loads((folder / "import.json").read_text(encoding="utf-8"))
    return ImportSource(import_id, meta, load_import(folder))


def is_import(root: Path, source_id: str) -> bool:
    return (imports_dir(root) / source_id / "import.json").is_file()


# ----------------------------------------------------------------------------- settings


def import_defaults(source: ImportSource, config_dir: Path = Path("config")) -> dict[str, dict[str, Any]]:
    """The Import defaults (the tree root, and `steamstudy build --import`): one dataset `overall` with List Size
    min(100, item count), Tag Depth `all`, no rules, Content Flags or Genre Tags, empty manual lists, and
    `analysis` / `network` copied from `config/`."""
    config = load_config(config_dir)
    return {
        "datasets": {"tag_depth": "all", "dataset": [
            {"key": "overall", "label": "Overall", "list_size": min(100, len(source.tables.items))}]},
        "exclusions": {"rule": [], "content_flag": []},
        "exclusion_overrides": {},
        "manual_exclusions": {},
        "genres": {"genre_tags": []},
        "analysis": json.loads(json.dumps(config.files["analysis"])),
        "network": json.loads(json.dumps(config.files["network"])),
    }


def read_import_config_dir(directory: Path) -> dict[str, dict[str, Any]] | None:
    """The reduced config set in a folder, or None when the folder does not hold one (no `datasets.toml`, or a
    Steam config set, which has `collection.toml`)."""

    directory = Path(directory)
    if not (directory / "datasets.toml").is_file() or (directory / f"{COLLECTION_FILE}.toml").is_file():
        return None
    files = {}
    for name in IMPORT_FILES:
        path = directory / f"{name}.toml"
        if not path.is_file():
            raise ConfigError(f"missing config file for an Import Build: {path}")
        files[name] = tomllib.loads(path.read_text(encoding="utf-8"))
    return files


class _Vocabulary:
    def __init__(self, tables: ImportTables):
        self.supplied = tables.attribute_ids == "supplied"
        self.by_name = {name: i for i, name in tables.attributes.items()}
        self.by_id = dict(tables.attributes)

    def ref(self, entry: Any, where: str) -> dict[str, Any]:
        """`{ name }` (numbered) or `{ id, name }` (supplied ids) resolved to `{ id, name }`; checked both ways."""
        if isinstance(entry, str):
            entry = {"name": entry}
        if not isinstance(entry, dict) or not isinstance(entry.get("name"), str):
            raise ConfigError(f"{where}: expected {{ name = ... }}" + (" with an id" if self.supplied else ""))
        name = entry["name"]
        if name not in self.by_name:
            raise ConfigError(f"{where}: attribute {name!r} is not in the Import")
        attr_id = self.by_name[name]
        if "id" in entry:
            if entry["id"] != attr_id:
                raise ConfigError(f"{where}: attribute {name!r} has id {attr_id} in the Import, not {entry['id']}")
        elif self.supplied:
            raise ConfigError(f"{where}: this Import supplies attribute ids; name {name!r} needs its id ({attr_id})")
        out = {"id": attr_id, "name": name}
        if "rank_limit" in entry:
            out["rank_limit"] = entry["rank_limit"]
        return out


def _entries(table: dict[str, Any], key: str, where: str, item_ids: set[int]) -> list[dict[str, Any]]:
    """Manual Exclusions / Overrides keyed by item `id`, as the Steam validator reads them (`appid`)."""
    out = []
    for i, entry in enumerate(table.get(key, [])):
        w = f"{where} entry {i + 1}"
        if not isinstance(entry, dict) or "appid" in entry:
            raise ConfigError(f"{w}: an Import Build keys entries by item id (`id`), not `appid`")
        item = entry.get("id")
        if not isinstance(item, int) or isinstance(item, bool):
            raise ConfigError(f"{w}: id must be an integer")
        if item not in item_ids:
            raise ConfigError(f"{w}: item {item} is not in the Import")
        out.append({**{k: v for k, v in entry.items() if k != "id"}, "appid": item})
    return out


def resolve_settings(files: dict[str, dict[str, Any]], source: ImportSource) -> dict[str, dict[str, Any]]:
    """An Import Build's settings in the Steam shape the Build stage reads. Raises `ConfigError`."""
    missing = [n for n in IMPORT_FILES if n not in files]
    if missing:
        raise ConfigError(f"an Import Build needs the config files {', '.join(missing)}")
    extra = [n for n in files if n not in IMPORT_FILES]
    if extra:
        raise ConfigError(f"not settings of an Import Build: {', '.join(sorted(extra))}")
    for name, keys in _NOT_FOR_IMPORTS.items():
        for key in keys:
            if key in files[name]:
                raise ConfigError(f"{name}.{key}: not a setting of an Import Build")
    vocab = _Vocabulary(source.tables)
    out = json.loads(json.dumps(files))

    datasets = out["datasets"]
    for i, d in enumerate(datasets.get("dataset", [])):
        if isinstance(d, dict) and d.get("defining_tag") is not None:
            d["defining_tag"] = vocab.ref(d["defining_tag"], f"datasets.dataset[{i}].defining_tag")
    depth = datasets.get("tag_depth", "all")
    if isinstance(depth, int) and not isinstance(depth, bool) and depth > source.longest_list:
        raise ConfigError(f"datasets.tag_depth: the Import's longest attribute list has {source.longest_list} "
                          f"attributes, got {depth}; use \"all\"")
    if "tag_depth" not in datasets:
        datasets["tag_depth"] = "all"

    ex = out["exclusions"]
    for kind in ("rule", "content_flag"):
        for i, item in enumerate(ex.get(kind, [])):
            w = f"exclusions.{kind}[{i}]"
            if not isinstance(item, dict):
                raise ConfigError(f"{w}: expected a table")
            steam = [k for k in _STEAM_SIGNALS if k in item]
            if steam:
                raise ConfigError(f"{w}.{steam[0]}: not a setting of an Import Build (name attributes in "
                                  "`attributes`)")
            attrs = item.pop("attributes", [])
            if not isinstance(attrs, list):
                raise ConfigError(f"{w}.attributes: expected a list")
            if kind == "content_flag" and any(isinstance(a, dict) and "rank_limit" in a for a in attrs):
                raise ConfigError(f"{w}.attributes: a Content Flag has no rank limit")
            item["tags"] = [vocab.ref(a, f"{w}.attributes[{j}]") for j, a in enumerate(attrs)]
    ex["allowed_app_types"] = ["game"]  # every item counts as a game; the fixed Steam rules never fire

    genres = out["genres"]
    genres["genre_tags"] = [vocab.ref(g, f"genres.genre_tags[{i}]")
                            for i, g in enumerate(genres.get("genre_tags", []))]

    item_ids = {i.id for i in source.tables.items}
    out["manual_exclusions"] = {"exclusion": _entries(files["manual_exclusions"], "exclusion",
                                                      "manual_exclusions.toml", item_ids)}
    out["exclusion_overrides"] = {"override": _entries(files["exclusion_overrides"], "override",
                                                       "exclusion_overrides.toml", item_ids)}
    rules = [r.get("name") for r in ex.get("rule", []) if isinstance(r, dict)]
    for i, o in enumerate(out["exclusion_overrides"]["override"]):
        if o.get("rule") not in rules:
            raise ConfigError(f"exclusion_overrides.toml entry {i + 1} (id {o['appid']}): rule {o.get('rule')!r} is "
                              f"not a named rule of this Build; it must be one of {tuple(rules)}")
    out["manual_metadata"] = {}
    return out


def import_config(files: dict[str, dict[str, Any]], source: ImportSource) -> Config:
    """The `Config` of an Import Build: computed from the resolved settings, identified (`files`, the hash) by the
    settings as written."""
    resolved = resolve_settings(files, source)
    config = config_from_data({**resolved, COLLECTION_FILE: MINIMAL_COLLECTION}, source="import")
    return dataclasses.replace(config, files=json.loads(canonical_json(files)))


# ----------------------------------------------------------------------------- the Build


@dataclass(frozen=True)
class ImportScore:
    """What ranking reads of an item: its score (None without one), its filter value and its Import rank."""

    mean_monthly_players: float | None
    months_observed: float | None
    rank: int


def import_rank_key(item_id: int, s: ImportScore) -> tuple[int, int]:
    return (s.rank, item_id)


class ImportGame(Game):
    """An item as the exclusion rules read it: always with data, of app type game, its attributes as tags."""

    @property
    def has_data(self) -> bool:
        return True


def import_games(tables: ImportTables) -> dict[int, Game]:
    games: dict[int, Game] = {}
    for item in tables.items:
        tags = tuple(StoreTag(a, tables.attributes[a], 0, p + 1) for p, a in enumerate(item.attribute_ids))
        games[item.id] = ImportGame(appid=item.id, name=item.name, page_outcome="import", details_outcome="import",
                                    tags=tags, app_type="game", metadata_source="import")
    return games


def build_import(source: ImportSource, files: dict[str, dict[str, Any]], build_id: str, *,
                 identity: BuildIdentity | None = None) -> BuildResult:
    try:
        config = import_config(files, source)
    except ConfigError as exc:
        raise BuildFailed(str(exc)) from exc
    t = source.tables
    result = BuildResult(snapshot_id=source.import_id, build_id=build_id)
    games = import_games(t)
    scores = {i.id: ImportScore(i.score, i.filter_value, i.rank) for i in t.items}
    try:
        manual = validate_manual_exclusions(config.manual_exclusions)
        overrides = {(e["appid"], e["rule"]): e for e in config.exclusion_overrides}
    except ExclusionListError as exc:
        raise BuildFailed(str(exc)) from exc
    from steamstudy.build.exclusion import _validate_list

    try:
        _validate_list(config.exclusion_overrides, "exclusion_overrides.toml")
    except ExclusionListError as exc:
        raise BuildFailed(str(exc)) from exc
    evaluations = {a: evaluate(games[a], config.exclusions, manual, overrides) for a in sorted(games)}
    excluded = {a for a, ev in evaluations.items() if ev.excluded}
    flags = {a: content_flags(games[a], config.exclusions) for a in games}

    depth = config.depth_cut
    ranked: dict[str, RankedDataset] = {}
    for d in config.datasets:
        r = slice_top(rank_pool(d, scores, games, excluded, depth, import_rank_key), scores)
        if len(r.top) < d.list_size:
            raise BuildFailed(f"dataset {d.key} has only {len(r.eligible)} eligible items; every dataset must hold "
                              f"exactly {d.list_size}")
        ranked[d.key] = r

    table = GameTable(scores, games, {}, {}, ranked, flags, depth)  # type: ignore[arg-type]
    keys = list(ranked)
    by_id = {i.id: i for i in t.items}
    for key, r in ranked.items():
        rows = [{"dataset": key, "rank": n, "appid": a, "name": games[a].name,
                 "mean_monthly_players": by_id[a].score, "months_observed": by_id[a].filter_value,
                 "tag_ids": [x.tag_id for x in games[a].tags], "tags": [x.name for x in games[a].tags],
                 "content_flags": flags.get(a, [])} for n, a in enumerate(r.top, start=1)]
        result.dataset_rows[key] = rows
        result.add(f"datasets/topn_{key}.csv", S.TOPN, [
            {"dataset": key, "rank": row["rank"], "id": row["appid"], "name": row["name"],
             "score": row["mean_monthly_players"], "filter_value": row["months_observed"], "tag_ids": row["tag_ids"],
             "tags": row["tags"]} for row in rows])
    members = sorted({a for r in ranked.values() for a in r.top})
    result.add("datasets/item_fields.csv", S.ITEM_FIELDS,
               [{"id": a, "field": f, "value": t.fields[a][f]} for a in members for f in t.extra_fields
                if f in t.fields.get(a, {})])

    excluded_evals = {a: ev for a, ev in evaluations.items() if ev.excluded}
    if t.score_present:
        result.add("reports/ties.csv", S.TIES, A.ties_rows(table))
    result.add("reports/exclusions.csv", S.EXCLUSIONS.for_datasets(keys), A.exclusion_rows(table, excluded_evals))
    result.add("reports/impact_removals.csv", S.IMPACT_REMOVALS.for_datasets(keys),
               A.impact_removal_rows(table, excluded_evals))
    result.add("reports/impact_near_misses.csv", S.IMPACT_NEAR_MISSES.for_datasets(keys),
               A.near_miss_rows(table, evaluations))
    result.add("reports/completeness.csv", S.COMPLETENESS, _completeness(source, evaluations, config, ranked))

    result.build_json = _build_json(source, config, build_id, identity or BuildIdentity())
    result.build_json["exclusion_overrides_applied"] = [
        {"id": a, "rule": rule, "reason": overrides[(a, rule)]["reason"]}
        for a, ev in evaluations.items() for rule in ev.overridden]
    result.build_json["dataset_sizes"] = {k: {"rows": len(r.top), "eligible_pool": len(r.eligible)}
                                          for k, r in ranked.items()}
    result.build_json["warnings"] = list(result.warnings)
    result.ranked, result.scores, result.games = ranked, scores, games  # type: ignore[assignment]

    from steamstudy.analysis.report import report_html
    from steamstudy.analysis.run import run_analysis
    from steamstudy.analysis.templates import CausalLanguageError

    run_analysis(result, config)
    try:
        result.texts["analysis/report.html"] = report_html(result, config)
        result.texts["reports/reports.html"] = import_reports_html(result, config, source)
    except CausalLanguageError as exc:
        raise BuildFailed(str(exc)) from exc
    _to_import_variants(result)
    return result


def _completeness(source: ImportSource, evaluations: dict[int, Any], config: Config,
                  ranked: dict[str, RankedDataset]) -> list[dict[str, Any]]:
    def row(section: str, item: str, value: int, note: str, dataset: str = "") -> dict[str, Any]:
        return {"section": section, "item": item, "dataset": dataset, "value": value, "note": note}

    codes = [*(r.name for r in config.exclusions.rules), "manual"]
    overlapping = {c: 0 for c in codes}
    primary = {c: 0 for c in codes}
    for ev in evaluations.values():
        for m in ev.matches:
            overlapping[m.rule] += 1
        if ev.primary_reason:
            primary[ev.primary_reason] += 1
    rows = [row("exclusions_overlapping", c, n, "excluded items matching this rule (an item can match several)")
            for c, n in overlapping.items()]
    rows += [row("exclusions_primary", c, n, "excluded items whose primary_reason is this rule")
             for c, n in primary.items()]
    rows.append(row("exclusions_primary", "excluded_games", sum(primary.values()), "items excluded by any rule"))
    top_h = wording(config)["top_h"]
    rows += [row("depth_check", "members", len(r.top), f"items in this {top_h} Dataset", k) for k, r in ranked.items()]
    t = source.tables
    rows += [row("import", "items", len(t.items), "items in the Import"),
             row("import", "attributes", len(t.attributes), "distinct attributes in the Import"),
             row("import", "warnings", len(source.meta.get("warnings", [])), "warnings kept in import.json")]
    return rows


def _build_json(source: ImportSource, config: Config, build_id: str, identity: BuildIdentity) -> dict[str, Any]:
    n = config.network
    changelog = list(identity.changelog) if identity.changelog is not None else []
    name = identity.name or build_id
    if identity.description:
        changelog.append({"date": build_date(build_id), "title": name, "text": identity.description})
    t = source.tables
    return {
        "source": "import",
        "import_id": source.import_id,
        "import_sha256": source.meta["sha256"],
        "build_id": build_id,
        "name": name,
        "description": identity.description,
        "parent_build_id": identity.parent_build_id,
        "mode": "",
        "filter_field": t.filter_field,
        "score_present": t.score_present,
        "extra_fields": list(t.extra_fields),
        "build_config_hash": config.build_config_hash,
        "config": {name: config.files[name] for name in sorted(config.files)},
        # The settings with every attribute resolved to its id: what the app reads (the Import is not shipped).
        "resolved_config": {k: v for k, v in sorted(resolve_settings(config.files, source).items())
                            if k in IMPORT_FILES},
        "changelog": changelog,
        "network_defaults": {
            "min_games_per_tag": n.min_games_per_tag, "min_shared_games": n.min_shared_games,
            "min_months": n.min_months, "clustering_weight": n.clustering_weight, "algorithm": n.algorithm,
            "resolution": n.resolution, "seed": n.seed, "null_replicates": n.null_replicates,
            "noise_seeds": n.noise_seeds, "resolution_sweep": list(n.resolution_sweep),
        },
        "software_versions": software_versions(),
    }


def import_reports_html(result: BuildResult, config: Config, source: ImportSource) -> str:
    from steamstudy.analysis.templates import paragraph, render_report, sentence
    from steamstudy.build.summary import build_banners

    bj = result.build_json
    t = source.tables
    primary = {r["item"]: r["value"] for r in result.rows("reports/completeness.csv")
               if r["section"] == "exclusions_primary" and r["item"] != "excluded_games"}
    blocks = [paragraph("summary_intro"), "## Build",
              sentence("summary_import_build", build_id=bj["build_id"], import_id=source.import_id,
                       config_hash=bj["build_config_hash"][:12]),
              "## Import",
              sentence("summary_import", items=len(t.items), attributes=len(t.attributes),
                       attribute_ids=t.attribute_ids, rank_by="score" if t.score_present else "file order",
                       filter_field=t.filter_field or "none")]
    blocks += ["- " + sentence("summary_import_warning", code=w["code"], row=w["row"] or "-", message=w["message"])
               for w in source.meta.get("warnings", [])]
    blocks += ["## Exclusions",
               sentence("summary_import_excluded", excluded=sum(primary.values()),
                        by_reason=", ".join(f"{k} {v}" for k, v in primary.items() if v) or "none"),
               sentence("summary_overrides", count=len(bj.get("exclusion_overrides_applied", []))),
               "## Datasets"]
    for d in config.datasets:
        size = bj["dataset_sizes"][d.key]
        blocks.append("- " + sentence("summary_import_dataset", label=d.label, rows=size["rows"],
                                      pool=size["eligible_pool"]))
    if t.score_present:
        w = wording(config)
        blocks.append(sentence("summary_ties", count=len(result.rows("reports/ties.csv")), top=w["top"],
                               cutoff=w["cutoff"]))
    if result.warnings:
        blocks.append("## Warnings")
        blocks += ["- " + sentence("summary_warning", text=w) for w in result.warnings]
    blocks.append(paragraph("attribution_import", import_id=source.import_id))
    return render_report("Build report summary", blocks, config.analysis.causal_words, banners=build_banners(bj))


_FROM_STEAM = {new: old for old, new in S.IMPORT_RENAMED.items()}


def _to_import_variants(result: BuildResult) -> None:
    """Every table assembled under its Steam name becomes its Import variant (same file name)."""
    for path, (schema, rows) in list(result.tables.items()):
        if schema.kind == "import":
            continue
        variant: FileSchema = S.import_variant(schema)
        names = [c.name for c in variant.columns]
        result.tables[path] = (variant, [{n: r.get(_FROM_STEAM.get(n, n), r.get(n)) for n in names} for r in rows])


def write_import_build(result: BuildResult, root: Path) -> Path:
    from steamstudy.build.writer import write_build

    return write_build(result, root)

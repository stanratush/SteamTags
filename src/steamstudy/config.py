"""Load and validate the TOML config set in `config/`.

The parsed, normalised contents of each file are kept as plain data (`Config.files`) and hashed:
`collection_config_hash` over `collection.toml`, `build_config_hash` over every file a Build reads.
Typed views over the same data are what the rest of the package uses.
"""

from __future__ import annotations

import hashlib
import json
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

COLLECTION_FILE = "collection"
BUILD_FILES = (
    "exclusions",
    "genres",
    "datasets",
    "network",
    "analysis",
    "manual_metadata",
    "manual_exclusions",
    "exclusion_overrides",
)
ALL_FILES = (COLLECTION_FILE, *BUILD_FILES)
CHANGELOG_FILE = "CHANGELOG.md"

CLUSTERING_WEIGHTS = ("shared_games", "lift")
ALGORITHMS = ("louvain", "leiden")


class ConfigError(ValueError):
    """A config file is missing, malformed or fails validation."""


@dataclass(frozen=True)
class TagRef:
    id: int
    name: str
    rank_limit: int | None = None  # exclusion rules only: a tighter display-position limit for this tag


@dataclass(frozen=True)
class DatasetDef:
    key: str
    label: str
    defining_tag: TagRef | None
    list_size: int = 100  # List Size: how many items the Top-N Dataset holds


@dataclass(frozen=True)
class ParameterSelectionDefaults:
    """`[parameter_selection]` in network.toml: Automatic Parameter Selection's settings and Pair Constraints."""

    clustering_weight: str
    min_months: int
    min_multi_tag_clusters: int
    g_range: tuple[int, int]
    s_range: tuple[int, int]
    gamma_step: float
    scan_seeds: int
    null_replicates: int
    subsamples: int
    workers: int  # 0 = os.cpu_count() - 1
    tolerance: float
    min_retention: float
    max_isolated_share: float
    min_lcc_share: float
    min_comparable_neighbours: int
    max_multi_tag_clusters: int | None  # None = off (0 in the file)


# The shipped table, for Builds whose network.toml predates it.
PARAMETER_SELECTION_DEFAULTS: dict[str, Any] = {
    "clustering_weight": "lift", "min_months": 0, "min_multi_tag_clusters": 3, "g_range": [3, 20],
    "s_range": [2, 12], "gamma_step": 0.05, "scan_seeds": 10, "null_replicates": 100, "subsamples": 100,
    "workers": 0, "tolerance": 0.05, "min_retention": 0.50, "max_isolated_share": 0.10, "min_lcc_share": 0.90,
    "min_comparable_neighbours": 2, "max_multi_tag_clusters": 0,
}


@dataclass(frozen=True)
class NetworkDefaults:
    min_games_per_tag: int
    min_shared_games: int
    min_months: int
    hide_genre_tags: bool
    hide_defining_tag: bool
    clustering_weight: str
    algorithm: str
    resolution: float
    seed: int
    null_replicates: int
    noise_seeds: int
    resolution_sweep: tuple[float, ...]
    parameter_selection: ParameterSelectionDefaults


@dataclass(frozen=True)
class AnalysisConfig:
    max_itemset_size: int
    min_support: int
    causal_words: tuple[str, ...]
    release_month_check: int


@dataclass(frozen=True)
class ExclusionRule:
    """One named Exclusion Rule. `name` is the code written to exclusions.csv, the impact reports and overrides."""

    name: str
    label: str
    tags: tuple[TagRef, ...] = ()
    name_only: tuple[str, ...] = ()
    content_descriptor_ids: tuple[int, ...] = ()
    adult_only_notice: bool = False


@dataclass(frozen=True)
class ContentFlag:
    """A Content Flag: the same shape as a rule's tag signal, but it never filters."""

    name: str
    label: str
    tags: tuple[TagRef, ...] = ()
    name_only: tuple[str, ...] = ()


@dataclass(frozen=True)
class ExclusionConfig:
    allowed_app_types: tuple[str, ...]
    global_rank_limit: int
    rules: tuple[ExclusionRule, ...]  # named rules, in evaluation order
    content_flags: tuple[ContentFlag, ...]


@dataclass(frozen=True)
class GateRecord:
    reference: str
    date: str

    @property
    def recorded(self) -> bool:
        return bool(self.reference.strip()) and bool(self.date.strip())


@dataclass(frozen=True)
class CollectionConfig:
    user_agent: str
    listing_passes: int
    steamcharts_per_second: float
    store_seconds_per_request: float
    steamdb_seconds_per_request: float
    connect_timeout: float
    read_timeout: float
    retry_schedule: tuple[float, ...]
    parse_failures_in_a_row: int
    test_listing_pages: int
    edge_case_appids: tuple[int, ...]
    operator_reply: GateRecord
    publish_monthly_players: str
    ethics_check: GateRecord
    steamdb_permission: GateRecord


@dataclass(frozen=True)
class Config:
    directory: Path
    files: dict[str, dict[str, Any]]
    changelog: str
    collection: CollectionConfig
    exclusions: ExclusionConfig
    genre_tags: tuple[TagRef, ...]
    genre_kind: dict[int, str]
    datasets: tuple[DatasetDef, ...]
    tag_depth: int | str  # Tag Depth ("tags per game"): an integer >= 2, or the literal "all"
    network: NetworkDefaults
    analysis: AnalysisConfig
    manual_metadata: tuple[dict[str, Any], ...]
    manual_exclusions: tuple[dict[str, Any], ...]
    exclusion_overrides: tuple[dict[str, Any], ...]

    @property
    def collection_config_hash(self) -> str:
        return content_hash({COLLECTION_FILE: self.files[COLLECTION_FILE]})

    @property
    def build_config_hash(self) -> str:
        return content_hash({name: self.files[name] for name in BUILD_FILES if name in self.files})

    @property
    def depth_cut(self) -> int | None:
        """The number of leading tags that count as "has" (None = every tag); Steam shows at most 20."""
        return None if self.tag_depth == "all" else int(self.tag_depth)

    def dataset(self, key: str) -> DatasetDef:
        for d in self.datasets:
            if d.key == key:
                return d
        raise KeyError(key)

    def changelog_entries(self) -> list[dict[str, str]]:
        """`## <date>: <title>` sections of CHANGELOG.md, in file order."""
        entries: list[dict[str, str]] = []
        for line in self.changelog.splitlines():
            if line.startswith("## "):
                heading = line[3:].strip()
                date, _, title = heading.partition(":")
                entries.append({"date": date.strip(), "title": title.strip(), "text": ""})
            elif entries:
                entries[-1]["text"] = (entries[-1]["text"] + "\n" + line).strip()
        return entries


def canonical_json(data: Any) -> str:
    """Sorted keys, no whitespace, non-ASCII kept: the normal form that hashes are taken over."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def content_hash(data: Any) -> str:
    return hashlib.sha256(canonical_json(data).encode("utf-8")).hexdigest()


def load_config(directory: str | Path = "config") -> Config:
    directory = Path(directory)
    files: dict[str, dict[str, Any]] = {}
    for name in ALL_FILES:
        path = directory / f"{name}.toml"
        if not path.is_file():
            raise ConfigError(f"missing config file: {path}")
        try:
            files[name] = tomllib.loads(path.read_text(encoding="utf-8"))
        except tomllib.TOMLDecodeError as exc:
            raise ConfigError(f"{path}: {exc}") from exc
    changelog_path = directory / CHANGELOG_FILE
    changelog = changelog_path.read_text(encoding="utf-8") if changelog_path.is_file() else ""
    return config_from_data(files, directory=directory, changelog=changelog)


def config_from_data(
    files: dict[str, dict[str, Any]], *, directory: Path = Path("config"), changelog: str = "",
    source: str = "steam",
) -> Config:
    """Validate parsed TOML contents (one dict per config file) into a `Config`. `source="import"` reads the
    settings of an Import Build once its attribute names are resolved (`steamstudy.build.import_build`): no Steam
    cap on Tag Depth, and no global rank limit unless one is set."""
    files = json.loads(canonical_json(files))  # normalise to plain JSON data
    return Config(
        directory=directory,
        files=files,
        changelog=changelog,
        collection=_collection(_get(files, COLLECTION_FILE)),
        exclusions=_exclusions(_get(files, "exclusions"), source),
        genre_tags=_tag_refs(_get(files, "genres").get("genre_tags", []), "genres.genre_tags"),
        genre_kind=_genre_kind(_get(files, "genres")),
        datasets=_datasets(_get(files, "datasets")),
        tag_depth=_tag_depth(_get(files, "datasets"), source),
        network=_network(_get(files, "network")),
        analysis=_analysis(_get(files, "analysis")),
        manual_metadata=tuple(_get(files, "manual_metadata").get("entry", [])),
        manual_exclusions=tuple(_get(files, "manual_exclusions").get("exclusion", [])),
        exclusion_overrides=tuple(_get(files, "exclusion_overrides").get("override", [])),
    )



# build.json copies every file a Build reads; the collection settings are not among them.
MINIMAL_COLLECTION: dict[str, Any] = {
    "contact": {"user_agent": "-"}, "listing": {"passes": 1},
    "rates": {"steamcharts_per_second": 1.0, "store_seconds_per_request": 1.0},
    "timeouts": {"connect_seconds": 1, "read_seconds": 1},
    "retry": {"schedule_seconds": [1], "parse_failures_in_a_row": 1},
}


def build_config(files: dict[str, dict[str, Any]], *, changelog: str = "") -> Config:
    """A `Config` from a Steam Build's settings alone (a `build.json` `config` block, or a Build Draft's)."""
    return config_from_data({**files, COLLECTION_FILE: MINIMAL_COLLECTION}, changelog=changelog)


# An Import Build without a global rank limit: every position of an attribute list counts for its rules.
NO_RANK_LIMIT = 1_000_000


def exclusions_new_shape(t: dict[str, Any]) -> dict[str, Any]:
    """`exclusions.toml` data in the named-rule shape, converting the old shape; the new shape comes back as is
    (keys with nothing in them omitted, as the shipped file writes them)."""
    ex = _exclusions(t)

    def tags(refs: tuple[TagRef, ...]) -> list[dict[str, Any]]:
        return [{"id": r.id, "name": r.name, **({"rank_limit": r.rank_limit} if r.rank_limit else {})}
                for r in refs]

    def signal(item: ExclusionRule | ContentFlag) -> dict[str, Any]:
        out: dict[str, Any] = {"name": item.name, "label": item.label}
        if isinstance(item, ExclusionRule):
            if item.content_descriptor_ids:
                out["content_descriptor_ids"] = list(item.content_descriptor_ids)
            if item.adult_only_notice:
                out["adult_only_notice"] = True
        if item.tags:
            out["tags"] = tags(item.tags)
        if item.name_only:
            out["name_only"] = list(item.name_only)
        return out

    old_keys = {*_OLD_RULE_TABLES, "per_tag_rank_limit", "content_flags", "rule", "content_flag"}
    out = {k: v for k, v in t.items() if k not in old_keys}
    out["rule"] = [signal(r) for r in ex.rules]
    out["content_flag"] = [signal(f) for f in ex.content_flags]
    return json.loads(canonical_json(out))


# ----------------------------------------------------------------------------- helpers


def _get(files: dict[str, Any], name: str) -> dict[str, Any]:
    if name not in files:
        raise ConfigError(f"missing config file: {name}.toml")
    return files[name]


def _req(table: dict[str, Any], key: str, kind: type | tuple[type, ...], where: str) -> Any:
    if key not in table:
        raise ConfigError(f"{where}: missing key '{key}'")
    value = table[key]
    if kind is float and isinstance(value, int) and not isinstance(value, bool):
        value = float(value)
    if isinstance(value, bool) and kind is not bool:
        raise ConfigError(f"{where}.{key}: expected {kind}, got bool")
    if not isinstance(value, kind):
        raise ConfigError(f"{where}.{key}: expected {kind}, got {type(value).__name__}")
    return value


def _at_least(value: int | float, minimum: int | float, where: str) -> None:
    if value < minimum:
        raise ConfigError(f"{where}: must be >= {minimum}, got {value}")


def _tag_refs(items: Any, where: str) -> tuple[TagRef, ...]:
    if not isinstance(items, list):
        raise ConfigError(f"{where}: expected a list of {{id, name}} tables")
    refs = []
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            raise ConfigError(f"{where}[{i}]: expected {{id, name}}")
        refs.append(TagRef(_req(item, "id", int, f"{where}[{i}]"), _req(item, "name", str, f"{where}[{i}]")))
    return tuple(refs)


def _gate(table: dict[str, Any], where: str) -> GateRecord:
    return GateRecord(str(table.get("reference", "")), str(table.get("date", "")))


# ----------------------------------------------------------------------------- per file


def _collection(t: dict[str, Any]) -> CollectionConfig:
    w = "collection"
    contact, listing, rates = t.get("contact", {}), t.get("listing", {}), t.get("rates", {})
    timeouts, retry, test = t.get("timeouts", {}), t.get("retry", {}), t.get("test_mode", {})
    gate = t.get("gate", {})
    passes = _req(listing, "passes", int, f"{w}.listing")
    _at_least(passes, 1, f"{w}.listing.passes")
    sc_rate = _req(rates, "steamcharts_per_second", float, f"{w}.rates")
    store_rate = _req(rates, "store_seconds_per_request", float, f"{w}.rates")
    steamdb_rate = float(rates.get("steamdb_seconds_per_request", store_rate))
    for name, value in (("steamcharts_per_second", sc_rate), ("store_seconds_per_request", store_rate)):
        if value <= 0:
            raise ConfigError(f"{w}.rates.{name}: must be > 0")
    schedule = _req(retry, "schedule_seconds", list, f"{w}.retry")
    user_agent = _req(contact, "user_agent", str, f"{w}.contact")
    if not user_agent.strip():
        raise ConfigError(f"{w}.contact.user_agent: must not be empty")
    operator = gate.get("operator_reply", {})
    return CollectionConfig(
        user_agent=user_agent,
        listing_passes=passes,
        steamcharts_per_second=sc_rate,
        store_seconds_per_request=store_rate,
        steamdb_seconds_per_request=steamdb_rate,
        connect_timeout=_req(timeouts, "connect_seconds", float, f"{w}.timeouts"),
        read_timeout=_req(timeouts, "read_seconds", float, f"{w}.timeouts"),
        retry_schedule=tuple(float(s) for s in schedule),
        parse_failures_in_a_row=_req(retry, "parse_failures_in_a_row", int, f"{w}.retry"),
        test_listing_pages=int(test.get("listing_pages", 4)),
        edge_case_appids=tuple(int(a) for a in test.get("edge_case_appids", [])),
        operator_reply=_gate(operator, f"{w}.gate.operator_reply"),
        publish_monthly_players=str(operator.get("publish_monthly_players", "")),
        ethics_check=_gate(gate.get("ethics_check", {}), f"{w}.gate.ethics_check"),
        steamdb_permission=GateRecord(
            str(t.get("steamdb", {}).get("permission_reference", "")),
            str(t.get("steamdb", {}).get("permission_date", "")),
        ),
    )


FIXED_RULES = ("store_data_unavailable", "app_type", "no_tags", "manual")
_OLD_RULE_TABLES = ("adult_content", "software_tag", "dating_sim_tag")
_OLD_LABELS = {"adult_content": "Adult content", "software_tag": "Software", "dating_sim_tag": "Dating Sim"}


def _limit_value(value: Any, where: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 20:
        raise ConfigError(f"{where}: must be an integer between 1 and 20")
    return value


def _rule_tags(items: Any, where: str) -> tuple[TagRef, ...]:
    if not isinstance(items, list):
        raise ConfigError(f"{where}: expected a list of {{id, name}} tables")
    out = []
    for i, item in enumerate(items):
        w = f"{where}[{i}]"
        if not isinstance(item, dict):
            raise ConfigError(f"{w}: expected {{id, name}}")
        limit = item.get("rank_limit")
        out.append(TagRef(_req(item, "id", int, w), _req(item, "name", str, w),
                          None if limit is None else _limit_value(limit, f"{w}.rank_limit")))
    return tuple(out)


def _name_only(table: dict[str, Any], where: str) -> tuple[str, ...]:
    value = table.get("name_only", [])
    if not isinstance(value, list) or not all(isinstance(n, str) for n in value):
        raise ConfigError(f"{where}.name_only: expected a list of strings")
    return tuple(value)


def _code(name: Any, where: str) -> str:
    if not isinstance(name, str) or not re.fullmatch(r"[a-z0-9_]+", name):
        raise ConfigError(f"{where}: name {name!r} must be non-empty and use only a-z, 0-9 and _")
    return name


def _label(item: dict[str, Any], default: str, where: str) -> str:
    label = item.get("label", default)
    if not isinstance(label, str) or not label.strip():
        raise ConfigError(f"{where}.label: must not be empty")
    return label


def _named_rule(item: Any, where: str) -> ExclusionRule:
    if not isinstance(item, dict):
        raise ConfigError(f"{where}: expected a table")
    name = _code(item.get("name"), f"{where}.name")
    ids = item.get("content_descriptor_ids", [])
    if not isinstance(ids, list) or not all(isinstance(i, int) and not isinstance(i, bool) for i in ids):
        raise ConfigError(f"{where}.content_descriptor_ids: expected a list of integers")
    notice = item.get("adult_only_notice", False)
    if not isinstance(notice, bool):
        raise ConfigError(f"{where}.adult_only_notice: expected true or false")
    rule = ExclusionRule(name, _label(item, name, where), _rule_tags(item.get("tags", []), f"{where}.tags"),
                         _name_only(item, where), tuple(ids), notice)
    if not (rule.tags or rule.name_only or rule.content_descriptor_ids or rule.adult_only_notice):
        raise ConfigError(f"{where} ({name}): a rule needs at least one signal (tags, name_only, "
                          "content_descriptor_ids or adult_only_notice)")
    return rule


def _content_flag(name: Any, item: Any, where: str) -> ContentFlag:
    if not isinstance(item, dict):
        raise ConfigError(f"{where}: expected a table")
    code = _code(name, f"{where}.name")
    return ContentFlag(code, _label(item, code, where), _tag_refs(item.get("tags", []), f"{where}.tags"),
                       _name_only(item, where))


def _old_rules(t: dict[str, Any], w: str) -> tuple[ExclusionRule, ...]:
    """Today's shape (adult_content / software_tag / dating_sim_tag tables, per_tag_rank_limit) as named rules."""
    limits: dict[int, int] = {}
    for key, value in t.get("per_tag_rank_limit", {}).items():
        try:
            tag_id = int(key)
        except ValueError as exc:
            raise ConfigError(f"{w}.per_tag_rank_limit: key '{key}' is not a tag id") from exc
        limits[tag_id] = _limit_value(value, f"{w}.per_tag_rank_limit.{key}")
    rules = []
    for code in _OLD_RULE_TABLES:
        table = t.get(code, {})
        adult = code == "adult_content"
        tags = tuple(TagRef(r.id, r.name, limits.get(r.id))
                     for r in _tag_refs(table.get("tags", []), f"{w}.{code}.tags"))
        ids = tuple(int(i) for i in table.get("content_descriptor_ids", [])) if adult else ()
        rule = ExclusionRule(code, _OLD_LABELS[code], tags, _name_only(table, f"{w}.{code}"), ids, adult)
        if rule.tags or rule.name_only or adult:
            rules.append(rule)
    return tuple(rules)


def _exclusions(t: dict[str, Any], source: str = "steam") -> ExclusionConfig:
    w = "exclusions"
    if source == "import" and "global_rank_limit" not in t:
        t = {**t, "global_rank_limit": NO_RANK_LIMIT}
    limit = _req(t, "global_rank_limit", int, w)
    if not (source == "import" and limit == NO_RANK_LIMIT) and not 1 <= limit <= 20:
        raise ConfigError(f"{w}.global_rank_limit: must be between 1 and 20, got {limit}")
    old = [k for k in (*_OLD_RULE_TABLES, "per_tag_rank_limit") if k in t]
    if isinstance(t.get("content_flags"), dict):
        old.append("content_flags")
    if old and ("rule" in t or "content_flag" in t):
        raise ConfigError(f"{w}: mixes the old shape ({old[0]}) with [[rule]] / [[content_flag]] entries")
    if old:
        rules = _old_rules(t, w)
        flags = tuple(_content_flag(code, table, f"{w}.content_flags.{code}")
                      for code, table in t.get("content_flags", {}).items())
    else:
        items = t.get("rule", [])
        if not isinstance(items, list):
            raise ConfigError(f"{w}.rule: expected [[rule]] entries")
        rules = tuple(_named_rule(item, f"{w}.rule[{i}]") for i, item in enumerate(items))
        raw_flags = t.get("content_flag", [])
        if not isinstance(raw_flags, list):
            raise ConfigError(f"{w}.content_flag: expected [[content_flag]] entries")
        flags = tuple(_content_flag(item.get("name") if isinstance(item, dict) else None, item,
                                    f"{w}.content_flag[{i}]") for i, item in enumerate(raw_flags))
    names = [r.name for r in rules]
    for i, name in enumerate(names):
        if name in FIXED_RULES:
            raise ConfigError(f"{w}.rule[{i}].name: '{name}' is a fixed rule and cannot be a named rule")
        if names.index(name) != i:
            raise ConfigError(f"{w}.rule[{i}].name: duplicate rule name '{name}'")
    flag_names = [f.name for f in flags]
    for i, name in enumerate(flag_names):
        if flag_names.index(name) != i:
            raise ConfigError(f"{w}.content_flag[{i}].name: duplicate Content Flag '{name}'")
    return ExclusionConfig(
        allowed_app_types=tuple(_req(t, "allowed_app_types", list, w)),
        global_rank_limit=limit,
        rules=rules,
        content_flags=flags,
    )


def _genre_kind(t: dict[str, Any]) -> dict[int, str]:
    kinds: dict[int, str] = {}
    for key, kind in t.get("genre_kind", {}).items():
        if kind not in ("genre", "business", "software"):
            raise ConfigError(f"genres.genre_kind.{key}: kind must be genre, business or software")
        kinds[int(key)] = kind
    return kinds


MIN_LIST_SIZE = 10
STEAM_MAX_TAG_DEPTH = 20  # a Steam store page displays at most 20 tags


def _tag_depth(t: dict[str, Any], source: str = "steam") -> int | str:
    """Tag Depth: 2-20 or "all" for a Steam Build ("all" is the default and the same as 20); for an Import Build
    2 or more (the Build checks it against the longest list), or "all"."""
    value = t.get("tag_depth", "all")
    if value == "all":
        return "all"
    if isinstance(value, bool) or not isinstance(value, int):
        raise ConfigError(f"datasets.tag_depth: must be an integer or the string \"all\", got {value!r}")
    if value < 2:
        raise ConfigError(f"datasets.tag_depth: must be at least 2 (or \"all\"), got {value}")
    if source == "steam" and value > STEAM_MAX_TAG_DEPTH:
        raise ConfigError(f"datasets.tag_depth: a Steam store page shows at most {STEAM_MAX_TAG_DEPTH} tags, "
                          f"got {value}; use \"all\"")
    return value


def _datasets(t: dict[str, Any]) -> tuple[DatasetDef, ...]:
    items = t.get("dataset", [])
    if not items:
        raise ConfigError("datasets: no [[dataset]] entries")
    out = []
    for i, item in enumerate(items):
        where = f"datasets.dataset[{i}]"
        defining = item.get("defining_tag")
        key = _code(_req(item, "key", str, where), f"{where}.key")
        label = _req(item, "label", str, where)
        if not label.strip():
            raise ConfigError(f"{where}.label: a label is required")
        size = item.get("list_size", 100)
        if isinstance(size, bool) or not isinstance(size, int) or size < MIN_LIST_SIZE:
            raise ConfigError(f"{where}.list_size: must be an integer of at least {MIN_LIST_SIZE}, got {size!r}")
        out.append(DatasetDef(key=key, label=label,
                              defining_tag=_tag_refs([defining], f"{where}.defining_tag")[0] if defining else None,
                              list_size=size))
    keys = [d.key for d in out]
    if len(set(keys)) != len(keys):
        raise ConfigError(f"datasets: duplicate dataset keys {keys}")
    plain = [d.key for d in out if d.defining_tag is None]
    if len(plain) != 1 or plain[0] != "overall":
        raise ConfigError("datasets: exactly one dataset must have no defining tag, and its key must be 'overall'"
                          f" (found {plain or 'none'})")
    if out[0].key != "overall":
        raise ConfigError("datasets: 'overall' must be listed first")
    tag_ids = [d.defining_tag.id for d in out if d.defining_tag]
    if len(set(tag_ids)) != len(tag_ids):
        raise ConfigError("datasets: a defining tag may be used by one dataset only")
    return tuple(out)


def _network(t: dict[str, Any]) -> NetworkDefaults:
    w = "network"
    weight = _req(t, "clustering_weight", str, w)
    if weight not in CLUSTERING_WEIGHTS:
        raise ConfigError(f"{w}.clustering_weight: must be one of {CLUSTERING_WEIGHTS}")
    algorithm = _req(t, "algorithm", str, w)
    if algorithm not in ALGORITHMS:
        raise ConfigError(f"{w}.algorithm: must be one of {ALGORITHMS}")
    resolution = _req(t, "resolution", float, w)
    if resolution <= 0:
        raise ConfigError(f"{w}.resolution: must be > 0")
    defaults = NetworkDefaults(
        min_games_per_tag=_req(t, "min_games_per_tag", int, w),
        min_shared_games=_req(t, "min_shared_games", int, w),
        min_months=_req(t, "min_months", int, w),
        hide_genre_tags=_req(t, "hide_genre_tags", bool, w),
        hide_defining_tag=_req(t, "hide_defining_tag", bool, w),
        clustering_weight=weight,
        algorithm=algorithm,
        resolution=resolution,
        seed=_req(t, "seed", int, w),
        null_replicates=_req(t, "null_replicates", int, w),
        noise_seeds=_req(t, "noise_seeds", int, w),
        resolution_sweep=tuple(float(g) for g in _req(t, "resolution_sweep", list, w)),
        parameter_selection=_parameter_selection(t.get("parameter_selection", PARAMETER_SELECTION_DEFAULTS)),
    )
    _at_least(defaults.min_games_per_tag, 1, f"{w}.min_games_per_tag")
    _at_least(defaults.min_shared_games, 1, f"{w}.min_shared_games")
    _at_least(defaults.min_months, 0, f"{w}.min_months")
    _at_least(defaults.null_replicates, 2, f"{w}.null_replicates")
    _at_least(defaults.noise_seeds, 2, f"{w}.noise_seeds")
    return defaults


def _between(value: int | float, lo: int | float, hi: int | float, where: str) -> None:
    if not lo <= value <= hi:
        raise ConfigError(f"{where}: must be between {lo} and {hi}, got {value}")


def _int_range(t: dict[str, Any], key: str, where: str) -> tuple[int, int]:
    value = _req(t, key, list, where)
    if len(value) != 2 or not all(isinstance(x, int) and not isinstance(x, bool) for x in value):
        raise ConfigError(f"{where}.{key}: expected [low, high] integers, got {value}")
    lo, hi = value
    if lo < 1 or lo > hi:
        raise ConfigError(f"{where}.{key}: expected 1 <= low <= high, got {value}")
    return lo, hi


def _parameter_selection(t: dict[str, Any]) -> ParameterSelectionDefaults:
    w = "network.parameter_selection"
    weight = _req(t, "clustering_weight", str, w)
    if weight not in CLUSTERING_WEIGHTS:
        raise ConfigError(f"{w}.clustering_weight: must be one of {CLUSTERING_WEIGHTS}")
    ps = ParameterSelectionDefaults(
        clustering_weight=weight,
        min_months=_req(t, "min_months", int, w),
        min_multi_tag_clusters=_req(t, "min_multi_tag_clusters", int, w),
        g_range=_int_range(t, "g_range", w),
        s_range=_int_range(t, "s_range", w),
        gamma_step=_req(t, "gamma_step", float, w),
        scan_seeds=_req(t, "scan_seeds", int, w),
        null_replicates=_req(t, "null_replicates", int, w),
        subsamples=_req(t, "subsamples", int, w),
        workers=_req(t, "workers", int, w),
        tolerance=_req(t, "tolerance", float, w),
        min_retention=_req(t, "min_retention", float, w),
        max_isolated_share=_req(t, "max_isolated_share", float, w),
        min_lcc_share=_req(t, "min_lcc_share", float, w),
        min_comparable_neighbours=_req(t, "min_comparable_neighbours", int, w),
        max_multi_tag_clusters=_req(t, "max_multi_tag_clusters", int, w) or None,
    )
    _between(ps.min_months, 0, 60, f"{w}.min_months")
    _between(ps.min_multi_tag_clusters, 1, 10, f"{w}.min_multi_tag_clusters")
    if ps.gamma_step <= 0:
        raise ConfigError(f"{w}.gamma_step: must be > 0")
    if abs(round(ps.gamma_step * 100) - ps.gamma_step * 100) > 1e-9:  # champ.scan_gammas rounds γ to 2 decimals
        raise ConfigError(f"{w}.gamma_step: must be a whole multiple of 0.01, got {ps.gamma_step}")
    for key in ("scan_seeds", "null_replicates", "subsamples"):
        _at_least(getattr(ps, key), 1, f"{w}.{key}")
    _at_least(ps.workers, 0, f"{w}.workers")
    for key in ("tolerance", "min_retention", "max_isolated_share", "min_lcc_share"):
        _between(getattr(ps, key), 0, 1, f"{w}.{key}")
    _between(ps.min_comparable_neighbours, 0, 4, f"{w}.min_comparable_neighbours")
    if ps.s_range[0] > ps.g_range[1]:
        raise ConfigError(f"{w}: the Parameter Grid has no (g, s) pairs because s_range starts at {ps.s_range[0]}, "
                          f"above the largest g, {ps.g_range[1]}")
    if ps.max_multi_tag_clusters is not None and ps.max_multi_tag_clusters < ps.min_multi_tag_clusters:
        raise ConfigError(f"{w}.max_multi_tag_clusters: must be 0 (off) or >= min_multi_tag_clusters "
                          f"({ps.min_multi_tag_clusters}), got {ps.max_multi_tag_clusters}")
    return ps


def _analysis(t: dict[str, Any]) -> AnalysisConfig:
    w = "analysis"
    cfg = AnalysisConfig(
        max_itemset_size=_req(t, "max_itemset_size", int, w),
        min_support=_req(t, "min_support", int, w),
        causal_words=tuple(_req(t, "causal_words", list, w)),
        release_month_check=_req(t, "release_month_check", int, w),
    )
    _at_least(cfg.max_itemset_size, 2, f"{w}.max_itemset_size")
    _at_least(cfg.min_support, 1, f"{w}.min_support")
    return cfg

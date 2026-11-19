"""The Parameter Selection mode's components: layout variant A, "Three panes", shaped like the Workbench.

Left, the Controls column (Run, Pair Constraints, Selection settings); in the middle the dataset strip, the metric
picker, the g × s heatmap, "Why this pair" and the validation card; on the right the Pair Inspector. At medium and
narrow widths the Workbench's forms apply: the Controls become a pill bar, and the Pair Inspector floats from a
heatmap pick until its ×.
Everything here is a pure function of the Build, the cache and the mode's stores; `callbacks.py` wires it. The
static layout registers its words for the relabel callback (`relabel.Labels`); everything `ps_render` sends takes
the Interface Language's translator `tx`.
"""

from __future__ import annotations

import dataclasses
import platform
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import plotly.graph_objects as go
from dash import dcc, html

from steamstudy.app import help as H
from steamstudy.app import ps_cache, ps_run
from steamstudy.app.ps_export import constraints_for, tag_names
from steamstudy.app.loader import BuildContext
from steamstudy.app.relabel import Labels, PerBuild, msg
from steamstudy.app import panels as P
from steamstudy.network import selection as SEL
from steamstudy.network import selection_text as T
from steamstudy.network import validation as V
from steamstudy.network.cluster import label_clusters
from steamstudy.i18n import Text
from steamstudy.versions import APP_LIBRARIES, software_versions

METRICS = [("neighbour_agreement", msg("Neighbour Agreement")), ("retention", msg("Information Retention")),
           ("isolated_share", msg("isolated share")), ("multi_tag_clusters", msg("Multi-Tag Clusters")),
           ("seed_noise", msg("Seed-Noise Floor")), ("q", "Q")]
LETTERS = {"no_selected_partition": "P", "no_neighbour_agreement": "A", "too_few_comparable_neighbours": "N",
           "retention_below_min": "R", "isolated_share_above_max": "I", "lcc_share_below_min": "L",
           "too_many_clusters": "K"}
# A reason letter's words (English, shown through `tx`: `reason_words`).
REASON_WORDS = {"no_selected_partition": msg("no Selected Partition"),
                "no_neighbour_agreement": msg("no Neighbour Agreement"),
                "too_few_comparable_neighbours": msg("too few comparable neighbours"),
                "retention_below_min": msg("Information Retention below the minimum"),
                "isolated_share_above_max": msg("isolated share above the maximum"),
                "lcc_share_below_min": msg("LCC share below the minimum"),
                "too_many_clusters": msg("too many Multi-Tag Clusters")}
CONSTRAINT_FIELDS = [("min_retention", msg("Minimum Information Retention"), 0.0, 1.0, 0.01),
                     ("max_isolated_share", msg("Maximum isolated share"), 0.0, 1.0, 0.01),
                     ("min_lcc_share", msg("Minimum LCC share"), 0.0, 1.0, 0.01),
                     ("min_comparable_neighbours", msg("Minimum comparable neighbours (different graph)"), 0, 4, 1),
                     ("max_multi_tag_clusters", msg("Maximum Multi-Tag Clusters (empty = off)"), 1, None, 1),
                     ("tolerance", msg("Tolerance (near-best)"), 0.0, 1.0, 0.01)]
CONSTRAINT_HELP = {"tolerance": "selection.constraint.tolerance"} | {
    name: f"selection.constraint.{name}" for name, *_ in CONSTRAINT_FIELDS if name != "tolerance"}
# A constraint's pill in the bar under the dataset strip names it short; its popover keeps the full label.
CONSTRAINT_PILLS = {"min_retention": msg("Retention ≥"), "max_isolated_share": msg("Isolated share ≤"),
                    "min_lcc_share": msg("LCC share ≥"), "min_comparable_neighbours": msg("Comparable neighbours ≥"),
                    "max_multi_tag_clusters": msg("Multi-Tag Clusters ≤"), "tolerance": msg("Tolerance")}
# The bar's two rows: first the constraints most often changed, then the rest.
CONSTRAINT_ROWS = (("min_retention", "max_isolated_share", "tolerance"),
                   ("min_lcc_share", "min_comparable_neighbours", "max_multi_tag_clusters"))


def reason_words(tx: Text) -> dict[str, str]:
    return {code: tx(words) for code, words in REASON_WORDS.items()}


# ----------------------------------------------------------------------------- stores <-> objects


def settings_data(settings: SEL.SelectionSettings) -> dict[str, Any]:
    return json_ready(dataclasses.asdict(settings))


def settings_of(data: Mapping[str, Any]) -> SEL.SelectionSettings:
    fields = {f.name for f in dataclasses.fields(SEL.SelectionSettings)}
    values: dict[str, Any] = {k: tuple(v) if isinstance(v, list) else v for k, v in data.items() if k in fields}
    return SEL.SelectionSettings(**values)


def constraints_data(c: SEL.Constraints) -> dict[str, Any]:
    return dataclasses.asdict(c)


def constraints_of(data: Mapping[str, Any]) -> SEL.Constraints:
    return SEL.Constraints(**{f.name: data[f.name] for f in dataclasses.fields(SEL.Constraints)})


active_constraints = constraints_for


def json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: json_ready(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_ready(v) for v in value]
    return value


def defaults_of(ctx: BuildContext) -> tuple[SEL.SelectionSettings, SEL.Constraints]:
    return (SEL.load_selection_settings(ctx.network, (t.id for t in ctx.genre_tags), ctx.build_id),
            SEL.default_constraints(ctx.network))


# ----------------------------------------------------------------------------- what the cache holds


@dataclass
class DatasetView:
    dataset: str
    label: str
    status: str  # not_run, partial, complete
    done: int
    total: int
    pairs: list[tuple[int, int]]
    pair_hash: dict[tuple[int, int], str] = field(default_factory=dict)
    results: dict[str, SEL.GraphResult] = field(default_factory=dict)
    links: list[SEL.Link] = field(default_factory=list)
    na: dict[tuple[int, int], SEL.NeighbourAgreement] = field(default_factory=dict)
    choice: SEL.Choice | None = None  # under the dataset's active constraints
    default_choice: SEL.Choice | None = None  # under the default constraints (the validated pair)
    computed_with: dict[str, Any] | None = None

    def result(self, pair: tuple[int, int]) -> SEL.GraphResult | None:
        h = self.pair_hash.get(pair)
        return None if h is None else self.results.get(h)

    @property
    def star(self) -> tuple[int, int] | None:
        return self.choice.chosen if self.choice else None


_LOADED: dict[tuple[str, int, float], dict[str, SEL.GraphResult]] = {}


def _results(cache_root: Path, key: dict[str, Any], hashes: set[str]) -> dict[str, SEL.GraphResult]:
    """Graph files, read once per (grid, file count, manifest time) in this process."""
    folder = ps_cache.grid_dir(cache_root, key)
    manifest = folder / "manifest.json"
    stamp = (str(folder), len(hashes), manifest.stat().st_mtime if manifest.is_file() else 0.0)
    if stamp not in _LOADED:
        if len(_LOADED) > 32:
            _LOADED.clear()
        _LOADED[stamp] = ps_cache.load_results(cache_root, key, hashes)
    return _LOADED[stamp]


def partial_agreement(pairs: list[tuple[int, int]], pair_hash: dict[tuple[int, int], str],
                      results: dict[str, SEL.GraphResult]) -> dict[tuple[int, int], SEL.NeighbourAgreement]:
    """Neighbour Agreement of the pairs whose every in-grid neighbour is computed (an unfinished grid)."""
    have = {p for p in pairs if pair_hash.get(p) in results}
    grid = SEL.Grid("", {p: pair_hash[p] for p in have}, results)
    links = SEL.neighbour_links(grid)
    na = SEL.neighbour_agreement(grid, links)
    inside = set(pairs)
    out = {}
    for (g, s), value in na.items():
        neighbours = [(g + dg, s + ds) for dg, ds in SEL.DIRECTIONS.values() if (g + dg, s + ds) in inside]
        if all(q in have for q in neighbours):
            out[(g, s)] = value
    return out


def dataset_view(ctx: BuildContext, settings: SEL.SelectionSettings, dataset: str, constraints: SEL.Constraints,
                 defaults: SEL.Constraints, cache_root: Path | None = None) -> DatasetView:
    cache_root = Path(cache_root or ctx.app_cache)
    pairs = settings.pairs()
    key = settings.grid_key(dataset, ctx.context(dataset))
    state = ps_cache.grid_state(cache_root, key, len(pairs))
    view = DatasetView(dataset, ctx.dataset(dataset).label, state.status if state.done else "not_run", state.done,
                       len(pairs), pairs, state.pair_hash, computed_with=state.computed_with)
    if not state.done:
        return view
    view.results = _results(cache_root, key, state.graph_hashes)
    if state.status != "complete":
        view.na = partial_agreement(pairs, state.pair_hash, view.results)
        return view
    manifest = state.manifest or {}
    view.links = [SEL.Link(**{**x, "p": tuple(x["p"]), "q": tuple(x["q"])}) for x in manifest["links"]]
    view.na = {tuple(int(v) for v in k.split(",")): SEL.NeighbourAgreement(**v)  # type: ignore[misc]
               for k, v in manifest["neighbour_agreement"].items()}
    grid = SEL.Grid(dataset, state.pair_hash, view.results)
    view.choice = SEL.choose(grid, view.na, constraints)
    view.default_choice = view.choice if constraints == defaults else SEL.choose(grid, view.na, defaults)
    return view


def is_validated(ctx: BuildContext, settings: SEL.SelectionSettings, dataset: str, pair: tuple[int, int] | None,
                 cache_root: Path | None = None) -> bool:
    if pair is None:
        return False
    key = settings.validation_key(dataset, ctx.context(dataset), *pair)
    return ps_cache.validation_path(Path(cache_root or ctx.app_cache), key).is_file()


def validation_of(ctx: BuildContext, settings: SEL.SelectionSettings, dataset: str, pair: tuple[int, int] | None,
                  observed: SEL.GraphResult | None, cache_root: Path | None = None) -> dict[str, Any] | None:
    """The pair's validation file with its `summary` derived from the records (never stored); `observed` is the
    pair's GraphResult. None when the pair is not validated under the current records version."""
    if pair is None or observed is None or observed.selected is None:
        return None
    key = settings.validation_key(dataset, ctx.context(dataset), *pair)
    validation = ps_cache.read_validation(Path(cache_root or ctx.app_cache), key)
    if validation is None:
        return None
    return {**validation, "summary": V.summary_from_records(observed, validation)}


# ----------------------------------------------------------------------------- small helpers


def _help(key: str, tx: Text) -> html.Span:
    return html.Span("?", className="ps-q term", tabIndex="0", **H.attrs(key, tx))


def _static_help(L: Labels, key: str) -> html.Span:
    """A `?` in the mode's static layout: its tooltip is relabelled on a language switch."""
    return html.Span("?", className="ps-q term", tabIndex="0", **L.help(key))


def _term(text_: str, key: str, tx: Text) -> html.Span:
    return html.Span(text_, className="term", tabIndex="0", **H.attrs(key, tx))


def provenance(computed_with: Mapping[str, Any] | None, *, tx: Text) -> tuple[str, str | None]:
    """The quiet provenance line when results were computed elsewhere, and the banner text for a library mismatch."""
    if not computed_with:
        return "", None
    versions = computed_with.get("versions", {})
    now = software_versions()
    mismatched = [(lib, versions[lib], now[lib]) for lib in APP_LIBRARIES
                  if lib in versions and lib in now and versions[lib] != now[lib]]
    if mismatched:
        names = ", ".join(tx("{lib} {old} (installed {new})", lib=lib, old=old, new=new) for lib, old, new in mismatched)
        return "", tx("These Parameter Selection results were computed with {names}; the numbers may differ here. "
                      "Clear app cache and Run to recompute here.", names=names)
    same = (versions.get("python") == now.get("python") and computed_with.get("system") == platform.system()
            and computed_with.get("machine") == platform.machine())
    if same:
        return "", None
    day = str(computed_with.get("utc", ""))[:10]
    return tx("Computed when this bundle was made: Python {python}, {system} {machine}, {day}",
              python=versions.get("python", "?"), system=computed_with.get("system", "?"),
              machine=computed_with.get("machine", "?"), day=day), None


# ----------------------------------------------------------------------------- Controls column


def _constraint_pills(L: Labels, defaults: SEL.Constraints) -> dict[str, html.Div]:
    """One pill per Pair Constraint: its short name and staged value; the popover holds its field."""
    pills = {}
    for name, label, lo, hi, step in CONSTRAINT_FIELDS:
        default = getattr(defaults, name)
        kw: dict[str, Any] = {"min": lo, "step": step}
        if hi is not None:
            kw["max"] = hi
        field = html.Div([
            html.Label([L.term(label, CONSTRAINT_HELP[name])], className="l", htmlFor=f"ps-c-{name}"),
            dcc.Input(id=f"ps-c-{name}", type="number", value=default, debounce=True, **kw),
            L.span(_default_text(default), className="mute small"),
            html.Span("", id=f"ps-c-{name}-changed", className="ps-changed small"),
        ], className="ps-field")
        pills[name] = _pill(L, f"c-{name}", CONSTRAINT_PILLS[name], CONSTRAINT_HELP[name], field)
    return pills


def constraint_value(value: Any, name: str, *, tx: Text) -> str:
    """A staged Pair Constraint as its pill shows it: the Multi-Tag Cluster cap is off when empty."""
    if name == "max_multi_tag_clusters" and value in (None, "", 0):
        return tx("off")
    return "–" if value in (None, "") else tx.figure(str(value))


def constraints_bar(L: Labels, constraints: SEL.Constraints) -> html.Div:
    """The Pair Constraints under the dataset strip: a pill each in two rows (`CONSTRAINT_ROWS`), then a row with
    where they apply, Confirm, Reset and the constraints label."""
    pills = _constraint_pills(L, constraints)
    return html.Div([
        html.Span([L.span(msg("Pair Constraints")), " ", _static_help(L, "selection.constraints"),
                   P.collapse_button(L, "ps", "constraints")], className="ps-cbar-h"),
        *[html.Div([pills[name] for name in row], className="ps-cbar-row") for row in CONSTRAINT_ROWS],
        html.Div([
            dcc.RadioItems(id="ps-c-scope", options=L.options("ps-c-scope", [("all", msg("All five datasets")),
                                                                             ("dataset", msg("this dataset only"))]),
                           value="all", className="seg", inline=True),
            html.Button(L.prop("ps-c-confirm", "children", msg("Confirm")), id="ps-c-confirm",
                        className="btn primary", disabled=True),
            html.Button(L.prop("ps-c-reset", "children", msg("Reset to defaults")), id="ps-c-reset", className="btn"),
            html.Span("", id="ps-c-unconfirmed", className="ps-changed small"),
            html.Span(id="ps-c-label", className="mute small"),
        ], className="ps-cbar-row ps-cbar-acts"),
    ], id="ps-cbar", className="ps-cbar")


def _default_text(default: Any) -> Callable[[Text], str]:
    """A Pair Constraint's default beside its field, as a function of the translator."""
    return lambda tx: tx("default {value}", value=tx("off") if default is None else tx.figure(str(default)))


def _pill(L: Labels, pill: str, label: str, key: str, section: html.Div) -> html.Div:
    """One Controls section: inline in the column, or a pill with a popover in the pill bar (medium and narrow, as
    in the Workbench); or a Pair Constraint's pill in the bar under the strip, at every form. The pill's value is
    filled by a callback (`ps_render`, `ps_constraint_pills`)."""
    btn_id = f"ps-pill-btn-{pill}"
    attrs: dict[str, Any] = {"data-pill": pill, "data-tip": L.prop(btn_id, "data-tip", lambda tx: H.tip(key, tx))}
    return html.Div([
        html.Button([L.span(label), " ", html.B("", id=f"ps-pill-{pill}", className="num")], id=btn_id,
                    className="pill-btn", **attrs),
        html.Div(section, className="pill-pop"),
    ], className="ctl-item")


def pill_values(views: list[DatasetView], running: bool, settings_custom: bool, *, tx: Text) -> tuple[str, str]:
    """The Controls pills' values: Run's state over the datasets, then default or custom for the settings."""
    done = sum(v.status == "complete" for v in views)
    run = (tx("running") if running else tx("{n} of {total} done", n=done, total=len(views)) if done
           else tx("not run"))
    return run, tx("custom") if settings_custom else tx("default")


def inspector_form(open_: bool) -> str:
    """The Pair Inspector's classes: docked at wide; at medium and narrow a floating card while open."""
    return "inspector docked ps-inspector" + (" has-sel" if open_ else "")


def run_one_label(tx: Text, ctx: BuildContext) -> str:
    return tx("Run {dataset}", dataset=ctx.datasets[0].label)


def defining_options(tx: Text, ctx: BuildContext) -> list[dict[str, Any]]:
    defining = [d.defining_tag.name for d in ctx.datasets if d.defining_tag]
    return [{"label": tx("hide each dataset's defining tag ({tags})", tags=", ".join(defining))
             if defining else tx("hide each dataset's defining tag"), "value": 1}]


def controls(L: Labels, ctx: BuildContext, defaults: SEL.SelectionSettings) -> html.Div:
    first = ctx.datasets[0].key
    field = ctx.read(first).filter_field
    run = html.Div([
        html.H4([L.span(msg("Run")), " ", _static_help(L, "selection.run")], className="ctl-h"),
        html.Div([html.Button(L.prop("ps-run-all", "children", msg("Run all datasets")), id="ps-run-all",
                              className="btn primary"),
                  html.Button(L.prop("ps-run-one", "children", PerBuild(run_one_label)),
                              id="ps-run-one", className="btn"),
                  html.Button(L.prop("ps-cancel", "children", msg("Cancel")), id="ps-cancel", className="btn",
                              disabled=True)],
                 className="row-inline"),
        html.Button(id="ps-continue", className="btn", style={"display": "none"}),
        html.Div(id="ps-rows", className="ps-rows"),
        html.Div(id="ps-cache-line", className="mute small"),
        html.Div(id="ps-provenance", className="mute small"),
        html.Div(id="ps-banner", className="warning", style={"display": "none"}),
        html.Div([html.Button(L.prop("ps-export", "children", msg("Export tables")), id="ps-export", className="btn",
                              disabled=True),
                  _static_help(L, "selection.export")], className="row-inline"),
    ], className="ctl-section")
    genre =[{"label": t.name, "value": t.id} for t in ctx.genre_tags]
    names = tag_names(ctx)
    settings = html.Div([
        html.H4([L.span(msg("Selection settings")), " ", _static_help(L, "selection.settings")], className="ctl-h"),
        html.Label([L.term(msg("Hidden Genre Tags"), "selection.setting.hidden")], className="l"),
        dcc.Checklist(id="ps-s-genre", options=genre, value=list(defaults.genre_hidden), inline=True,
                      className="chips"),
        dcc.Checklist(id="ps-s-defining", options=L.prop("ps-s-defining", "options", PerBuild(defining_options)),
                      value=[1] if defaults.hide_defining_tag else [], className="check"),
        html.Label([L.term(msg("Removed tags"), "selection.setting.removed")], className="l"),
        dcc.Dropdown(id="ps-s-removed", options=[{"label": n, "value": t} for t, n in sorted(names.items(),
                                                                                            key=lambda x: x[1])],
                     value=list(defaults.removed_tag_ids), multi=True,
                     placeholder=L.prop("ps-s-removed", "placeholder", msg("no removed tags"))),
        *([html.Label([L.term(msg("Minimum Months Filter") if field.label == "Minimum Months Filter" else field.label,
                                   "selection.setting.min_months")], className="l"),
           dcc.Slider(id="ps-s-min-months", min=int(field.minimum), max=int(field.maximum), step=1,
                      value=defaults.min_months, marks={int(field.minimum): str(int(field.minimum)),
                                                        int(field.maximum): str(int(field.maximum))},
                      tooltip={"placement": "bottom"})] if field else
          # no filter field: kept for the callbacks, hidden, so every item is kept
          [html.Div(dcc.Slider(id="ps-s-min-months", min=0, max=1, step=1, value=defaults.min_months),
                    style={"display": "none"})]),
        html.Label([L.term(msg("Clustering weight"), "selection.setting.weight")], className="l"),
        dcc.RadioItems(id="ps-s-weight", options=L.options("ps-s-weight", [("lift", msg("Lift")),
                                                                           ("shared_games", msg("Shared games"))]),
                       value=defaults.clustering_weight, className="seg", inline=True),
        html.Label([L.term(msg("Minimum Multi-Tag Clusters"), "selection.setting.min_multi_tag_clusters")],
                   className="l"),
        dcc.Input(id="ps-s-min-multi", type="number", min=1, max=10, step=1, value=defaults.min_multi_tag_clusters),
        html.Div([html.Button(L.prop("ps-s-use", "children", msg("Use these settings")), id="ps-s-use",
                              className="btn primary"),
                  html.Button(L.prop("ps-s-reset", "children", msg("Reset to defaults")), id="ps-s-reset",
                              className="btn"),
                  html.Button(L.prop("ps-s-copy", "children", msg("Copy from Workbench")), id="ps-s-copy",
                              className="btn")], className="stack"),
        html.Div([L.span(line, className="ps-line") for line in read_only(defaults)],
                 className="mute small ps-readonly"),
        html.Div(id="ps-s-label", className="mute small"),
    ], className="ctl-section")
    return html.Div([html.Div([html.B(L.span(msg("Parameter Selection"))), P.collapse_button(L, "ps", "controls")],
                              className="ctl-title"),
                     _pill(L, "run", msg("Run"), "selection.run", run),
                     _pill(L, "settings", msg("Selection settings"), "selection.settings", settings)],
                    id="ps-controls", className="controls ps-controls")


def read_only(s: SEL.SelectionSettings) -> list[Callable[[Text], str]]:
    """The settings the mode never changes, one line each, as functions of the translator."""
    return [lambda tx: tx(T.LEIDEN_ONLY) + ".",
            lambda tx: tx("Parameter Grid: g {g_lo}–{g_hi}, s {s_lo}–{s_hi}, s ≤ g ({n} pairs)", g_lo=s.g_range[0],
                          g_hi=s.g_range[1], s_lo=s.s_range[0], s_hi=s.s_range[1], n=len(s.pairs())),
            lambda tx: tx("γ from 0 to γ_max(n_e) in steps of {step}; {seeds} scan seeds",
                          step=tx.fixed(s.gamma_step, "g"), seeds=s.scan_seeds),
            lambda tx: tx("Null Comparison R = {r}; Subsample Stability S = {s}", r=s.replicates, s=s.subsamples),
            lambda tx: tx("Workbench seed priority: {order}",
                          order=tx(SEED_PRIORITY_LABELS[s.workbench_seed_priority]))]


# The Build's Workbench Seed Priority, as the Fixed settings name it.
SEED_PRIORITY_LABELS = {"closest_gamma": msg("Closest γ to the midpoint"), "main_seed": msg("Prefer the main seed")}


def run_rows(views: list[DatasetView], progress: Mapping[str, Any] | None, validated: Mapping[str, bool], *,
             tx: Text) -> list[Any]:
    rows = []
    for v in views:
        live = progress if progress and progress.get("dataset") == v.dataset else None
        if live and live["phase"] == "validation":
            text_ = tx("validation {done} of {total} replicates", done=live["done"], total=live["total"])
            value, top = live["done"], live["total"]
        elif live:
            text_, value, top = (tx("grid {done} of {total} pairs", done=live["done"], total=live["total"]),
                                 live["done"], live["total"])
        elif v.status == "complete":
            text_ = tx("grid done, validated") if validated.get(v.dataset) else tx("grid done, not validated")
            value, top = v.total, v.total
        elif v.status == "partial":
            text_, value, top = tx("grid {done} of {total} pairs", done=v.done, total=v.total), v.done, v.total
        else:
            text_, value, top = tx("not run"), 0, v.total
        rows.append(html.Div([html.Span(v.label, className="ps-row-name"), html.Span(text_, className="mute small"),
                              html.Progress(value=str(value), max=str(max(top, 1)))], className="ps-row"))
    return rows


# ----------------------------------------------------------------------------- dataset strip and loading panel


def strip(views: list[DatasetView], current: str, custom: Mapping[str, str], *, tx: Text) -> list[Any]:
    buttons = []
    for v in views:
        if v.status == "complete" and v.choice is not None:
            if v.star is None:
                text_ = tx("no qualifying pair")
            else:
                g, s = v.star
                text_ = tx("★ {g}·{s} NA {na}", g=g, s=s, na=tx.num(v.na[v.star].value))
        elif v.status == "partial":
            text_ = tx("grid {done} of {total}", done=v.done, total=v.total)
        else:
            text_ = tx("not run")
        marker = custom.get(v.dataset)
        buttons.append(html.Button([html.B(v.label), html.Span(text_, className="ps-strip-v"),
                                    *([html.Span(tx("custom"), className="ps-custom", title=marker)] if marker else [])],
                                   id={"type": "ps-strip", "dataset": v.dataset},
                                   className="ps-strip-btn" + (" on" if v.dataset == current else "")))
    return [html.Div(buttons, className="ps-strip-row"), _help("selection.dataset_strip", tx)]


def loading_panel(progress: Mapping[str, Any] | None, views: list[DatasetView], settings: SEL.SelectionSettings,
                  reason: str, *, tx: Text) -> list[Any]:
    lengths = [r.scan_length for v in views for r in v.results.values() if r.scan_length]
    scan = f"{min(lengths)}–{max(lengths)}" if lengths else tx("up to several hundred")
    what = tx("Searching {pairs} Threshold Pairs × {scan} resolutions × {seeds} seeds for each dataset, then checking "
              "the chosen pair against {replicates} shuffled networks and {subsamples} subsamples.",
              pairs=len(settings.pairs()), scan=scan, seeds=settings.scan_seeds, replicates=settings.replicates,
              subsamples=settings.subsamples)
    where, eta = tx("Starting…"), tx("estimating…")
    if progress:
        where_values = {"index": progress["dataset_index"], "n": progress["n_datasets"], "dataset": progress["dataset"],
                        "done": progress["done"], "total": progress["total"]}
        where = (tx("Dataset {index} of {n} ({dataset}): grid {done} of {total} pairs.", **where_values)
                 if progress["phase"] == "grid" else
                 tx("Dataset {index} of {n} ({dataset}): validation {done} of {total} replicates.", **where_values))
        eta = f"{ps_run.eta_text(progress, tx)} · {ps_run.elapsed_text(progress['elapsed'], tx)}"
    once = tx("A one-off: results are cached. Cancel keeps the finished pairs and Continue resumes; a cancelled "
              "validation restarts from the beginning.")
    body = [html.B(tx("Computing Parameter Selection")), html.Div(what), html.Div(reason, className="mute"),
            html.Div(where), html.Div(once, className="mute small"), html.Div(eta, className="ps-eta"),
            html.A(tx("How Automatic Parameter Selection works"), href="#", className="term",
                   **H.attrs("selection.run", tx))]
    return [html.Div(body, className="ps-loading", role="status")]


# ----------------------------------------------------------------------------- heatmap


def metric_value(result: SEL.GraphResult | None, na: SEL.NeighbourAgreement | None, metric: str) -> float | None:
    if result is None:
        return None
    if metric == "neighbour_agreement":
        return None if na is None else na.value
    if metric == "seed_noise":
        return None if result.seed_noise is None else result.seed_noise["floor"]
    return {"retention": result.retention, "isolated_share": result.isolated_share,
            "multi_tag_clusters": result.n_multi, "q": result.modularity}[metric]


def plotly_separators(tx: Text) -> str:
    """Plotly's decimal and thousands marks: the language's decimal mark, and no thousands separator in Bulgarian
    (English keeps Plotly's own default)."""
    return ".," if tx.decimal == "." else tx.decimal


def heatmap(view: DatasetView, metric: str, inspected: tuple[int, int] | None, *, tx: Text) -> go.Figure:
    gs = sorted({g for g, _ in view.pairs})
    ss = sorted({s for _, s in view.pairs})
    complete = view.status == "complete" and view.choice is not None
    metric_name = tx(dict(METRICS)[metric])
    reasons_of = reason_words(tx)
    z: list[list[float | None]] = []
    text_: list[list[str]] = []
    hover: list[list[str]] = []
    for g in gs:
        zr: list[float | None] = []
        tr: list[str] = []
        hr: list[str] = []
        for s in ss:
            if (g, s) not in view.pairs:
                zr.append(None)
                tr.append("")
                hr.append("")
                continue
            r = view.result((g, s))
            na = view.na.get((g, s))
            value = metric_value(r, na, metric)
            zr.append(value)
            if r is None:
                tr.append("")
                hr.append(tx("g={g}, s={s}: pending", g=g, s=s))
                continue
            reasons = view.choice.reasons[(g, s)] if complete and view.choice else []
            mark = "★" if complete and view.star == (g, s) else ""
            tr.append(mark + "".join(LETTERS[x] for x in reasons))
            verdict = (tx("✓ qualifies") if complete and not reasons else
                       "; ".join(reasons_of[x] for x in reasons) if complete else tx("selection after the whole grid"))
            hr.append(tx("g={g}, s={s}<br>{metric}: {value}<br>NA: {na}<br>tags: {tags}<br>Multi-Tag Clusters: "
                         "{clusters}<br>{verdict}", g=g, s=s, metric=metric_name, value=tx.num(value, 3),
                         na=tx.num(None if na is None else na.value, 3), tags=r.n_tags, clusters=tx.num(r.n_multi),
                         verdict=verdict))
        z.append(zr)
        text_.append(tr)
        hover.append(hr)
    grey = metric in ("q",)
    fig = go.Figure(go.Heatmap(z=z, x=ss, y=gs, text=text_, texttemplate="%{text}", hovertext=hover,
                               hoverinfo="text", colorscale="Greys" if grey else "Viridis", showscale=True,
                               colorbar={"title": metric_name}, xgap=1, ygap=1))
    shapes = []
    if complete and view.choice is not None:
        for g, s in view.choice.near_best:
            shapes.append(_cell_shape(g, s, "#f28e2b", 2))
    if inspected is not None:
        shapes.append(_cell_shape(*inspected, "#222", 3))
    caption = tx(T.DESCRIPTIVE_CAPTION) if metric == "q" else ""
    # The ticks name the cells' centres; the grid lines go between the cells (half-way), so the empty cells
    # behind the grey background line up with the filled ones and their gaps.
    edges = {"dtick": 1, "showgrid": False, "zeroline": False,
             "minor": {"tick0": 0.5, "dtick": 1, "showgrid": True, "gridcolor": "#fff", "gridwidth": 1}}
    fig.update_layout(shapes=shapes, margin={"l": 40, "r": 10, "t": 30 if caption else 10, "b": 40},
                      xaxis={"title": tx("s (minimum shared games)"), **edges},
                      yaxis={"title": tx("g (minimum games per tag)"), **edges}, plot_bgcolor="#e6e6e6",
                      title={"text": caption, "font": {"size": 12}} if caption else None,
                      separators=plotly_separators(tx))
    return fig


def _cell_shape(g: int, s: int, color: str, width: int) -> dict[str, Any]:
    return {"type": "rect", "x0": s - 0.5, "x1": s + 0.5, "y0": g - 0.5, "y1": g + 0.5,
            "line": {"color": color, "width": width}, "fillcolor": "rgba(0,0,0,0)"}


def heatmap_key(L: Labels) -> html.Div:
    letters = [html.Span([html.B(letter), " ", L.term(REASON_WORDS[code], f"selection.reason.{letter}")],
                         className="ps-key-item") for code, letter in LETTERS.items()]
    return html.Div([L.span(msg("★ chosen · orange outline: near-best · dark outline: inspected · "),
                            className="mute small"), *letters,
                     _static_help(L, "selection.heatmap")], className="ps-key")


def metric_picker(L: Labels) -> html.Div:
    keys = {"neighbour_agreement": "selection.metric.neighbour_agreement", "retention": "selection.metric.retention",
            "isolated_share": "selection.metric.isolated_share",
            "multi_tag_clusters": "selection.metric.multi_tag_clusters", "seed_noise": "selection.metric.seed_noise",
            "q": "selection.metric.q"}
    return html.Div([
        dcc.RadioItems(id="ps-metric", options=L.options("ps-metric", METRICS), value="neighbour_agreement",
                       className="seg", inline=True),
        html.Span([L.term(label, keys[key]) for key, label in METRICS], className="ps-metric-help"),
    ], className="ps-picker")


# ----------------------------------------------------------------------------- "Why this pair" and validation


def render(paragraphs: list[T.Paragraph]) -> list[Any]:
    out = []
    for p in paragraphs:
        spans = [html.B(t) if style == "bold" else html.I(t) if style == "italic" else t for t, style in p]
        out.append(html.P(spans))
    return out


def why(view: DatasetView, inspected: tuple[int, int] | None, settings_label: str, constraints_label: str,
        minimum_k: int, *, tx: Text) -> list[Any]:
    """"Why this pair" for the inspected cell: the selected pair's explanation, or for any other pair whether it
    qualifies and why another one was selected."""
    if view.status == "not_run":
        return [html.P(tx(T.NOTHING_RUN))]
    if view.status != "complete" or view.choice is None:
        return [html.P(tx(T.NO_SELECTION_YET, done=view.done, total=view.total))]
    if inspected is not None and inspected != view.star and (other := view.result(inspected)) is not None:
        return [html.H4(tx("Why this pair")),
                *render(T.pair_explanation(view.choice, inspected, other, view.na[inspected], settings_label,
                                           constraints_label, minimum_k, reason_words(tx), tx=tx))]
    if view.star is None:
        table = html.Table([html.Tr([html.Th(tx("Constraint")), html.Th(tx("alone")), html.Th(tx("cumulative"))])] + [
            html.Tr([html.Td(phrase), html.Td(str(e.alone)), html.Td(str(e.cumulative))])
            for phrase, e in zip(T.constraint_phrases(view.choice.constraints, tx), view.choice.exclusion)],
            className="ps-table")
        return [html.H4(tx("Why this pair")), *render(T.no_qualifying_message(view.choice, constraints_label, tx=tx)),
                table]
    pair = view.result(view.star)
    assert pair is not None
    return [html.H4(tx("Why this pair")), *render(T.explanation(view.choice, pair, view.na[view.star], settings_label,
                                                                constraints_label, minimum_k, tx=tx))]


def _chips(c: Mapping[str, Any], tx: Text) -> list[Any]:
    """A Cluster's status chips in one arm, in display order: Not assessable, Dissolved in most subsamples,
    borderline."""
    out: list[Any] = []
    if not c["assessable"]:
        out.append(html.Span(tx("Not assessable"), className="ps-chip na"))
    if c["dissolved_in_most"]:
        out.append(html.Span(tx("Dissolved in most subsamples"), className="ps-chip diss"))
    if c["borderline"]:
        out.append(html.Span(tx("borderline"), className="ps-chip bord"))
    return out


def _status(c: Mapping[str, Any]) -> tuple[bool, bool, bool]:
    return c["assessable"], c["dissolved_in_most"], c["borderline"]


def _whisker(arms: list[tuple[str, Mapping[str, Any]]], tx: Text) -> html.Div:
    """The dot-and-whisker plot of one Cluster: per arm, the dissolution frequency (dot) and its 95% Wilson interval
    (whisker) against ½, in absolutely positioned spans; dark when Dissolved in most subsamples, hollow grey
    otherwise, and "Not assessable" in words when B* = 0."""
    track: list[Any] = [html.Span(className="ps-half")]
    labels: list[Any] = []
    for i, (letter, c) in enumerate(arms):
        line = f"ps-wl{i + 1}"
        labels.append(html.Span(letter, className=f"ps-wlab {line}"))
        if not c["assessable"]:
            track.append(html.Span(tx("Not assessable"), className=f"ps-wna {line}"))
            continue
        tone = "diss" if c["dissolved_in_most"] else "open"
        low, high = c["wilson_low"], c["wilson_high"]
        track.append(html.Span(className=f"ps-wbar {line} {tone}",
                               style={"left": f"{low * 100:.2f}%", "width": f"{(high - low) * 100:.2f}%"}))
        track.append(html.Span(className=f"ps-wdot {line} {tone}",
                               style={"left": f"{c['dissolution_frequency'] * 100:.2f}%"}))
    return html.Div([*labels, html.Div(track, className="ps-track")], className="ps-whisker")


def _compact(lo: float | None, hi: float | None, tx: Text) -> str:
    """A compact range of values ≥ 0 (Jaccard spreads): an en dash, no spaces."""
    return "—" if lo is None or hi is None else f"{tx.fixed(lo, '.2f')}–{tx.fixed(hi, '.2f')}"


def _mean_se(mean: float | None, se: float | None, tx: Text) -> str:
    if mean is None:
        return "—"
    return tx.fixed(mean, ".2f") + ("" if se is None else f" ± {tx.fixed(se, '.2f')}")


def _frequency(k: int, b: int, low: float | None, high: float | None, tx: Text) -> list[Any]:
    """"k of B*" over a Wilson interval as whole percents ("42–62%")."""
    if not b or low is None or high is None:
        return ["—"]
    return [tx("{k} of {n}", k=k, n=b),
            html.Span(f"{tx.fixed(low * 100, '.0f')}–{tx.pct(high, 0)}", className="sub")]


def _detail(arms: list[tuple[str, Mapping[str, Any]]], members: list[int], names: Mapping[int, str], *,
            tx: Text) -> html.Div:
    """An expanded row: every figure for both arms, then every member tag."""
    def head(top: str, sub: str) -> html.Th:
        return html.Th([top, html.Span(sub, className="sub")], className="n")

    rows = [html.Tr([html.Th(tx("Arm")), head(tx("Hennig's J"), tx("mean ± s.e.; 10th–90th pct")),
                     head(tx("≤ 0.5 in"), tx("k of B*; 95% Wilson")), head(tx("> 0.75 in"), tx("k of B*; 95% Wilson")),
                     head(tx("Whole-Cluster J"), tx("mean ± s.e."))])]
    for name, c in arms:
        b = c["assessable_subsamples"]
        rows.append(html.Tr([
            html.Td(name),
            html.Td([_mean_se(c["mean_jaccard"], c["mean_jaccard_se"], tx),
                     html.Span(_compact(c["jaccard_p10"], c["jaccard_p90"], tx), className="sub")], className="n"),
            html.Td(_frequency(c["at_most_half"], b, c["wilson_low"], c["wilson_high"], tx), className="n"),
            html.Td(_frequency(c["recovered"], b, c["recovery_wilson_low"], c["recovery_wilson_high"], tx),
                    className="n"),
            html.Td(_mean_se(c["mean_whole_cluster_jaccard"], c["whole_cluster_jaccard_se"], tx), className="n"),
        ]))
    tags = ", ".join(names.get(t, str(t)) for t in members)
    return html.Div([html.Div(html.Table(rows, className="ps-table ps-ctable"), className="ps-tw"),
                     html.Div(tags, className="small mute")], className="ps-cdetail")


def cluster_list(summary: Mapping[str, Any], names: Mapping[int, str], *, tx: Text) -> html.Div:
    """The interval plot: one expandable row per Multi-Tag Cluster, in Cluster order, with its size, the dissolution
    frequency of both arms against ½, and its statuses."""
    sub = summary["subsample"]
    re_arm, at_arm = sub["reselected"], sub["at_resolution"]
    size_help = html.Span("?", className="ps-q term", tabIndex="0", **H.attrs(
        "selection.subsample", tx, last=("caution", tx(
            "Clusters of 2–3 tags can take only a few Jaccard values, and they drop sharply when they lose or move "
            "one tag."))))
    rows: list[Any] = [
        html.P([tx("Share of subsamples with Hennig's Jaccard ≤ 0.5, with its 95% Wilson interval. R = re-selected, "
                   "A = at resolution."), " ", tx("Click a row for every figure.")], className="ps-legend small mute"),
        html.Div([html.Span(tx("Cluster")), html.Span([tx("Size"), size_help]), html.Span(tx("≤ 0.5: 0 — ½ — 1")),
                  html.Span(tx("Status"), className="st")], className="ps-crow head"),
    ]
    for r, a in zip(re_arm["clusters"], at_arm["clusters"]):
        if _status(r) == _status(a):
            status: list[Any] = _chips(r, tx)
        else:
            status = [html.Span("R", className="small mute"), " ", *(_chips(r, tx) or ["—"]), " ",
                      html.Span("A", className="small mute"), " ", *(_chips(a, tx) or ["—"])]
        flags = [(letter, c, arm["n"] - arm["degenerate"]) for letter, c, arm in (("R", r, re_arm), ("A", a, at_arm))
                 if c["rarely_assessable"]]
        if len(flags) == 2 and (flags[0][1]["assessable_subsamples"], flags[0][2]) == (
                flags[1][1]["assessable_subsamples"], flags[1][2]):
            flags = flags[:1]
            flags[0] = ("", *flags[0][1:])
        for letter, c, s in flags:
            status.append(html.Span(("⚑ " + (f"{letter} " if letter else "")
                                     + tx("rarely assessable ({b} of {s})", b=c["assessable_subsamples"], s=s)),
                                    className="ps-flag"))
        members = [names.get(t, str(t)) for t in r["members"]]
        shown = ", ".join(members[:3]) + (", …" if len(members) > 3 else "")
        summary_row = html.Summary([
            html.Span([html.B(r["label"]), html.Span(shown, className="mem")], className="ps-cname"),
            html.Span(str(r["size"]), className="n"),
            _whisker([("R", r), ("A", a)], tx),
            html.Span(status, className="st"),
        ], className="ps-crow")
        rows.append(html.Details([summary_row, _detail([(tx("re-selected"), r), (tx("at resolution"), a)], r["members"],
                                                       names, tx=tx)], className="ps-crow-d"))
    return html.Div(rows, className="ps-clusters")


def validation_card(view: DatasetView, validation: Mapping[str, Any] | None, names: Mapping[int, str], *,
                    tx: Text, pair: tuple[int, int] | None = None) -> list[Any]:
    """The validation of `pair`, the cell inspected on the heatmap (by default the default-constraint pair), with the
    custom-constraints note when another pair is chosen (or a warning when none qualifies under them)."""
    if view.status != "complete" or view.default_choice is None:
        return []
    default = view.default_choice.chosen
    pair = pair or default
    if pair is None:
        return [html.P(tx("No pair qualifies under the default constraints, so nothing was validated automatically. "
                          "Validate this pair is offered on any inspected pair."))]
    summary = validation["summary"] if validation else None
    out: list[Any] = [html.H4([T.validation_title(pair, tx=tx), _help("selection.validate", tx)])]
    if pair == default:
        note = T.constraints_note(pair, view.star, view.star == pair, tx=tx)
    elif default is not None:
        note = (tx("This is the pair you selected; the pair chosen under the default constraints is g = {g}, s = {s}.",
                   g=default[0], s=default[1]), False)
    else:
        note = None
    if note is not None:
        out.append(html.P(note[0], className="ps-note warning" if note[1] else "small mute"))
    if summary is None:
        result = view.result(pair)
        if result is None or result.selected is None:
            return out + [html.P(tx("This pair has no Selected Partition, so it cannot be validated."))]
        return out + [html.P(tx("Not validated. Validate this pair in the Pair Inspector runs its validation."))]
    for section in (T.null_section(summary, pair, tx=tx), T.subsample_section(summary, names, tx=tx)):
        out += [html.H5([section.title, _help(section.help_key, tx)]), html.P(section.header, className="small mute"),
                *render(section.paragraphs)]
    out.append(cluster_list(summary, names, tx=tx))
    out += render(T.closing(tx=tx))
    out.append(html.Div([_term(tx("Three kinds of stability"), "selection.stability", tx), " · ",
                         _term(tx("Null Comparison"), "selection.null", tx), " · ",
                         _term(tx("Subsample Stability"), "selection.subsample", tx)], className="small"))
    return out


# ----------------------------------------------------------------------------- Pair Inspector


def champ_figure(result: SEL.GraphResult, *, tx: Text) -> go.Figure:
    fig = go.Figure()
    champ = result.champ
    if champ is None:
        fig.update_layout(title={"text": tx("No edges: no scan")}, height=260, separators=plotly_separators(tx))
        return fig
    end, two_m = champ["gamma_end"], champ["two_m"]
    parts = champ["admissible"]
    xs = [0.0, end]
    for i, p in enumerate(parts):
        fig.add_trace(go.Scatter(x=xs, y=[(p["a_hat"] - x * p["p_hat"]) / two_m for x in xs], mode="lines",
                                 line={"width": 1, "color": "#bbb"}, name=f"P{i + 1}", hoverinfo="name",
                                 showlegend=False))
    env_x, env_y = [], []
    for p in parts:
        env_x += [p["a"], p["b"]]
        env_y += [(p["a_hat"] - p["a"] * p["p_hat"]) / two_m, (p["a_hat"] - p["b"] * p["p_hat"]) / two_m]
    fig.add_trace(go.Scatter(x=env_x, y=env_y, mode="lines", line={"width": 3, "color": "#4e79a7"},
                             name=tx("envelope"), showlegend=False))
    shapes, notes = [], []
    for i, p in enumerate(parts):
        if p["stable"]:
            shapes.append({"type": "rect", "xref": "x", "yref": "paper", "x0": p["a"], "x1": p["b"], "y0": 0, "y1": 1,
                           "fillcolor": "rgba(89,161,79,0.18)", "line": {"width": 0}})
        if p["gamma_hat"] is not None and p["target"] is not None:
            t = parts[p["target"]]
            y = (t["a_hat"] - p["gamma_hat"] * t["p_hat"]) / two_m
            notes.append({"x": p["gamma_hat"], "y": y, "ax": (p["a"] + p["b"]) / 2,
                          "ay": (p["a_hat"] - (p["a"] + p["b"]) / 2 * p["p_hat"]) / two_m, "axref": "x",
                          "ayref": "y", "showarrow": True, "arrowhead": 2, "arrowcolor": "#e15759", "text": ""})
    if result.selected_resolution is not None:
        shapes.append({"type": "line", "xref": "x", "yref": "paper", "x0": result.selected_resolution,
                       "x1": result.selected_resolution, "y0": 0, "y1": 1, "line": {"color": "#222", "dash": "dot"}})
    fig.update_layout(shapes=shapes, annotations=notes, height=280, margin={"l": 40, "r": 10, "t": 10, "b": 35},
                      xaxis={"title": "γ", "range": [0, end]}, yaxis={"title": "Q"}, separators=plotly_separators(tx))
    return fig


def _kv(rows: list[tuple[Any, str]]) -> html.Table:
    return html.Table([html.Tr([html.Th(k), html.Td(v)]) for k, v in rows], className="ps-kv")


def links_table(view: DatasetView, pair: tuple[int, int], *, tx: Text) -> html.Table:
    if not view.links:
        return html.Table([], className="ps-table")
    directions = SEL.pair_links(view.links, *pair, view.pairs)
    rows = [html.Tr([html.Th(x) for x in ("", tx("status"), "ARI", tx("tag overlap"))]
                    + [html.Th(_term(tx("Edge Overlap"), "selection.edge_overlap", tx)), html.Th("")])]
    for name, link in directions.items():
        if link is None:
            continue
        rows.append(html.Tr([html.Td(name), html.Td(link.status), html.Td(tx.num(link.ari)),
                             html.Td(tx.num(link.shared_jaccard)), html.Td(tx.num(link.edge_overlap)),
                             html.Td(tx("identical graph") if link.identical_graph else "")]))
    return html.Table(rows, className="ps-table ps-links")


def workbench_line(result: SEL.GraphResult, *, tx: Text) -> tuple[str, str]:
    wb = result.workbench
    if wb is None:
        return tx("No Selected Partition: {reason}", reason=result.reason), "warning small"
    seed = tx("main seed") if wb["seed_kind"] == "main" else tx("scan seed {seed}", seed=wb["seed"])
    gamma = tx.fixed(wb["gamma"], ".2f")
    if wb["flag"] is None:
        return tx("Workbench γ {gamma}, {seed}: reproduces the Selected Partition ✓", gamma=gamma, seed=seed), "small"
    return (tx("Workbench γ {gamma}, main seed: {flag}, shows a different partition (ARI {ari})", gamma=gamma,
               flag=wb["flag"], ari=tx.fixed(wb["ari"], ".2f")), "warning small")


def inspector(view: DatasetView, pair: tuple[int, int] | None, names: Mapping[int, str], *, tx: Text) -> list[Any]:
    if pair is None or view.result(pair) is None:
        return [html.P(tx("Click a computed cell to inspect its pair."), className="mute")]
    r = view.result(pair)
    assert r is not None
    g, s = pair
    complete = view.choice is not None
    reasons = view.choice.reasons[pair] if complete and view.choice else []
    reasons_of = reason_words(tx)
    badges = ([html.Span(tx("✓ qualifies"), className="ps-badge ok")] if complete and not reasons else
              [html.Span(reasons_of[x], className="ps-badge") for x in reasons])
    p = r.selected_partition
    if p is not None and p["clipped_high"]:
        badges.append(html.Span("clipped_high", className="ps-badge"))
    if r.workbench and r.workbench["flag"]:
        badges.append(html.Span(r.workbench["flag"], className="ps-badge"))
    na = view.na.get(pair)
    na_text = (tx.num(None) if na is None or na.value is None else
               tx.n(na.n_different, one="{value} over {n} different-graph neighbour; {identical} identical, {missing} "
                                        "missing",
                    other="{value} over {n} different-graph neighbours; {identical} identical, {missing} missing",
                    value=tx.fixed(na.value, ".3f"), identical=na.n_identical, missing=na.n_missing))
    noise = r.seed_noise
    na_ = tx.num(None)
    interval = ", " if tx.decimal == "." else "; "  # a decimal comma needs another mark between the two ends
    metrics = _kv([
        (_term(tx("Neighbour Agreement"), "selection.inspector.neighbour_agreement", tx), na_text),
        (_term(tx("Information Retention"), "selection.inspector.retention", tx), tx.num(r.retention, 3)),
        (_term(tx("isolated share"), "selection.inspector.isolated_share", tx), tx.num(r.isolated_share, 3)),
        (_term(tx("LCC share"), "selection.inspector.lcc_share", tx), tx.num(r.lcc_share, 3)),
        (_term(tx("Multi-Tag / One-Tag Clusters"), "selection.inspector.clusters", tx),
         na_ if r.n_multi is None else tx("{multi} / {isolated} isolated + {connected} connected", multi=r.n_multi,
                                          isolated=r.n_one_isolated, connected=r.n_one_connected)),
        (_term(tx("Seed-Noise Floor"), "selection.inspector.seed_noise", tx),
         na_ if noise is None else tx("min {floor}, mean {mean}, exact {exact} of {runs}",
                                      floor=tx.fixed(noise["floor"], ".2f"), mean=tx.fixed(noise["mean"], ".2f"),
                                      exact=noise["exact"], runs=noise["runs"])),
        (_term(tx("hits"), "selection.inspector.hits", tx),
         na_ if p is None else tx("{hits} of {runs} runs", hits=p["hits"], runs=r.scan_runs)),
        (_term(tx("domain"), "selection.inspector.domain", tx),
         na_ if p is None else f"[{tx.fixed(p['a'], '.3f')}{interval}{tx.fixed(p['b'], '.3f')}]"),
        (_term("γ̂", "selection.inspector.gamma_hat", tx), na_ if p is None else tx.num(p["gamma_hat"], 3)),
        (_term(tx("Selected Resolution"), "selection.inspector.resolution", tx), tx.num(r.selected_resolution, 3)),
        (_term(tx("scan range"), "selection.inspector.scan_range", tx),
         tx("no scan") if r.gamma_end is None else
         tx("0 to {end} (n_e = {n_e}, {n} values)", end=tx.fixed(r.gamma_end, ".2f"), n_e=r.n_e, n=r.scan_length)),
    ])
    descriptive = html.Div([
        html.Div(_term(tx(T.DESCRIPTIVE_CAPTION), "selection.inspector.descriptive", tx), className="small mute"),
        _kv([(_term("Q", "selection.inspector.q", tx), tx.num(r.modularity, 3)),
             (_term(tx("Coverage"), "selection.inspector.coverage", tx), tx.num(r.coverage, 3)),
             (_term(tx("Silhouette"), "selection.inspector.silhouette", tx), tx.num(r.silhouette, 3))]),
    ], className="ps-descriptive")
    clusters: list[Any] = []
    if p is not None:
        groups: dict[int, set[int]] = {}
        for t, label in zip(r.nodes, p["membership"]):
            groups.setdefault(label, set()).add(t)
        remove = tx("Remove (stage in Selection settings)")
        for c in label_clusters([frozenset(x) for x in groups.values()]):
            if c.size < 2:
                continue
            clusters.append(html.Div([html.B(c.label + " "), *[
                html.Span([names.get(t, str(t)), html.Button("×", id={"type": "ps-remove", "tag": t},
                                                              className="x small", title=remove)],
                          className="ps-member") for t in sorted(c.members, key=lambda t: names.get(t, ""))]],
                className="ps-cluster"))
    return [
        html.H4([tx("{dataset}: g = {g}, s = {s}", dataset=view.label, g=g, s=s), _help("selection.inspector", tx)]),
        html.Div(badges, className="ps-badges"),
        html.H5([tx("Metrics")]), metrics, descriptive,
        html.H5([_term(tx("Neighbour links"), "selection.inspector.links", tx)]), links_table(view, pair, tx=tx),
        html.H5([_term("CHAMP", "selection.inspector.champ", tx)]),
        dcc.Graph(figure=champ_figure(r, tx=tx), config={"displayModeBar": False}, id="ps-champ"),
        html.H5(tx("Clusters")), *clusters,
    ]


def _null_badge(summary: Mapping[str, Any], tx: Text) -> html.Span:
    """The Null Comparison in one badge, in its three states, with " ⚠" when most shuffled networks have no Q."""
    null = summary["null"]
    state, d = summary["verdicts"]["null_q"], null["q_defined"]
    weak = " ⚠" if null["weak"] else ""
    if state == "reached":
        words: Any = [_term(tx("Q not above the null ({k} of {d})", k=null["q"]["reach"], d=d),
                            "selection.verdict.q_not_above_null", tx), weak]
    elif state == "above_all_defined":
        words = tx("Q above all {d} shuffled networks", d=d) + weak
    else:
        words = tx("Null Q undefined") + weak
    return html.Span(words, className=f"ps-badge null-{state}" + (" warn" if weak else ""))


def _status_strip(letter: str, clusters: list[Mapping[str, Any]]) -> html.Div:
    """One square per Multi-Tag Cluster in Cluster order: dark = dissolved in most subsamples, dashed outline =
    borderline, hatched = not assessable; the label as its tooltip."""
    def classes(c: Mapping[str, Any]) -> str:
        out = ["ps-sq"]
        if not c["assessable"]:
            out.append("na")
        if c["dissolved_in_most"]:
            out.append("diss")
        if c["borderline"]:
            out.append("bord")
        return " ".join(out)

    return html.Div([html.Span(letter, className="small mute ps-strip-lab"),
                     *[html.I(className=classes(c), title=c["label"]) for c in clusters]], className="ps-vstrip")


def inspector_validation(view: DatasetView, pair: tuple[int, int] | None, validation: Mapping[str, Any] | None, *,
                         tx: Text) -> list[Any]:
    """The Inspector's Validation section, above the static Validate this pair button: "Not validated", or the null
    badge, the dissolved count, the R and A status strips, the median ARI and a link to the card (which follows the
    inspected pair)."""
    result = None if pair is None else view.result(pair)
    if result is None or result.selected is None:
        return []
    head = html.H5([tx("Validation"), _help("selection.validate", tx)])
    if not validation:
        return [head, html.P(tx("Not validated"), className="mute")]
    v = validation["summary"]
    sub = v["subsample"]
    out: list[Any] = [
        head,
        html.Div([_null_badge(v, tx), html.Span(_term(
            tx("Dissolved in most subsamples (re-selected): {n}", n=len(v["verdicts"]["dissolved_in_most"]["reselected"])),
            "selection.verdict.dissolved", tx), className="ps-badge")], className="ps-badges"),
        _status_strip("R", sub["reselected"]["clusters"]), _status_strip("A", sub["at_resolution"]["clusters"]),
        html.Div(tx("median ARI re-selected {reselected}, at resolution {at}",
                    reselected=tx.num(sub["reselected"]["ari"]["median"]),
                    at=tx.num(sub["at_resolution"]["ari"]["median"])), className="small"),
    ]
    goto: dict[str, Any] = {"data-goto": "ps-validation"}  # workbench.js scrolls the main column to the card
    out.append(html.A(tx("Open the validation card") + " ↓", href="#ps-validation", className="small ps-goto", **goto))
    return out


# ----------------------------------------------------------------------------- the whole mode


def mode_layout(ctx: BuildContext, L: Labels) -> html.Div:
    defaults, constraints = defaults_of(ctx)
    first = ctx.datasets[0].key
    main = html.Div([
        html.Div(id="ps-strip", className="ps-strip"),
        constraints_bar(L, constraints),
        P.rail(L, "ps", "constraints"),
        metric_picker(L),
        # Responsive: it follows the main column's width when a panel is turned off. The height stays 460 px: app.css
        # gives it `flex: 0 0 460px` in the scrolling main column, so a long validation card cannot shrink it.
        dcc.Graph(id="ps-heatmap", config={"displayModeBar": False}, responsive=True, style={"height": "460px"}),
        heatmap_key(L),
        html.Div(id="ps-why", className="panel ps-why"),
        html.Div(id="ps-validation", className="panel ps-validation"),
    ], id="ps-main", className="main ps-main")
    # The loading panel, over the main column while a job runs (ps_render fills it); Cancel, in the Controls, stays
    # in reach.
    job = html.Div(id="ps-loading", className="ps-job")
    # Over the whole mode while ps_render runs (callbacks.py `running`): entering the mode, a dataset or a metric.
    busy = html.Div(html.Div(html.Span(L.prop("ps-busy", "children", msg("Loading Parameter Selection…")),
                                       id="ps-busy", hidden=True), className="busy", role="status"),
                    className="ps-busy")
    inspector_panel = html.Div([
        html.Div([html.B(L.span(msg("Pair Inspector"))), P.collapse_button(L, "ps", "inspector"),
                  html.Button("×", id="ps-inspector-close", className="x",
                              title=L.prop("ps-inspector-close", "title", msg("Close")))],
                 className="insp-title"),
        html.Div([html.Button(L.prop("ps-apply", "children", msg("Apply to Workbench")), id="ps-apply",
                              className="btn primary"),
                  _static_help(L, "selection.apply"),
                  # Always shown; enabled under Apply to Workbench's rule and only when these settings are the
                  # comparison's shared settings (callbacks.py `ps_use_cc_state`).
                  html.Button(L.prop("ps-use-cc", "children", msg("Use in Cluster Comparison")), id="ps-use-cc",
                              className="btn", disabled=True),
                  _static_help(L, "selection.use_in_comparison")], className="row-inline"),
        html.Div(id="ps-apply-line", className="small"),
        html.Div(id="ps-inspector-body"),
        # The Validation section at the Inspector's bottom: its content is rendered, and the Validate this pair button
        # stays a static component under it (its callback toggles the style and `disabled`).
        html.Div([html.Div(id="ps-inspector-validation"),
                  html.Button(L.prop("ps-validate", "children", msg("Validate this pair")), id="ps-validate",
                              className="btn", style={"display": "none"})], className="ps-insp-validation"),
    ], id="ps-inspector", className=inspector_form(False))
    stores = [dcc.Store(id="ps-active", data=settings_data(defaults)),
              dcc.Store(id="ps-constraints", data={"shared": constraints_data(constraints), "datasets": {}}),
              dcc.Store(id="ps-dataset", data=first), dcc.Store(id="ps-pair"),
              dcc.Store(id="ps-run-request"), dcc.Store(id="ps-run-done"), dcc.Store(id="ps-progress"),
              dcc.Store(id="ps-running", data=False),
              dcc.Store(id="ps-validate-request"), dcc.Store(id="ps-validate-done"), dcc.Store(id="ps-applied"),
              dcc.Download(id="ps-download")]
    return html.Div([*stores, controls(L, ctx, defaults), P.rail(L, "ps", "controls"), main, job, inspector_panel,
                     P.rail(L, "ps", "inspector"), busy],
                    id="ps-body", className="app-body ps-body")

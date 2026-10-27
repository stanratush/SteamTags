"""The Parameter Selection mode's components: layout variant A, "Three panes", shaped like the Workbench.

Left, the Controls column (Run, Pair Constraints, Selection settings); in the middle the dataset strip, the metric
picker, the g × s heatmap, "Why this pair" and the validation card; on the right the Pair Inspector. Everything here
is a pure function of the Build, the cache and the mode's stores; `callbacks.py` wires it.
"""

from __future__ import annotations

import dataclasses
import platform
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import plotly.graph_objects as go
from dash import dcc, html

from steamstudy.app import help as H
from steamstudy.app import ps_cache, ps_run
from steamstudy.app.ps_export import constraints_for, tag_names
from steamstudy.app.loader import BuildContext
from steamstudy.network import selection as SEL
from steamstudy.network import selection_text as T
from steamstudy.network.cluster import label_clusters
from steamstudy.versions import APP_LIBRARIES, software_versions

METRICS = [("neighbour_agreement", "Neighbour Agreement"), ("retention", "Information Retention"),
           ("isolated_share", "isolated share"), ("multi_tag_clusters", "Multi-Tag Clusters"),
           ("seed_noise", "Seed-Noise Floor"), ("q", "Q")]
LETTERS = {"no_selected_partition": "P", "no_neighbour_agreement": "A", "too_few_comparable_neighbours": "N",
           "retention_below_min": "R", "isolated_share_above_max": "I", "lcc_share_below_min": "L",
           "too_many_clusters": "K"}
REASON_WORDS = {"no_selected_partition": "no Selected Partition", "no_neighbour_agreement": "no Neighbour Agreement",
                "too_few_comparable_neighbours": "too few comparable neighbours",
                "retention_below_min": "Information Retention below the minimum",
                "isolated_share_above_max": "isolated share above the maximum",
                "lcc_share_below_min": "LCC share below the minimum", "too_many_clusters": "too many Multi-Tag Clusters"}
CONSTRAINT_FIELDS = [("min_retention", "Minimum Information Retention", 0.0, 1.0, 0.01),
                     ("max_isolated_share", "Maximum isolated share", 0.0, 1.0, 0.01),
                     ("min_lcc_share", "Minimum LCC share", 0.0, 1.0, 0.01),
                     ("min_comparable_neighbours", "Minimum comparable neighbours (different graph)", 0, 4, 1),
                     ("max_multi_tag_clusters", "Maximum Multi-Tag Clusters (empty = off)", 1, None, 1),
                     ("tolerance", "Tolerance (near-best)", 0.0, 1.0, 0.01)]
CONSTRAINT_HELP = {"tolerance": "selection.constraint.tolerance"} | {
    name: f"selection.constraint.{name}" for name, *_ in CONSTRAINT_FIELDS if name != "tolerance"}


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
                  cache_root: Path | None = None) -> dict[str, Any] | None:
    if pair is None:
        return None
    key = settings.validation_key(dataset, ctx.context(dataset), *pair)
    return ps_cache.read_validation(Path(cache_root or ctx.app_cache), key)


# ----------------------------------------------------------------------------- small helpers


def _help(key: str) -> html.Span:
    return html.Span("?", className="ps-q term", tabIndex="0", **H.attrs(key))


def _term(text: str, key: str) -> html.Span:
    return html.Span(text, className="term", tabIndex="0", **H.attrs(key))


def _num(value: Any, digits: int = 2) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def provenance(computed_with: Mapping[str, Any] | None) -> tuple[str, str | None]:
    """The quiet provenance line when results were computed elsewhere, and the banner text for a library mismatch."""
    if not computed_with:
        return "", None
    versions = computed_with.get("versions", {})
    now = software_versions()
    mismatched = [(lib, versions[lib], now[lib]) for lib in APP_LIBRARIES
                  if lib in versions and lib in now and versions[lib] != now[lib]]
    if mismatched:
        names = ", ".join(f"{lib} {old} (installed {new})" for lib, old, new in mismatched)
        return "", (f"These Parameter Selection results were computed with {names}; the numbers may differ here. "
                    "Clear app cache and Run to recompute here.")
    same = (versions.get("python") == now.get("python") and computed_with.get("system") == platform.system()
            and computed_with.get("machine") == platform.machine())
    if same:
        return "", None
    day = str(computed_with.get("utc", ""))[:10]
    return (f"Computed when this bundle was made: Python {versions.get('python', '?')}, "
            f"{computed_with.get('system', '?')} {computed_with.get('machine', '?')}, {day}"), None


# ----------------------------------------------------------------------------- Controls column


def _constraint_inputs(defaults: SEL.Constraints) -> list[Any]:
    rows = []
    for name, label, lo, hi, step in CONSTRAINT_FIELDS:
        default = getattr(defaults, name)
        kw: dict[str, Any] = {"min": lo, "step": step}
        if hi is not None:
            kw["max"] = hi
        rows.append(html.Div([
            html.Label([_term(label, CONSTRAINT_HELP[name])], className="l", htmlFor=f"ps-c-{name}"),
            dcc.Input(id=f"ps-c-{name}", type="number", value=default, debounce=True, **kw),
            html.Span(f"default {'off' if default is None else default}", className="mute small"),
            html.Span("", id=f"ps-c-{name}-changed", className="ps-changed small"),
        ], className="ps-field"))
    return rows


def controls(ctx: BuildContext, defaults: SEL.SelectionSettings, constraints: SEL.Constraints) -> html.Div:
    first = ctx.datasets[0].key
    defining = [d.defining_tag.name for d in ctx.datasets if d.defining_tag]
    run = html.Div([
        html.H4(["Run ", _help("selection.run")], className="ctl-h"),
        html.Div([html.Button("Run all datasets", id="ps-run-all", className="btn primary"),
                  html.Button(f"Run {ctx.dataset(first).label}", id="ps-run-one", className="btn"),
                  html.Button("Cancel", id="ps-cancel", className="btn")], className="row-inline"),
        html.Button("Continue", id="ps-continue", className="btn", style={"display": "none"}),
        html.Div(id="ps-rows", className="ps-rows"),
        html.Div(id="ps-cache-line", className="mute small"),
        html.Div(id="ps-provenance", className="mute small"),
        html.Div(id="ps-banner", className="warning", style={"display": "none"}),
        html.Div([html.Button("Export tables", id="ps-export", className="btn", disabled=True),
                  _help("selection.export")], className="row-inline"),
    ], className="ctl-section")
    pc = html.Div([
        html.H4(["Pair Constraints ", _help("selection.constraints")], className="ctl-h"),
        *_constraint_inputs(constraints),
        html.Label("Apply to", className="l"),
        dcc.RadioItems(id="ps-c-scope", options=[{"label": "All five datasets", "value": "all"},
                                                 {"label": "this dataset only", "value": "dataset"}],
                       value="all", className="seg", inline=True),
        html.Div([html.Button("Confirm", id="ps-c-confirm", className="btn primary", disabled=True),
                  html.Button("Reset to defaults", id="ps-c-reset", className="btn")], className="row-inline"),
        html.Span("", id="ps-c-unconfirmed", className="ps-changed small"),
        html.Div(id="ps-c-label", className="mute small"),
    ], className="ctl-section")
    genre = [{"label": t.name, "value": t.id} for t in ctx.genre_tags]
    names = tag_names(ctx)
    settings = html.Div([
        html.H4(["Selection settings ", _help("selection.settings")], className="ctl-h"),
        html.Label([_term("Hidden Genre Tags", "selection.setting.hidden")], className="l"),
        dcc.Checklist(id="ps-s-genre", options=genre, value=list(defaults.genre_hidden), inline=True,
                      className="chips"),
        dcc.Checklist(id="ps-s-defining", options=[{"label": "hide each dataset's defining tag"
                                                    + (f" ({', '.join(defining)})" if defining else ""), "value": 1}],
                      value=[1] if defaults.hide_defining_tag else [], className="check"),
        html.Label([_term("Removed tags", "selection.setting.removed")], className="l"),
        dcc.Dropdown(id="ps-s-removed", options=[{"label": n, "value": t} for t, n in sorted(names.items(),
                                                                                            key=lambda x: x[1])],
                     value=list(defaults.removed_tag_ids), multi=True, placeholder="no removed tags"),
        html.Label([_term("Minimum Months Filter", "selection.setting.min_months")], className="l"),
        dcc.Slider(id="ps-s-min-months", min=0, max=60, step=1, value=defaults.min_months,
                   marks={0: "0", 60: "60"}, tooltip={"placement": "bottom"}),
        html.Label([_term("Clustering weight", "selection.setting.weight")], className="l"),
        dcc.RadioItems(id="ps-s-weight", options=[{"label": "Lift", "value": "lift"},
                                                  {"label": "Shared games", "value": "shared_games"}],
                       value=defaults.clustering_weight, className="seg", inline=True),
        html.Label([_term("Minimum Multi-Tag Clusters", "selection.setting.min_multi_tag_clusters")], className="l"),
        dcc.Input(id="ps-s-min-multi", type="number", min=1, max=10, step=1, value=defaults.min_multi_tag_clusters),
        html.Div([html.Button("Use these settings", id="ps-s-use", className="btn primary"),
                  html.Button("Reset to defaults", id="ps-s-reset", className="btn"),
                  html.Button("Copy from Workbench", id="ps-s-copy", className="btn")], className="stack"),
        html.Div(read_only(defaults), className="mute small ps-readonly"),
        html.Div(id="ps-s-label", className="mute small"),
    ], className="ctl-section")
    return html.Div([html.Div([html.B("Parameter Selection")], className="ctl-title"), run, pc, settings],
                    id="ps-controls", className="controls ps-controls")


def read_only(s: SEL.SelectionSettings) -> list[Any]:
    return [html.Div(T.LEIDEN_ONLY + "."),
            html.Div(f"Parameter Grid: g {s.g_range[0]}–{s.g_range[1]}, s {s.s_range[0]}–{s.s_range[1]}, s ≤ g "
                     f"({len(s.pairs())} pairs)"),
            html.Div(f"γ from 0 to γ_max(n_e) in steps of {s.gamma_step:g}; {s.scan_seeds} scan seeds"),
            html.Div(f"Null Comparison R = {s.replicates}; Subsample Stability S = {s.subsamples}")]


def run_rows(views: list[DatasetView], progress: Mapping[str, Any] | None, validated: Mapping[str, bool]) -> list[Any]:
    rows = []
    for v in views:
        live = progress if progress and progress.get("dataset") == v.dataset else None
        if live and live["phase"] == "validation":
            text, value, top = f"validation {live['done']} of {live['total']} replicates", live["done"], live["total"]
        elif live:
            text, value, top = f"grid {live['done']} of {live['total']} pairs", live["done"], live["total"]
        elif v.status == "complete":
            text = "grid done, validated" if validated.get(v.dataset) else "grid done, not validated"
            value, top = v.total, v.total
        elif v.status == "partial":
            text, value, top = f"grid {v.done} of {v.total} pairs", v.done, v.total
        else:
            text, value, top = "not run", 0, v.total
        rows.append(html.Div([html.Span(v.label, className="ps-row-name"), html.Span(text, className="mute small"),
                              html.Progress(value=str(value), max=str(max(top, 1)))], className="ps-row"))
    return rows


# ----------------------------------------------------------------------------- dataset strip and loading panel


def strip(views: list[DatasetView], current: str, custom: Mapping[str, str]) -> list[Any]:
    buttons = []
    for v in views:
        if v.status == "complete" and v.choice is not None:
            if v.star is None:
                text = "no qualifying pair"
            else:
                g, s = v.star
                text = f"★ {g}·{s} NA {_num(v.na[v.star].value)}"
        elif v.status == "partial":
            text = f"grid {v.done} of {v.total}"
        else:
            text = "not run"
        marker = custom.get(v.dataset)
        buttons.append(html.Button([html.B(v.label), html.Span(text, className="ps-strip-v"),
                                    *([html.Span("custom", className="ps-custom", title=marker)] if marker else [])],
                                   id={"type": "ps-strip", "dataset": v.dataset},
                                   className="ps-strip-btn" + (" on" if v.dataset == current else "")))
    return [html.Div(buttons, className="ps-strip-row"), _help("selection.dataset_strip")]


def loading_panel(progress: Mapping[str, Any] | None, views: list[DatasetView], settings: SEL.SelectionSettings,
                  reason: str, compact: bool) -> list[Any]:
    lengths = [r.scan_length for v in views for r in v.results.values() if r.scan_length]
    scan = f"{min(lengths)}–{max(lengths)}" if lengths else "up to several hundred"
    what = (f"Searching {len(settings.pairs())} Threshold Pairs × {scan} resolutions × {settings.scan_seeds} seeds "
            f"for each dataset, then checking the chosen pair against {settings.replicates} shuffled networks and "
            f"{settings.subsamples} subsamples.")
    where, eta = "Starting…", "estimating…"
    if progress:
        unit = "pairs" if progress["phase"] == "grid" else "replicates"
        where = (f"Dataset {progress['dataset_index']} of {progress['n_datasets']} ({progress['dataset']}): "
                 f"{progress['phase']} {progress['done']} of {progress['total']} {unit}.")
        eta = f"{ps_run.eta_text(progress)} · {ps_run.elapsed_text(progress['elapsed'])}"
    once = ("A one-off: results are cached. Cancel keeps the finished pairs and Continue resumes; a cancelled "
            "validation restarts from the beginning.")
    body = [html.B("Computing Parameter Selection"), html.Div(what), html.Div(reason, className="mute"),
            html.Div(where), html.Div(once, className="mute small"), html.Div(eta, className="ps-eta"),
            html.A("How Automatic Parameter Selection works", href="#", className="term",
                   **H.attrs("selection.run"))]
    return [html.Div(body, className="ps-loading" + (" compact" if compact else ""))]


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


def heatmap(view: DatasetView, metric: str, inspected: tuple[int, int] | None) -> go.Figure:
    gs = sorted({g for g, _ in view.pairs})
    ss = sorted({s for _, s in view.pairs})
    complete = view.status == "complete" and view.choice is not None
    z: list[list[float | None]] = []
    text: list[list[str]] = []
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
                hr.append(f"g={g}, s={s}: pending")
                continue
            reasons = view.choice.reasons[(g, s)] if complete and view.choice else []
            mark = "★" if complete and view.star == (g, s) else ""
            tr.append(mark + "".join(LETTERS[x] for x in reasons))
            verdict = ("✓ qualifies" if complete and not reasons else
                       "; ".join(REASON_WORDS[x] for x in reasons) if complete else "selection after the whole grid")
            hr.append(f"g={g}, s={s}<br>{dict(METRICS)[metric]}: {_num(value, 3)}<br>NA: "
                      f"{_num(None if na is None else na.value, 3)}<br>tags: {r.n_tags}<br>Multi-Tag Clusters: "
                      f"{_num(r.n_multi)}<br>{verdict}")
        z.append(zr)
        text.append(tr)
        hover.append(hr)
    grey = metric in ("q",)
    fig = go.Figure(go.Heatmap(z=z, x=ss, y=gs, text=text, texttemplate="%{text}", hovertext=hover,
                               hoverinfo="text", colorscale="Greys" if grey else "Viridis", showscale=True,
                               colorbar={"title": dict(METRICS)[metric]}, xgap=1, ygap=1))
    shapes = []
    if complete and view.choice is not None:
        for g, s in view.choice.near_best:
            shapes.append(_cell_shape(g, s, "#f28e2b", 2))
    if inspected is not None:
        shapes.append(_cell_shape(*inspected, "#222", 3))
    caption = T.DESCRIPTIVE_CAPTION if metric == "q" else ""
    fig.update_layout(shapes=shapes, margin={"l": 40, "r": 10, "t": 30 if caption else 10, "b": 40},
                      xaxis={"title": "s (minimum shared games)", "dtick": 1},
                      yaxis={"title": "g (minimum games per tag)", "dtick": 1}, plot_bgcolor="#e6e6e6",
                      title={"text": caption, "font": {"size": 12}} if caption else None, height=460)
    return fig


def _cell_shape(g: int, s: int, color: str, width: int) -> dict[str, Any]:
    return {"type": "rect", "x0": s - 0.5, "x1": s + 0.5, "y0": g - 0.5, "y1": g + 0.5,
            "line": {"color": color, "width": width}, "fillcolor": "rgba(0,0,0,0)"}


def heatmap_key() -> html.Div:
    letters = [html.Span([html.B(letter), " ", _term(REASON_WORDS[code], f"selection.reason.{letter}")],
                         className="ps-key-item") for code, letter in LETTERS.items()]
    return html.Div([html.Span("★ chosen · orange outline: near-best · dark outline: inspected · ",
                               className="mute small"), *letters,
                     _help("selection.heatmap")], className="ps-key")


def metric_picker() -> html.Div:
    keys = {"neighbour_agreement": "selection.metric.neighbour_agreement", "retention": "selection.metric.retention",
            "isolated_share": "selection.metric.isolated_share",
            "multi_tag_clusters": "selection.metric.multi_tag_clusters", "seed_noise": "selection.metric.seed_noise",
            "q": "selection.metric.q"}
    return html.Div([
        dcc.RadioItems(id="ps-metric", options=[{"label": label, "value": key} for key, label in METRICS],
                       value="neighbour_agreement", className="seg", inline=True),
        html.Span([_term(label, keys[key]) for key, label in METRICS], className="ps-metric-help"),
    ], className="ps-picker")


# ----------------------------------------------------------------------------- "Why this pair" and validation


def render(paragraphs: list[T.Paragraph]) -> list[Any]:
    out = []
    for p in paragraphs:
        spans = [html.B(t) if style == "bold" else html.I(t) if style == "italic" else t for t, style in p]
        out.append(html.P(spans))
    return out


def why(view: DatasetView, settings_label: str, constraints_label: str, minimum_k: int) -> list[Any]:
    if view.status == "not_run":
        return [html.P(T.NOTHING_RUN)]
    if view.status != "complete" or view.choice is None:
        return [html.P(T.NO_SELECTION_YET.format(done=view.done, total=view.total))]
    if view.star is None:
        table = html.Table([html.Tr([html.Th("Constraint"), html.Th("alone"), html.Th("cumulative")])] + [
            html.Tr([html.Td(phrase), html.Td(str(e.alone)), html.Td(str(e.cumulative))])
            for phrase, e in zip(T.constraint_phrases(view.choice.constraints), view.choice.exclusion)],
            className="ps-table")
        return [html.H4("Why this pair"), *render(T.no_qualifying_message(view.choice, constraints_label)), table]
    pair = view.result(view.star)
    assert pair is not None
    return [html.H4("Why this pair"), *render(T.explanation(view.choice, pair, view.na[view.star], settings_label,
                                                            constraints_label, minimum_k))]


def cluster_table(summary: Mapping[str, Any], names: Mapping[int, str]) -> html.Table:
    head = html.Tr([html.Th(x) for x in ("Arm", "Cluster", "mean Jaccard", "≤ 0.5 in k of B*", "retention share",
                                         "absent", "")])
    rows = [head]
    for arm, label in (("reselected", "re-selected"), ("at_resolution", "at resolution")):
        for c in summary["subsample"][arm]["clusters"]:
            rows.append(html.Tr([html.Td(label), html.Td(T.cluster_name(c, names)), html.Td(_num(c["mean_jaccard"])),
                                 html.Td(f"{c['at_most_half']} of {c['present']}"), html.Td(_num(c["mean_retention"])),
                                 html.Td(str(c["absent"])),
                                 html.Td(_term("Dissolved", "selection.verdict.dissolved") if c["dissolved"] else "")]))
    return html.Table(rows, className="ps-table")


def validation_card(view: DatasetView, validation: Mapping[str, Any] | None, names: Mapping[int, str]) -> list[Any]:
    """The default-constraint pair's validation, with the custom-constraints note when another pair is chosen."""
    if view.status != "complete" or view.default_choice is None:
        return []
    pair = view.default_choice.chosen
    if pair is None:
        return [html.P("No pair qualifies under the default constraints, so nothing was validated automatically. "
                       "Validate this pair is offered on any inspected pair.")]
    summary = validation["summary"] if validation else None
    paragraphs = T.validation_block(summary, pair, view.star, view.star == pair, names)
    out = render(paragraphs)
    if summary is not None:
        out.append(cluster_table(summary, names))
    out.append(html.Div([_term("Three kinds of stability", "selection.stability"), " · ",
                         _term("Null Comparison", "selection.null"), " · ",
                         _term("Subsample Stability", "selection.subsample")], className="small"))
    return out


# ----------------------------------------------------------------------------- Pair Inspector


def champ_figure(result: SEL.GraphResult) -> go.Figure:
    fig = go.Figure()
    champ = result.champ
    if champ is None:
        fig.update_layout(title={"text": "No edges: no scan"}, height=260)
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
                             name="envelope", showlegend=False))
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
                      xaxis={"title": "γ", "range": [0, end]}, yaxis={"title": "Q"})
    return fig


def _kv(rows: list[tuple[Any, str]]) -> html.Table:
    return html.Table([html.Tr([html.Th(k), html.Td(v)]) for k, v in rows], className="ps-kv")


def links_table(view: DatasetView, pair: tuple[int, int]) -> html.Table:
    if not view.links:
        return html.Table([], className="ps-table")
    directions = SEL.pair_links(view.links, *pair, view.pairs)
    rows = [html.Tr([html.Th(x) for x in ("", "status", "ARI", "tag overlap")]
                    + [html.Th(_term("Edge Overlap", "selection.edge_overlap")), html.Th("")])]
    for name, link in directions.items():
        if link is None:
            continue
        rows.append(html.Tr([html.Td(name), html.Td(link.status), html.Td(_num(link.ari)),
                             html.Td(_num(link.shared_jaccard)), html.Td(_num(link.edge_overlap)),
                             html.Td("identical graph" if link.identical_graph else "")]))
    return html.Table(rows, className="ps-table ps-links")


def workbench_line(result: SEL.GraphResult) -> tuple[str, str]:
    wb = result.workbench
    if wb is None:
        return f"No Selected Partition: {result.reason}", "warning small"
    seed = "main seed" if wb["seed_kind"] == "main" else f"scan seed {wb['seed']}"
    if wb["flag"] is None:
        return f"Workbench γ {wb['gamma']:.2f}, {seed}: reproduces the Selected Partition ✓", "small"
    return (f"Workbench γ {wb['gamma']:.2f}, main seed: {wb['flag']}, shows a different partition "
            f"(ARI {wb['ari']:.2f})"), "warning small"


def inspector(view: DatasetView, pair: tuple[int, int] | None, validation: Mapping[str, Any] | None,
              names: Mapping[int, str]) -> list[Any]:
    if pair is None or view.result(pair) is None:
        return [html.P("Click a computed cell to inspect its pair.", className="mute")]
    r = view.result(pair)
    assert r is not None
    g, s = pair
    complete = view.choice is not None
    reasons = view.choice.reasons[pair] if complete and view.choice else []
    badges = ([html.Span("✓ qualifies", className="ps-badge ok")] if complete and not reasons else
              [html.Span(REASON_WORDS[x], className="ps-badge") for x in reasons])
    p = r.selected_partition
    if p is not None and p["clipped_high"]:
        badges.append(html.Span("clipped_high", className="ps-badge"))
    if r.workbench and r.workbench["flag"]:
        badges.append(html.Span(r.workbench["flag"], className="ps-badge"))
    na = view.na.get(pair)
    na_text = ("n/a" if na is None or na.value is None else
               f"{na.value:.3f} over {na.n_different} different-graph neighbour(s); {na.n_identical} identical, "
               f"{na.n_missing} missing")
    noise = r.seed_noise
    metrics = _kv([
        (_term("Neighbour Agreement", "selection.inspector.neighbour_agreement"), na_text),
        (_term("Information Retention", "selection.inspector.retention"), _num(r.retention, 3)),
        (_term("isolated share", "selection.inspector.isolated_share"), _num(r.isolated_share, 3)),
        (_term("LCC share", "selection.inspector.lcc_share"), _num(r.lcc_share, 3)),
        (_term("Multi-Tag / One-Tag Clusters", "selection.inspector.clusters"),
         "n/a" if r.n_multi is None else f"{r.n_multi} / {r.n_one_isolated} isolated + {r.n_one_connected} connected"),
        (_term("Seed-Noise Floor", "selection.inspector.seed_noise"),
         "n/a" if noise is None else f"min {noise['floor']:.2f}, mean {noise['mean']:.2f}, "
                                     f"exact {noise['exact']} of {noise['runs']}"),
        (_term("hits", "selection.inspector.hits"), "n/a" if p is None else f"{p['hits']} of {r.scan_runs} runs"),
        (_term("domain", "selection.inspector.domain"), "n/a" if p is None else f"[{p['a']:.3f}, {p['b']:.3f}]"),
        (_term("γ̂", "selection.inspector.gamma_hat"), "n/a" if p is None else _num(p["gamma_hat"], 3)),
        (_term("Selected Resolution", "selection.inspector.resolution"), _num(r.selected_resolution, 3)),
        (_term("scan range", "selection.inspector.scan_range"),
         "no scan" if r.gamma_end is None else f"0 to {r.gamma_end:.2f} (n_e = {r.n_e}, {r.scan_length} values)"),
    ])
    descriptive = html.Div([
        html.Div(_term(T.DESCRIPTIVE_CAPTION, "selection.inspector.descriptive"), className="small mute"),
        _kv([(_term("Q", "selection.inspector.q"), _num(r.modularity, 3)),
             (_term("Coverage", "selection.inspector.coverage"), _num(r.coverage, 3)),
             (_term("Silhouette", "selection.inspector.silhouette"), _num(r.silhouette, 3))]),
    ], className="ps-descriptive")
    clusters: list[Any] = []
    if p is not None:
        groups: dict[int, set[int]] = {}
        for t, label in zip(r.nodes, p["membership"]):
            groups.setdefault(label, set()).add(t)
        for c in label_clusters([frozenset(x) for x in groups.values()]):
            if c.size < 2:
                continue
            clusters.append(html.Div([html.B(c.label + " "), *[
                html.Span([names.get(t, str(t)), html.Button("×", id={"type": "ps-remove", "tag": t},
                                                              className="x small", title="Remove (stage in Selection "
                                                                                         "settings)")],
                          className="ps-member") for t in sorted(c.members, key=lambda t: names.get(t, ""))]],
                className="ps-cluster"))
    compact = [html.Span("Not validated", className="mute")]
    if validation:
        v = validation["summary"]
        reselected = v["subsample"]["reselected"]["ari"]["median"]
        compact = [html.Span(_term("Q not above the null", "selection.verdict.q_not_above_null")
                             if v["verdicts"]["q_not_above_null"] else "Q above all null replicates",
                             className="ps-badge"),
                   html.Span(f"Dissolved: {len(v['verdicts']['dissolved']['reselected'])}", className="ps-badge"),
                   html.Span(f" median ARI re-selected {_num(reselected)}, at resolution "
                             f"{_num(v['subsample']['at_resolution']['ari']['median'])}", className="small")]
    return [
        html.H4([f"{view.label}: g = {g}, s = {s}", _help("selection.inspector")]),
        html.Div(badges, className="ps-badges"),
        html.H5(["Metrics"]), metrics, descriptive,
        html.H5([_term("Neighbour links", "selection.inspector.links")]), links_table(view, pair),
        html.H5([_term("CHAMP", "selection.inspector.champ")]),
        dcc.Graph(figure=champ_figure(r), config={"displayModeBar": False}, id="ps-champ"),
        html.H5("Clusters"), *clusters,
        html.H5(["Validation ", _help("selection.validate")]), html.Div(compact, className="ps-badges"),
    ]


# ----------------------------------------------------------------------------- the whole mode


def mode_layout(ctx: BuildContext) -> html.Div:
    defaults, constraints = defaults_of(ctx)
    first = ctx.datasets[0].key
    main = html.Div([
        html.Div(id="ps-strip", className="ps-strip"),
        html.Div(id="ps-loading"),
        metric_picker(),
        dcc.Graph(id="ps-heatmap", config={"displayModeBar": False}),
        heatmap_key(),
        html.Div(id="ps-why", className="panel ps-why"),
        html.Div(id="ps-validation", className="panel ps-validation"),
    ], id="ps-main", className="main ps-main")
    inspector_panel = html.Div([
        html.Div([html.B("Pair Inspector")], className="insp-title"),
        html.Div([html.Button("Apply to Workbench", id="ps-apply", className="btn primary"),
                  _help("selection.apply")], className="row-inline"),
        html.Div(id="ps-apply-line", className="small"),
        html.Div([html.Button("Validate this pair", id="ps-validate", className="btn", style={"display": "none"}),
                  _help("selection.validate")], className="row-inline"),
        html.Div(id="ps-inspector-body"),
    ], id="ps-inspector", className="inspector docked ps-inspector")
    stores = [dcc.Store(id="ps-active", data=settings_data(defaults)),
              dcc.Store(id="ps-constraints", data={"shared": constraints_data(constraints), "datasets": {}}),
              dcc.Store(id="ps-dataset", data=first), dcc.Store(id="ps-pair"),
              dcc.Store(id="ps-run-request"), dcc.Store(id="ps-run-done"), dcc.Store(id="ps-progress"),
              dcc.Store(id="ps-running", data=False),
              dcc.Store(id="ps-validate-request"), dcc.Store(id="ps-validate-done"), dcc.Store(id="ps-applied"),
              dcc.Download(id="ps-download")]
    return html.Div([*stores, controls(ctx, defaults, constraints), main, inspector_panel], id="ps-body",
                    className="app-body ps-body")

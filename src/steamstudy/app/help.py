"""Two-layer help for the app's metrics and analytical controls (spec: .scratch/metric-help/spec.md).

Layer 1 is the In short block of the element's User Guide entry: workbench.js shows it as a tooltip on hover or
keyboard focus. Layer 2 is the whole entry, which a click opens in the help modal. The guide is the only source
of the text; the app adds at most one "Now:" line of live values, and a label shown for export columns names them.

A tooltip reaches the browser as structured lines, `[kind, text]` in JSON (`data-tip`): the kinds are the In short
labels' (`guide.IN_SHORT_KINDS`) plus "now", "column", "columns" and "field". workbench.js shows each kind's label in
the Interface Language (the `ui-words` store), so the browser never parses a label. The guide text comes in the
translator's language, English wherever the Bulgarian guide is not written yet.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from typing import Any

from steamstudy.app.guide import LABELS, in_short_at
from steamstudy.export import schema as S
from steamstudy.i18n import Text

METRIC_REFERENCE = "03-metric-reference.md"
APP_CONTROLS = "02-app-controls.md"
CITING = "05-citing-and-reproducing.md"

# help key -> (guide file, heading anchor). Controls whose effect is self-explanatory (the two thresholds, hiding and
# removing tags, the layout switch and Tidy) have no help of their own; their entries stay in the guide.
HELP: dict[str, tuple[str, str]] = {
    "summary.games": (METRIC_REFERENCE, "network-size"),
    "summary.tags": (METRIC_REFERENCE, "network-size"),
    "summary.links": (METRIC_REFERENCE, "network-size"),
    "summary.clusters": (METRIC_REFERENCE, "cluster-labels-and-counts"),
    "summary.q": (METRIC_REFERENCE, "modularity-q"),
    "summary.silhouette": (METRIC_REFERENCE, "mean-silhouette"),
    "quality.q": (METRIC_REFERENCE, "modularity-q"),
    "quality.excess": (METRIC_REFERENCE, "excess-modularity-and-z-score"),
    "quality.coverage": (METRIC_REFERENCE, "coverage-and-inter-cluster-weight-share"),
    "quality.silhouette": (METRIC_REFERENCE, "mean-silhouette"),
    "quality.seed_noise": (METRIC_REFERENCE, "adjusted-rand-index"),
    "quality.sentence": (METRIC_REFERENCE, "clusters-and-partition-quality"),
    "quality.noise_sentence": (METRIC_REFERENCE, "stability"),
    "control.min-months": (APP_CONTROLS, "minimum-months-filter"),
    "control.weight": (APP_CONTROLS, "clustering-weight"),
    "control.algorithm": (APP_CONTROLS, "clustering-algorithm"),
    "control.gamma": (APP_CONTROLS, "resolution-γ"),
    "control.seed": (APP_CONTROLS, "seed"),
    "header.lang": (APP_CONTROLS, "interface-language"),
    "legend.key": (APP_CONTROLS, "reading-the-graph"),
    "legend.one_tag": (APP_CONTROLS, "grey-one-tag-clusters"),
    "legend.thickness": (APP_CONTROLS, "edge-appearance"),
    "connections.ratio": (METRIC_REFERENCE, "connection-ratio"),
    "graph.cluster_map": (APP_CONTROLS, "cluster-map"),
    "connections.share": (METRIC_REFERENCE, "connection-share"),
    "edges.width": (APP_CONTROLS, "width"),
    "edges.scale": (APP_CONTROLS, "scaling"),
    "edges.color": (APP_CONTROLS, "colour"),
    "edges.strength": (APP_CONTROLS, "strength"),
    "edges.between": (APP_CONTROLS, "links-between-clusters"),
    "edges.hide": (APP_CONTROLS, "hide-links-below"),
    "state.n_games": (METRIC_REFERENCE, "network-size"),
    "state.null_replicates": (METRIC_REFERENCE, "null-model-baseline"),
    "state.noise_seeds": (METRIC_REFERENCE, "stability"),
    "export.zip": (CITING, "deposit-the-export-zip"),
}

# The Parameter Selection mode's help: every heatmap metric, Inspector label, Pair Constraint, Selection Setting,
# reason letter and verdict tag, the dataset strip and the mode's actions.
_NA, _RET, _FRAG = "neighbour-agreement", "information-retention", "isolated-share-and-lcc-share"
_ADM, _GHAT = "admissible-partition-and-optimality-domain", "resolution-estimate-and-stable-partition"
_SEL, _RULE = "selected-partition-and-selected-resolution", "pair-constraints-qualifying-pair-and-the-selection-rule"
SELECTION_HELP: dict[str, tuple[str, str]] = {
    "selection.run": (METRIC_REFERENCE, "how-automatic-parameter-selection-works"),
    "selection.apply": (APP_CONTROLS, "apply-to-workbench"),
    "selection.validate": (APP_CONTROLS, "validate-this-pair"),
    "selection.export": (APP_CONTROLS, "export-tables"),
    "selection.dataset_strip": (APP_CONTROLS, "dataset-strip"),
    "selection.heatmap": (APP_CONTROLS, "heatmap-and-reason-letters"),
    "selection.inspector": (APP_CONTROLS, "pair-inspector"),
    "selection.constraints": (APP_CONTROLS, "pair-constraints"),
    "selection.settings": (APP_CONTROLS, "selection-settings"),
    "selection.stability": (METRIC_REFERENCE, "three-kinds-of-stability"),
    "selection.edge_overlap": (METRIC_REFERENCE, "edge-overlap"),
    "selection.metric.neighbour_agreement": (METRIC_REFERENCE, _NA),
    "selection.metric.retention": (METRIC_REFERENCE, _RET),
    "selection.metric.isolated_share": (METRIC_REFERENCE, _FRAG),
    "selection.metric.multi_tag_clusters": (METRIC_REFERENCE, _SEL),
    "selection.metric.seed_noise": (METRIC_REFERENCE, "adjusted-rand-index"),
    "selection.metric.q": (METRIC_REFERENCE, "modularity-q"),
    "selection.inspector.neighbour_agreement": (METRIC_REFERENCE, _NA),
    "selection.inspector.retention": (METRIC_REFERENCE, _RET),
    "selection.inspector.isolated_share": (METRIC_REFERENCE, _FRAG),
    "selection.inspector.lcc_share": (METRIC_REFERENCE, _FRAG),
    "selection.inspector.clusters": (METRIC_REFERENCE, _SEL),
    "selection.inspector.seed_noise": (METRIC_REFERENCE, "adjusted-rand-index"),
    "selection.inspector.hits": (METRIC_REFERENCE, _ADM),
    "selection.inspector.domain": (METRIC_REFERENCE, _ADM),
    "selection.inspector.resolution": (METRIC_REFERENCE, _SEL),
    "selection.inspector.scan_range": (METRIC_REFERENCE, _ADM),
    "selection.inspector.gamma_hat": (METRIC_REFERENCE, _GHAT),
    "selection.inspector.descriptive": (METRIC_REFERENCE, _RULE),
    "selection.inspector.q": (METRIC_REFERENCE, "modularity-q"),
    "selection.inspector.coverage": (METRIC_REFERENCE, "coverage-and-inter-cluster-weight-share"),
    "selection.inspector.silhouette": (METRIC_REFERENCE, "mean-silhouette"),
    "selection.inspector.links": (METRIC_REFERENCE, _NA),
    "selection.inspector.champ": (METRIC_REFERENCE, _ADM),
    "selection.constraint.min_retention": (METRIC_REFERENCE, _RET),
    "selection.constraint.max_isolated_share": (METRIC_REFERENCE, _FRAG),
    "selection.constraint.min_lcc_share": (METRIC_REFERENCE, _FRAG),
    "selection.constraint.min_comparable_neighbours": (METRIC_REFERENCE, _NA),
    "selection.constraint.max_multi_tag_clusters": (METRIC_REFERENCE, _RULE),
    "selection.constraint.tolerance": (METRIC_REFERENCE, _RULE),
    "selection.setting.hidden": (APP_CONTROLS, "selection-settings"),
    "selection.setting.removed": (APP_CONTROLS, "selection-settings"),
    "selection.setting.min_months": (APP_CONTROLS, "minimum-months-filter"),
    "selection.setting.weight": (APP_CONTROLS, "clustering-weight"),
    "selection.setting.min_multi_tag_clusters": (METRIC_REFERENCE, _SEL),
    "selection.reason.P": (METRIC_REFERENCE, _SEL),
    "selection.reason.A": (METRIC_REFERENCE, _NA),
    "selection.reason.N": (METRIC_REFERENCE, _NA),
    "selection.reason.R": (METRIC_REFERENCE, _RET),
    "selection.reason.I": (METRIC_REFERENCE, _FRAG),
    "selection.reason.L": (METRIC_REFERENCE, _FRAG),
    "selection.reason.K": (METRIC_REFERENCE, _RULE),
    "selection.verdict.dissolved": (METRIC_REFERENCE, "subsample-stability"),
    "selection.verdict.q_not_above_null": (METRIC_REFERENCE, "null-comparison"),
    "selection.null": (METRIC_REFERENCE, "null-comparison"),
    "selection.subsample": (METRIC_REFERENCE, "subsample-stability"),
}
HELP.update(SELECTION_HELP)
# The Cluster Comparison mode's help: every figure, label, flag badge, source state, the minimum slider, ⇄ and Export
# CSV, plus Parameter Selection's "Use in Cluster Comparison".
_MATCH, _JACC = "cluster-match-and-comparable-tags", "match-jaccard-and-jaccard-on-comparable-tags"
_GAMES, _FLAGS = "games-in-common-and-games-in-both-clusters", "no-match-flags"
COMPARISON_HELP: dict[str, tuple[str, str]] = {
    "comparison.mode": (APP_CONTROLS, "cluster-comparison-mode"),
    "comparison.how": (METRIC_REFERENCE, "how-a-cluster-comparison-works"),
    "comparison.shared_settings": (APP_CONTROLS, "shared-settings"),
    "comparison.datasets": (APP_CONTROLS, "datasets"),
    "comparison.source.pick": (APP_CONTROLS, "datasets"),
    "comparison.source.cell": (APP_CONTROLS, "datasets"),
    "comparison.source.hand": (APP_CONTROLS, "datasets"),
    "comparison.source.no_run": (APP_CONTROLS, "datasets"),
    "comparison.seed_noise": (METRIC_REFERENCE, "adjusted-rand-index"),
    "comparison.neighbour_agreement": (METRIC_REFERENCE, "neighbour-agreement"),
    "comparison.pairs": (APP_CONTROLS, "dataset-pairs"),
    "comparison.ari": (METRIC_REFERENCE, "ari-on-comparable-tags"),
    "comparison.comparable_tags": (METRIC_REFERENCE, "comparable-tags-coverage"),
    "comparison.games_in_common": (METRIC_REFERENCE, _GAMES),
    "comparison.diagram": (APP_CONTROLS, "link-diagram"),
    "comparison.swap": (APP_CONTROLS, "link-diagram"),
    "comparison.minimum": (APP_CONTROLS, "minimum-similarity-and-flags"),
    "comparison.flag.outside_network": (METRIC_REFERENCE, _FLAGS),
    "comparison.flag.only_one_tag_clusters": (METRIC_REFERENCE, _FLAGS),
    "comparison.flag.below_minimum": (METRIC_REFERENCE, _FLAGS),
    "comparison.match": (METRIC_REFERENCE, _MATCH),
    "comparison.match_jaccard": (METRIC_REFERENCE, _JACC),
    "comparison.comparable_jaccard": (METRIC_REFERENCE, _JACC),
    "comparison.share": (METRIC_REFERENCE, "shared-share"),
    "comparison.overlap": (METRIC_REFERENCE, "overlap-vs-expected"),
    "comparison.tag_groups": (METRIC_REFERENCE, _FLAGS),
    "comparison.detail": (APP_CONTROLS, "match-detail"),
    "comparison.games": (APP_CONTROLS, "games-in-both-clusters"),
    "comparison.comparison_id": (METRIC_REFERENCE, "comparison-state-and-comparisonid"),
    "comparison.export": (APP_CONTROLS, "export-csv"),
    "selection.use_in_comparison": (APP_CONTROLS, "use-in-cluster-comparison"),
}
HELP.update(COMPARISON_HELP)
# The draft dialog's settings (repository only): hover shows the chapter-3 entry's In short, a click opens it.
DRAFT_HELP: dict[str, tuple[str, str]] = {
    "draft.list_size": (METRIC_REFERENCE, "list-size"),
    "draft.tag_depth": (METRIC_REFERENCE, "tags-per-game-tag-depth"),
    "draft.defining_tag": (METRIC_REFERENCE, "defining-tag"),
    "draft.eligible_pool": (METRIC_REFERENCE, "eligible-pool-baseline"),
    "draft.exclusions": (METRIC_REFERENCE, "exclusions-and-would-be-ranks"),
}
HELP.update(DRAFT_HELP)

# (declared file, column name), as in `view.INSPECTOR_LABELS`
Columns = Iterable[tuple[str, str]]


# One tooltip line: (kind, text).
TipLine = tuple[str, str]


def tip_lines(entry: tuple[str, str], tx: Text, now: str | None = None,
              last: TipLine | None = None) -> list[TipLine]:
    """An entry's In short lines in the translator's language, then the optional Now line and last line."""
    lines = list(in_short_at(tx.lang, *entry))
    if now:
        lines.append(("now", now))
    if last:
        lines.append(last)
    return lines


def tip_json(lines: list[TipLine]) -> str:
    """The lines as `data-tip` carries them (workbench.js `showTip`)."""
    return json.dumps([list(line) for line in lines], ensure_ascii=False)


def tip_text(lines: list[TipLine], tx: Text) -> str:
    """The lines as plain text, each with its label (ag-grid's own header tooltip)."""
    return "\n".join(f"{LABELS[tx.lang][kind]} {text}" for kind, text in lines)


def _tip(entry: tuple[str, str], tx: Text, now: str | None = None, last: TipLine | None = None) -> str:
    return tip_json(tip_lines(entry, tx, now, last))


def _target(entry: tuple[str, str]) -> str:
    file, anchor = entry
    return f"{file}#{anchor}"


def tip(key: str, tx: Text, now: str | None = None, last: TipLine | None = None) -> str:
    """The tooltip (`data-tip`): one line per In short line, then the optional Now line and last line."""
    return _tip(HELP[key], tx, now, last)


def target(key: str) -> str:
    """Where a click opens the help modal: `<guide file>#<anchor>`."""
    return _target(HELP[key])


def attrs(key: str, tx: Text, now: str | None = None, last: TipLine | None = None) -> dict[str, Any]:
    """The data attributes that give a Dash component both help layers (workbench.js reads them)."""
    return {"data-tip": tip(key, tx, now, last), "data-help": target(key)}


# Columns that identify or label a row have no help of their own (spec: identifier columns are out of scope): those
# of the ids-and-names entry, tag id lists, and row labels that the schema files under a metric's entry.
IDENTIFIERS_ENTRY = "identifiers-names-and-lists"
ROW_LABELS = frozenset({"source_cluster", "target_cluster", "is_intra_cluster", "appids", "cluster_a", "cluster_b",
                        "seed", "replicate", "noise_seed_index"})


def column_has_help(column: tuple[str, str]) -> bool:
    """Whether an export column (file, name) measures something with its own guide entry."""
    file, name = column
    entry = S.file(file).column(name).guide_entry
    return (entry not in (None, IDENTIFIERS_ENTRY) and name not in ROW_LABELS
            and not name.endswith(("tag_id", "tag_ids")))


def column_entry(columns: Columns) -> tuple[str, str]:
    """The guide entry of a label shown for export columns: the first column's, from the export schema."""
    file, name = next(iter(columns))
    entry = S.file(file).column(name).guide_entry
    if entry is None:
        raise ValueError(f"{name} in {file} has no guide entry")
    return METRIC_REFERENCE, entry


def column_line(columns: Columns, tx: Text) -> TipLine:
    """The column line: ("column", "name (file)"), or ("columns", "a, b (file); c (other file)"). Column and file
    names stay English in every language; only the label is the language's."""
    by_file: dict[str, list[str]] = {}
    for file, name in columns:
        by_file.setdefault(file.split("/")[-1], []).append(name)
    names = "; ".join(f"{', '.join(names)} ({file})" for file, names in by_file.items())
    return ("column" if sum(map(len, by_file.values())) == 1 else "columns"), names


def column_help(columns: Columns, tx: Text) -> tuple[list[TipLine], str]:
    """Both help layers for a label or header shown for export columns: the tooltip lines (its entry's In short,
    then the column names) and where a click opens the help modal."""
    columns = list(columns)
    entry = column_entry(columns)
    return tip_lines(entry, tx, last=column_line(columns, tx)), _target(entry)


def column_attrs(columns: Columns, tx: Text) -> dict[str, str]:
    """`column_help` as the data attributes workbench.js reads."""
    lines, target_ = column_help(columns, tx)
    return {"data-tip": tip_json(lines), "data-help": target_}

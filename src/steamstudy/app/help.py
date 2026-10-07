"""Two-layer help for the app's metrics and analytical controls (spec: .scratch/metric-help/spec.md).

Layer 1 is the In short block of the element's User Guide entry: workbench.js shows it as a tooltip on hover or
keyboard focus. Layer 2 is the whole entry, which a click opens in the help modal. The guide is the only source
of the text; the app adds at most one "Now:" line of live values, and a label shown for export columns names them.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from steamstudy.app.guide import in_short_at
from steamstudy.export import schema as S

METRIC_REFERENCE = "03-metric-reference.md"

# help key -> (guide file, heading anchor)
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
}

# (declared file, column name), as in `view.INSPECTOR_LABELS`
Columns = Iterable[tuple[str, str]]


def _tip(entry: tuple[str, str], now: str | None = None, last: str | None = None) -> str:
    lines = [f"{label} {text}" for label, text in in_short_at(*entry)]
    if now:
        lines.append(f"Now: {now}")
    if last:
        lines.append(last)
    return "\n".join(lines)


def _target(entry: tuple[str, str]) -> str:
    file, anchor = entry
    return f"{file}#{anchor}"


def tip(key: str, now: str | None = None) -> str:
    """The tooltip text: one labelled line per In short line, then the optional Now line."""
    return _tip(HELP[key], now)


def target(key: str) -> str:
    """Where a click opens the help modal: `<guide file>#<anchor>`."""
    return _target(HELP[key])


def attrs(key: str, now: str | None = None) -> dict[str, Any]:
    """The data attributes that give a Dash component both help layers (workbench.js reads them)."""
    return {"data-tip": tip(key, now), "data-help": target(key)}


def column_entry(columns: Columns) -> tuple[str, str]:
    """The guide entry of a label shown for export columns: the first column's, from the export schema."""
    file, name = next(iter(columns))
    entry = S.file(file).column(name).guide_entry
    if entry is None:
        raise ValueError(f"{name} in {file} has no guide entry")
    return METRIC_REFERENCE, entry


def column_line(columns: Columns) -> str:
    """"Column: name (file)", or "Columns: a, b (file); c (other file)" (workbench.js styles the line)."""
    by_file: dict[str, list[str]] = {}
    for file, name in columns:
        by_file.setdefault(file.split("/")[-1], []).append(name)
    names = "; ".join(f"{', '.join(names)} ({file})" for file, names in by_file.items())
    return f"{'Column' if sum(map(len, by_file.values())) == 1 else 'Columns'}: {names}"


def column_attrs(columns: Columns) -> dict[str, str]:
    """Both help layers for a label shown for export columns: its entry's In short, then the column names."""
    columns = list(columns)
    entry = column_entry(columns)
    return {"data-tip": _tip(entry, last=column_line(columns)), "data-help": _target(entry)}

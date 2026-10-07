"""Two-layer help for the app's metrics and analytical controls (spec: .scratch/metric-help/spec.md).

Layer 1 is the In short block of the element's User Guide entry: workbench.js shows it as a tooltip on hover or
keyboard focus. Layer 2 is the whole entry, which a click opens in the help modal. The guide is the only source
of the text; the app adds at most one "Now:" line of live values.
"""

from __future__ import annotations

from typing import Any

from steamstudy.app.guide import in_short_at

METRIC_REFERENCE = "03-metric-reference.md"

# help key -> (guide file, heading anchor)
HELP: dict[str, tuple[str, str]] = {
    "summary.games": (METRIC_REFERENCE, "network-size"),
    "summary.tags": (METRIC_REFERENCE, "network-size"),
    "summary.links": (METRIC_REFERENCE, "network-size"),
    "summary.clusters": (METRIC_REFERENCE, "cluster-labels-and-counts"),
    "summary.q": (METRIC_REFERENCE, "modularity-q"),
    "summary.silhouette": (METRIC_REFERENCE, "mean-silhouette"),
}


def tip(key: str, now: str | None = None) -> str:
    """The tooltip text: one labelled line per In short line, then the optional Now line."""
    lines = [f"{label} {text}" for label, text in in_short_at(*HELP[key])]
    if now:
        lines.append(f"Now: {now}")
    return "\n".join(lines)


def target(key: str) -> str:
    """Where a click opens the help modal: `<guide file>#<anchor>`."""
    file, anchor = HELP[key]
    return f"{file}#{anchor}"


def attrs(key: str, now: str | None = None) -> dict[str, Any]:
    """The data attributes that give a Dash component both help layers (workbench.js reads them)."""
    return {"data-tip": tip(key, now), "data-help": target(key)}

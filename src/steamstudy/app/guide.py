"""In-app help: each panel's `?` opens the matching User Guide section, rendered offline with dcc.Markdown.

The guide files are the repository's `docs/user-guide/*.md`, shipped as package data (`steamstudy/guide/`).
"""

from __future__ import annotations

import re
from pathlib import Path

# panel -> (guide file, heading anchor)
PANEL_SECTIONS: dict[str, tuple[str, str]] = {
    "controls": ("02-app-controls.md", "control-reference"),
    "dataset": ("01-getting-started.md", "load-a-dataset"),
    "filters": ("03-metric-reference.md", "tags-not-in-the-network"),
    "network": ("03-metric-reference.md", "the-tag-network"),
    "inspector": ("01-getting-started.md", "inspect-a-node-an-edge-or-a-cluster"),
    "quality": ("03-metric-reference.md", "clusters-and-partition-quality"),
    "clusters": ("03-metric-reference.md", "cluster-center"),
    "removal": ("03-metric-reference.md", "removal-sensitivity"),
    "nodes": ("04-files.md", "nodescsv"),
    "edges": ("04-files.md", "edgescsv"),
    "export": ("05-citing-and-reproducing.md", "citing-and-reproducing-a-network-state"),
}


def guide_dir() -> Path:
    packaged = Path(__file__).resolve().parents[1] / "guide"
    if packaged.is_dir():
        return packaged
    return Path(__file__).resolve().parents[3] / "docs" / "user-guide"


def slug(heading: str) -> str:
    """GitHub-style heading anchor."""
    text = heading.strip().lower()
    text = re.sub(r"[`*_]", "", text)
    text = re.sub(r"[^\w\- ]", "", text)
    return text.replace(" ", "-")


def headings(markdown: str) -> list[tuple[int, str, str]]:
    """(level, text, anchor) of every Markdown heading."""
    out = []
    for line in markdown.splitlines():
        m = re.match(r"^(#{1,6})\s+(.*?)\s*#*\s*$", line)
        if m:
            out.append((len(m.group(1)), m.group(2), slug(m.group(2))))
    return out


def section(markdown: str, anchor: str) -> str | None:
    """The section under the heading with this anchor, up to the next heading of the same or a higher level."""
    lines = markdown.splitlines()
    start, level = None, 0
    for i, line in enumerate(lines):
        m = re.match(r"^(#{1,6})\s+(.*?)\s*#*\s*$", line)
        if not m:
            continue
        if start is None and slug(m.group(2)) == anchor:
            start, level = i, len(m.group(1))
        elif start is not None and len(m.group(1)) <= level:
            return "\n".join(lines[start:i])
    return "\n".join(lines[start:]) if start is not None else None


def help_markdown(panel: str) -> str:
    file, anchor = PANEL_SECTIONS.get(panel, ("00-three-rules.md", "three-rules"))
    path = guide_dir() / file
    if not path.is_file():
        return f"The User Guide file {file} is not installed."
    text = section(path.read_text(encoding="utf-8"), anchor)
    return text if text is not None else f"Section #{anchor} not found in {file}."

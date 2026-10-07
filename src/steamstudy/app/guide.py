"""In-app help: each panel's `?` opens the matching User Guide section, rendered offline with dcc.Markdown, and
each metric's In short block is its tooltip (see `steamstudy.app.help`). Guide links inside the modal open their
target entry there.

The guide files are the repository's `docs/user-guide/*.md`, shipped as package data (`steamstudy/guide/`).
"""

from __future__ import annotations

import re
from functools import lru_cache
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


@lru_cache(maxsize=None)
def chapter(file: str) -> str | None:
    """A guide chapter's Markdown, read once per process."""
    path = guide_dir() / file
    return path.read_text(encoding="utf-8") if path.is_file() else None


def first_section(markdown: str) -> str:
    """A chapter's opening: its title and introduction with the first `##` section, up to the second."""
    lines = markdown.splitlines()
    starts = [i for i, line in enumerate(lines) if re.match(r"^#{1,2}\s", line)]
    return "\n".join(lines[:starts[2]] if len(starts) > 2 else lines)


# ----------------------------------------------------------------------------- links inside the help modal

# An in-guide link shown in the modal points here, followed by its target (`<file>#<anchor>` or `<file>`):
# workbench.js opens that entry in the modal instead of following the link.
HELP_LINK = "#help:"
# A Markdown link: (`[text]`, href)
LINK = re.compile(r"(\[[^\]]*\])\(([^)\s]+)\)")


def resolve_link(href: str, file: str) -> str | None:
    """Where an in-guide link opens in the modal, as `<file>#<anchor>` or `<file>`; None for any other link."""
    if href.startswith("#"):
        return file + href
    path, _, anchor = href.partition("#")
    if not re.fullmatch(r"[\w.-]+\.md", path):
        return None
    return f"{path}#{anchor}" if anchor else path


def modal_links(markdown: str, file: str) -> str:
    """The Markdown with every in-guide link pointed at the modal; other links stay as they are."""
    def point(m: re.Match) -> str:
        target = resolve_link(m.group(2), file)
        return m.group(0) if target is None else f"{m.group(1)}({HELP_LINK}{target})"
    return LINK.sub(point, markdown)


def help_markdown_at(file: str, anchor: str | None = None) -> str:
    """The guide section under one heading (the chapter's first section without one), for the help modal."""
    text = chapter(file)
    if text is None:
        return f"The User Guide file {file} is not installed."
    found = section(text, anchor) if anchor else first_section(text)
    if found is None:
        return f"Section #{anchor} not found in {file}."
    return modal_links(found, file)


def help_markdown(panel: str) -> str:
    return help_markdown_at(*PANEL_SECTIONS.get(panel, ("00-three-rules.md", "three-rules")))


# ----------------------------------------------------------------------------- In short (the tooltip layer)

# An entry's In short block: a blockquote right under its heading, one labelled line per paragraph, in this order.
IN_SHORT_LABELS = ("In short.", "Higher →", "Lower →", "Raising it →", "Here:", "Caution:")
_LABEL_ORDER = {"In short.": 0, "Higher →": 1, "Lower →": 1, "Raising it →": 1, "Here:": 2, "Caution:": 3}
IN_SHORT_MAX_WORDS = 60


def plain(markdown: str) -> str:
    """Inline Markdown as plain text: links keep their text; emphasis and code marks go."""
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", markdown)
    return re.sub(r"[`*_]", "", text).strip()


def in_short(entry: str) -> list[tuple[str, str]]:
    """The (label, text) lines of the In short block that opens an entry, or [] if it has none.

    The block is the first blockquote after the heading, before any other paragraph."""
    lines = entry.splitlines()[1:]
    while lines and not lines[0].strip():
        lines.pop(0)
    quote = []
    for line in lines:
        if not line.startswith(">"):
            break
        quote.append(line[1:].strip())
    out = []
    for para in " ".join(q if q else "\n" for q in quote).split("\n"):
        m = re.match(r"^\*\*(.+?)\*\*\s*(.*)$", para.strip())
        if m and m.group(1) in IN_SHORT_LABELS:
            out.append((m.group(1), plain(m.group(2))))
    return out


@lru_cache(maxsize=None)
def in_short_at(file: str, anchor: str) -> tuple[tuple[str, str], ...]:
    """An entry's In short lines, read once per process (the Inspector asks on every selection)."""
    text = chapter(file)
    entry = section(text, anchor) if text is not None else None
    return tuple(in_short(entry)) if entry else ()


def in_short_problems(lines: list[tuple[str, str]]) -> list[str]:
    """What breaks the In short form: no first line, labels out of order or repeated, over the word cap."""
    problems = []
    if not lines or lines[0][0] != "In short.":
        problems.append("does not open with 'In short.'")
    order = [_LABEL_ORDER[label] for label, _ in lines]
    if order != sorted(set(order)):
        problems.append(f"labels out of order or repeated: {[label for label, _ in lines]}")
    words = sum(len(text.split()) for _, text in lines)
    if words > IN_SHORT_MAX_WORDS:
        problems.append(f"{words} words, over {IN_SHORT_MAX_WORDS}")
    return problems

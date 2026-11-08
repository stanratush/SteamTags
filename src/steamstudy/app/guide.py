"""In-app help: each panel's `?` opens the matching User Guide section, rendered offline with dcc.Markdown, and
each metric's In short block is its tooltip (see `steamstudy.app.help`). Guide links inside the modal open their
target entry there.

The guide files are the repository's `docs/user-guide/*.md`, shipped as package data (`steamstudy/guide/`), and
their Bulgarian copy in `bg/` with the same file names. A Bulgarian heading ends with `{#<english-slug>}`, so every
anchor, help key and in-guide link is the same in both languages. A Bulgarian file, `##` section or anchor that is
not written yet falls back to the English one.
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
    # The Build menu and the draft dialog (repository only): each draft step's `?` opens its chapter-7 section.
    "build-menu": ("07-making-builds.md", "the-build-tree"),
    "import": ("08-imported-data.md", "making-an-import"),
    "draft-start": ("07-making-builds.md", "draft-start"),
    "draft-top_n": ("07-making-builds.md", "draft-top-n"),
    "draft-curation": ("07-making-builds.md", "draft-curation"),
    "draft-reports": ("07-making-builds.md", "draft-reports"),
    "draft-network": ("07-making-builds.md", "draft-network-defaults"),
    "draft-review": ("07-making-builds.md", "draft-review"),
}


def guide_dir(lang: str = "en") -> Path:
    """The folder of the guide in `lang`: the English guide, or its `bg/` copy."""
    packaged = Path(__file__).resolve().parents[1] / "guide"
    base = packaged if packaged.is_dir() else Path(__file__).resolve().parents[3] / "docs" / "user-guide"
    return base if lang == "en" else base / lang


def slug(heading: str) -> str:
    """GitHub-style heading anchor."""
    text = heading.strip().lower()
    text = re.sub(r"[`*_]", "", text)
    text = re.sub(r"[^\w\- ]", "", text)
    return text.replace(" ", "-")


_HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
_ID = re.compile(r"^(.*?)\s*\{#([^}\s]+)\}$")


def heading(line: str) -> tuple[int, str, str] | None:
    """(level, shown text, anchor) of a Markdown heading line: an explicit `{#id}` is the anchor and is not shown;
    otherwise the anchor is the text's slug."""
    m = _HEADING.match(line)
    if not m:
        return None
    text = m.group(2)
    explicit = _ID.match(text)
    if explicit:
        return len(m.group(1)), explicit.group(1), explicit.group(2)
    return len(m.group(1)), text, slug(text)


def headings(markdown: str) -> list[tuple[int, str, str]]:
    """(level, text, anchor) of every Markdown heading."""
    return [h for h in map(heading, markdown.splitlines()) if h]


# An anchor kept after its heading was renamed: code, help keys and in-guide links that use it still resolve.
ALIASES = {"edge-thickness": "edge-appearance"}


def section(markdown: str, anchor: str) -> str | None:
    """The section under the heading with this anchor, up to the next heading of the same or a higher level (an
    `ALIASES` anchor gives its heading's section)."""
    lines = markdown.splitlines()
    start, level = None, 0
    for i, line in enumerate(lines):
        h = heading(line)
        if not h:
            continue
        if start is None and h[2] == anchor:
            start, level = i, h[0]
        elif start is not None and h[0] <= level:
            return "\n".join(lines[start:i])
    if start is None:
        return section(markdown, ALIASES[anchor]) if anchor in ALIASES else None
    return "\n".join(lines[start:])


def shown(markdown: str) -> str:
    """The Markdown as the modal shows it: headings without their `{#id}`."""
    return "\n".join(re.sub(r"\s*\{#[^}\s]+\}\s*$", "", line) if heading(line) else line
                     for line in markdown.splitlines())


def _sections(markdown: str) -> tuple[str, list[tuple[str, str]]]:
    """A chapter as its preamble (title and introduction) and its `##` sections, (anchor, text), in order."""
    lines = markdown.splitlines()
    cuts = [(i, h[2]) for i, h in ((i, heading(line)) for i, line in enumerate(lines)) if h and h[0] == 2]
    if not cuts:
        return markdown, []
    bounds = [i for i, _ in cuts] + [len(lines)]
    return ("\n".join(lines[:cuts[0][0]]),
            [(anchor, "\n".join(lines[bounds[k]:bounds[k + 1]])) for k, (_, anchor) in enumerate(cuts)])


def splice(translated: str, english: str) -> str:
    """A partly translated chapter: the English chapter's `##` sections in their order, each translated one in place
    of its English text. The translated title and introduction are used once it has a title of its own."""
    pre, done = _sections(translated)
    en_pre, en_parts = _sections(english)
    have = dict(done)
    if not any(h and h[0] == 1 for h in map(heading, pre.splitlines())):
        pre = en_pre
    return "\n".join([pre, *(have.get(anchor, text) for anchor, text in en_parts)])


def _read(lang: str, file: str) -> str | None:
    path = guide_dir(lang) / file
    return path.read_text(encoding="utf-8") if path.is_file() else None


@lru_cache(maxsize=None)
def chapter(lang: str, file: str) -> str | None:
    """A guide chapter's Markdown in `lang`, read once per process: English wherever the translation is missing."""
    english = _read("en", file)
    if lang == "en":
        return english
    translated = _read(lang, file)
    if translated is None or english is None:
        return translated or english
    return splice(translated, english)


def first_section(markdown: str) -> str:
    """A chapter's opening: its title and introduction with the first `##` section, up to the second."""
    lines = markdown.splitlines()
    starts = [i for i, line in enumerate(lines) if re.match(r"^#{1,2}\s", line)]
    return "\n".join(lines[:starts[2]] if len(starts) > 2 else lines)


def entry_at(lang: str, file: str, anchor: str) -> str | None:
    """The section under one anchor in `lang`, or the English one where the translation has none."""
    for each in dict.fromkeys((lang, "en")):
        text = chapter(each, file)
        found = section(text, anchor) if text is not None else None
        if found is not None:
            return found
    return None


# ----------------------------------------------------------------------------- links inside the help modal

# An in-guide link shown in the modal points here, followed by its target (`<file>#<anchor>` or `<file>`):
# workbench.js opens that entry in the modal instead of following the link. Targets are the same in every
# language: the modal opens them in the language shown.
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


def help_markdown_at(lang: str, file: str, anchor: str | None = None) -> str:
    """The guide section under one heading (the chapter's first section without one), for the help modal."""
    text = chapter(lang, file)
    if text is None:
        return f"The User Guide file {file} is not installed."
    found = entry_at(lang, file, anchor) if anchor else first_section(text)
    if found is None:
        return f"Section #{anchor} not found in {file}."
    return modal_links(shown(found), file)


def help_markdown(lang: str, panel: str) -> str:
    return help_markdown_at(lang, *PANEL_SECTIONS.get(panel, ("00-three-rules.md", "three-rules")))


# ----------------------------------------------------------------------------- In short (the tooltip layer)

# The labels of an entry's In short block (a blockquote right under its heading, one labelled line per paragraph, in
# this order), of a tooltip's other lines, and the entry markers, per language. Kinds are the same in every language;
# the Bulgarian words are the term table's Guide labels (docs/i18n/bg-terms.md).
IN_SHORT_KINDS = ("in_short", "higher", "lower", "raising", "here", "caution")
LABELS: dict[str, dict[str, str]] = {
    "en": {"in_short": "In short.", "higher": "Higher →", "lower": "Lower →", "raising": "Raising it →",
           "here": "Here:", "caution": "Caution:", "now": "Now:", "column": "Column:", "columns": "Columns:",
           "field": "Field:"},
    "bg": {"in_short": "Накратко.", "higher": "По-високо →", "lower": "По-ниско →", "raising": "При повишаване →",
           "here": "Тук:", "caution": "Внимание:", "now": "Сега:", "column": "Колона:", "columns": "Колони:",
           "field": "Поле:"},
}
MARKERS: dict[str, dict[str, str]] = {
    "en": {"why": "Why it matters here", "exact": "Exact definition", "example": "Example", "bounds": "Bounds",
           "compare": "Compare with", "caution": "Caution", "shown": "Shown in the app as",
           "steam_only": "Steam Builds only"},
    "bg": {"why": "Защо има значение тук", "exact": "Точна дефиниция", "example": "Пример", "bounds": "Граници",
           "compare": "Сравнете с", "caution": "Внимание", "shown": "В приложението се показва като",
           "steam_only": "Само за компилации от Steam"},
}
_ORDER = {"in_short": 0, "higher": 1, "lower": 1, "raising": 1, "here": 2, "caution": 3}
IN_SHORT_LABELS = tuple(LABELS["en"][kind] for kind in IN_SHORT_KINDS)
IN_SHORT_MAX_WORDS = 60


def plain(markdown: str) -> str:
    """Inline Markdown as plain text: links keep their text; emphasis and code marks go."""
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", markdown)
    # code spans keep their underscores (`layout_source`); elsewhere only emphasis marks go, not snake_case
    parts = re.split(r"(`[^`]*`)", text)
    return "".join(p[1:-1] if p.startswith("`") else re.sub(r"\*|(?<!\w)_|_(?!\w)", "", p) for p in parts).strip()


def _in_short(entry: str, kinds: dict[str, str]) -> list[tuple[str, str]]:
    """(label, text) of the In short block's lines whose label is a key of `kinds`."""
    lines = entry.splitlines()[1:]
    while lines and not lines[0].strip():
        lines.pop(0)
    if lines and re.fullmatch(r"\*[^*]+\.\*", lines[0].strip()):  # a line such as "*Steam Builds only.*"
        lines.pop(0)
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
        if m and m.group(1) in kinds:
            out.append((m.group(1), plain(m.group(2))))
    return out


def _kinds(lang: str) -> dict[str, str]:
    """In short label -> kind, for one language."""
    return {LABELS[lang][kind]: kind for kind in IN_SHORT_KINDS}


def in_short(entry: str, lang: str = "en") -> list[tuple[str, str]]:
    """The (label, text) lines of the In short block that opens an entry, in the language's labels, or [] if it has
    none. The block is the first blockquote after the heading, before any other paragraph."""
    return _in_short(entry, _kinds(lang))


@lru_cache(maxsize=None)
def in_short_at(lang: str, file: str, anchor: str) -> tuple[tuple[str, str], ...]:
    """An entry's In short lines as (kind, text), read once per process (the Inspector asks on every selection).
    An entry not translated yet gives its English lines."""
    entry = entry_at(lang, file, anchor)
    if not entry:
        return ()
    either = {**_kinds("en"), **_kinds(lang)}
    return tuple((either[label], text) for label, text in _in_short(entry, either))


def in_short_problems(lines: list[tuple[str, str]], lang: str = "en") -> list[str]:
    """What breaks the In short form: no first line, labels out of order or repeated, over the word cap."""
    problems = []
    kinds = _kinds(lang)
    if not lines or kinds.get(lines[0][0]) != "in_short":
        problems.append(f"does not open with {LABELS[lang]['in_short']!r}")
    order = [_ORDER[kinds[label]] for label, _ in lines if label in kinds]
    if order != sorted(set(order)) or len(order) != len(lines):
        problems.append(f"labels out of order or repeated: {[label for label, _ in lines]}")
    words = sum(len(text.split()) for _, text in lines)
    if words > IN_SHORT_MAX_WORDS:
        problems.append(f"{words} words, over {IN_SHORT_MAX_WORDS}")
    return problems

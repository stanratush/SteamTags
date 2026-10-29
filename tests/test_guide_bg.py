"""The Bulgarian User Guide (`docs/user-guide/bg/`): structure parity with the English guide, and the lookups that
fall back to English (spec: .scratch/bilingual-cluster-views/spec.md, "The Bulgarian User Guide", "Tests").

Every English file has a Bulgarian twin, every English heading has a twin at the same level with the same In short
labels and entry markers, every Bulgarian heading carries an English `{#id}`, and every in-guide link resolves. (The app
still splices English into any gap at runtime; the tests leave none.)
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from conftest import REPO
from steamstudy.app import guide as G

EN = REPO / "docs" / "user-guide"
BG = EN / "bg"

# An entry's markers, by kind: how each language writes it (guide.MARKERS) inside the entry's own text.
MARKER_FORMS = {"why": "*{}.*", "exact": "**{}:**", "example": "*{}.*", "bounds": "*{}.*", "compare": "*{}.*",
                "caution": "*{}.*", "shown": "{}"}


def _own(markdown: str, anchor: str) -> str:
    """A heading's own text: from it to the next heading of any level."""
    lines = markdown.splitlines()
    start = next(i for i, line in enumerate(lines) if (h := G.heading(line)) and h[2] == anchor)
    end = next((i for i in range(start + 1, len(lines)) if G.heading(lines[i])), len(lines))
    return "\n".join(lines[start:end])


def _markers(text: str, lang: str) -> dict[str, int]:
    return {kind: text.count(form.format(G.MARKERS[lang][kind])) for kind, form in MARKER_FORMS.items()}


def _shape(markdown: str, lang: str) -> list[tuple[int, str, tuple[str, ...], dict[str, int]]]:
    """Each heading as (level, anchor, its In short kinds, its markers), in order."""
    kinds = {G.LABELS[lang][k]: k for k in G.IN_SHORT_KINDS}
    out = []
    for level, _, anchor in G.headings(markdown):
        own = _own(markdown, anchor)
        out.append((level, anchor, tuple(kinds[label] for label, _ in G.in_short(own, lang)), _markers(own, lang)))
    return out


def problems(en_dir: Path, bg_dir: Path) -> list[str]:
    """What breaks the Bulgarian guide's structure against the English one."""
    out = []
    english = {p.name: p.read_text(encoding="utf-8") for p in en_dir.glob("*.md")}
    en_anchors = {name: {(level, anchor) for level, _, anchor in G.headings(text)} for name, text in english.items()}
    translated = {p.name: p.read_text(encoding="utf-8") for p in bg_dir.glob("*.md")} if bg_dir.is_dir() else {}
    for name, text in translated.items():
        if name not in english:
            out.append(f"bg/{name}: no English file of that name")
            continue
        for line in text.splitlines():
            h = G.heading(line)
            if h is None:
                continue
            if not re.search(r"\{#[^}\s]+\}\s*$", line):
                out.append(f"bg/{name}: heading without an {{#id}}: {line!r}")
            elif (h[0], h[2]) not in en_anchors[name]:
                out.append(f"bg/{name}: {{#{h[2]}}} is no English heading at level {h[0]}")
        for _, href in G.LINK.findall(text):
            target = G.resolve_link(href, name)
            if target is None:
                continue
            file, _, anchor = target.partition("#")
            anchor = G.ALIASES.get(anchor, anchor)  # a renamed heading's old anchor resolves, as in the app
            if file not in english or (anchor and anchor not in {a for _, a in en_anchors[file]}):
                out.append(f"bg/{name}: link {href} resolves to no English heading")
    for file, en_text in sorted(english.items()):
        if file not in translated:
            out.append(f"{file}: no Bulgarian file bg/{file}")
            continue
        en_shape = {(level, anchor): rest for level, anchor, *rest in _shape(en_text, "en")}
        bg_shape = {(level, anchor): rest for level, anchor, *rest in _shape(translated[file], "bg")}
        for key, (kinds, markers) in en_shape.items():
            if key not in bg_shape:
                out.append(f"{file}: no Bulgarian twin of {{#{key[1]}}} at level {key[0]}")
                continue
            bg_kinds, bg_markers = bg_shape[key]
            if bg_kinds != kinds:
                out.append(f"{file}: {{#{key[1]}}} In short labels {bg_kinds}, English has {kinds}")
            if bg_markers != markers:
                out.append(f"{file}: {{#{key[1]}}} markers {bg_markers}, English has {markers}")
    return out


def test_the_bulgarian_guide_keeps_the_english_structure():
    assert problems(EN, BG) == []


# ----------------------------------------------------------------------------- fixtures

ENGLISH = """# Metrics

Intro.

## Size

### Lift

> **In short.** How often two tags meet.
>
> **Caution:** rare tags.

Text. *Why it matters here.* Because. See [Q](#modularity-q).

**Exact definition:** w.

### Modularity Q

> **In short.** Q.

*Why it matters here.* Q matters.

## Other

### Seed

> **In short.** The seed.
"""

BULGARIAN = """# Метрики {#metrics}

Въведение.

## Размер {#size}

### Лифт (Lift) {#lift}

> **Накратко.** Колко често се срещат два тага.
>
> **Внимание:** редки тагове.

Текст. *Защо има значение тук.* Защото. Вижте [Q](#modularity-q).

**Точна дефиниция:** w.
"""


@pytest.fixture
def guide(tmp_path, monkeypatch):
    en, bg = tmp_path / "en", tmp_path / "en" / "bg"
    bg.mkdir(parents=True)
    (en / "03-metric-reference.md").write_text(ENGLISH, encoding="utf-8")
    (bg / "03-metric-reference.md").write_text(BULGARIAN, encoding="utf-8")
    monkeypatch.setattr(G, "guide_dir", lambda lang="en": en if lang == "en" else en / lang)
    G.chapter.cache_clear()
    G.in_short_at.cache_clear()
    yield en, bg
    G.chapter.cache_clear()
    G.in_short_at.cache_clear()


def test_a_bulgarian_heading_id_is_its_anchor_and_is_not_shown(guide):
    assert G.heading("### Лифт (Lift) {#lift}") == (3, "Лифт (Lift)", "lift")
    assert G.heading("### Modularity Q") == (3, "Modularity Q", "modularity-q")
    entry = G.section(G.chapter("bg", "03-metric-reference.md"), "lift")
    assert entry.startswith("### Лифт (Lift) {#lift}") and "Модул" not in entry
    shown = G.help_markdown_at("bg", "03-metric-reference.md", "lift")
    assert shown.startswith("### Лифт (Lift)\n") and "{#" not in shown
    assert f"({G.HELP_LINK}03-metric-reference.md#modularity-q)" in shown  # links keep their English target


def test_bulgarian_in_short_lines_read_with_the_bulgarian_labels(guide):
    assert G.in_short_at("bg", "03-metric-reference.md", "lift") == (
        ("in_short", "Колко често се срещат два тага."), ("caution", "редки тагове."))
    assert G.in_short_at("en", "03-metric-reference.md", "lift")[0] == ("in_short", "How often two tags meet.")
    entry = G.section(BULGARIAN, "lift")
    assert G.in_short_problems(G.in_short(entry, "bg"), "bg") == []
    assert G.in_short(entry, "en") == []  # each language reads its own labels


def test_a_missing_bulgarian_entry_falls_back_to_english(guide):
    # "modularity-q" sits in a translated ## section that lacks it; "seed" in a ## section not translated yet
    assert G.help_markdown_at("bg", "03-metric-reference.md", "modularity-q").startswith("### Modularity Q")
    assert G.in_short_at("bg", "03-metric-reference.md", "seed") == (("in_short", "The seed."),)
    assert G.help_markdown_at("bg", "04-files.md").startswith("The User Guide file")  # no file in either language


def test_a_partial_chapter_splices_english_sections_into_the_gaps_in_order(guide):
    text = G.chapter("bg", "03-metric-reference.md")
    order = [anchor for level, _, anchor in G.headings(text) if level <= 2]
    assert order == ["metrics", "size", "other"]
    assert "## Размер {#size}" in text and "## Other" in text and text.startswith("# Метрики")


def test_a_missing_bulgarian_file_reads_as_english(guide):
    en, bg = guide
    (en / "06-known-limitations.md").write_text("# Known limitations\n\n## A\n\nText.\n", encoding="utf-8")
    assert G.chapter("bg", "06-known-limitations.md") == G.chapter("en", "06-known-limitations.md")


def test_a_bulgarian_stub_without_a_title_keeps_the_english_opening(guide):
    en, bg = guide
    (en / "README.md").write_text("# User Guide\n\nRead this first.\n", encoding="utf-8")
    (bg / "README.md").write_text("Being written; English is shown in its place.\n", encoding="utf-8")
    assert G.chapter("bg", "README.md") == G.chapter("en", "README.md")


def test_the_parity_check_fails_on_a_missing_heading_or_file(guide):
    en, bg = guide
    assert problems(en, bg) == ["03-metric-reference.md: no Bulgarian twin of {#modularity-q} at level 3",
                                "03-metric-reference.md: no Bulgarian twin of {#other} at level 2",
                                "03-metric-reference.md: no Bulgarian twin of {#seed} at level 3"]
    (en / "06-known-limitations.md").write_text("# Known limitations\n", encoding="utf-8")
    assert "06-known-limitations.md: no Bulgarian file bg/06-known-limitations.md" in problems(en, bg)


def test_the_parity_check_fails_on_labels_markers_ids_and_links(guide):
    en, bg = guide
    path = bg / "03-metric-reference.md"
    path.write_text(BULGARIAN.replace("> **Внимание:** редки тагове.", "> **Тук:** редки тагове."), encoding="utf-8")
    assert any("In short labels" in p for p in problems(en, bg))
    path.write_text(BULGARIAN.replace("*Защо има значение тук.* ", ""), encoding="utf-8")
    assert any("markers" in p for p in problems(en, bg))
    path.write_text(BULGARIAN.replace(" {#lift}", ""), encoding="utf-8")
    assert any("without an {#id}" in p for p in problems(en, bg))
    path.write_text(BULGARIAN.replace("{#lift}", "{#lyft}"), encoding="utf-8")
    assert any("is no English heading" in p for p in problems(en, bg))
    path.write_text(BULGARIAN.replace("(#modularity-q)", "(#modularity)"), encoding="utf-8")
    assert any("resolves to no English heading" in p for p in problems(en, bg))


def test_a_link_to_a_renamed_headings_alias_resolves(guide, monkeypatch):
    en, bg = guide
    monkeypatch.setitem(G.ALIASES, "lift-old", "lift")
    (bg / "03-metric-reference.md").write_text(BULGARIAN.replace("(#modularity-q)", "(#lift-old)"), encoding="utf-8")
    assert not any("resolves to no English heading" in p for p in problems(en, bg))


def test_the_english_guide_is_unchanged_by_the_bulgarian_lookups():
    """English anchors are the computed slugs, so every code-referenced anchor still resolves."""
    from steamstudy.app.help import HELP
    from steamstudy.export.column_index import render

    for key, (file, anchor) in HELP.items():
        assert G.in_short_at("en", file, anchor), key
    assert G.chapter("en", "appendix-b-column-index.md") == render()


def test_the_bulgarian_methods_paragraph_is_the_report_template_in_bulgarian():
    from steamstudy.i18n import text
    from steamstudy.network.selection_text import methods_paragraph

    assert f"> {methods_paragraph(text('bg'))}\n" in (BG / "05-citing-and-reproducing.md").read_text(encoding="utf-8")


def test_tooltip_lines_round_trip_and_take_the_languages_labels():
    import json

    from steamstudy.app import help as H
    from steamstudy.app.layout import ui_words
    from steamstudy.i18n import text

    en, bg = text("en"), text("bg")
    lines = H.tip_lines(H.HELP["control.seed"], en, now="seed 7", last=("field", "seed"))
    assert [kind for kind, _ in lines] == ["in_short", "here", "caution", "now", "field"]
    assert [tuple(line) for line in json.loads(H.tip_json(lines))] == lines
    plain = H.tip_text(lines, en).split("\n")
    assert plain[0].startswith("In short. ") and plain[-2:] == ["Now: seed 7", "Field: seed"]
    assert H.tip_text(lines, bg).split("\n")[-2:] == ["Сега: seed 7", "Поле: seed"]
    assert H.column_line([("app_export/nodes.csv", "degree"), ("app_export/nodes.csv", "degree_intra")], en) == (
        "columns", "degree, degree_intra (nodes.csv)")
    for tx in (en, bg):  # the browser labels every kind it can be sent
        assert set(ui_words(tx)["tip"]) >= {*G.IN_SHORT_KINDS, "now", "column", "columns", "field"}


def _guide_labels_table() -> dict[str, str]:
    """The term table's Guide labels, English -> Bulgarian, with `A / B` rows split and notes in parentheses dropped."""
    text = (REPO / "docs" / "i18n" / "bg-terms.md").read_text(encoding="utf-8")
    section = re.search(r"^## Guide labels\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    assert section, "bg-terms.md has no Guide labels section"
    rows = [line for line in section.group(1).splitlines() if line.startswith("|")][2:]
    out = {}
    for line in rows:
        en, bg = (re.sub(r"\s*\(.*?\)", "", c).strip() for c in line.strip().strip("|").split("|"))
        out.update(zip((x.strip() for x in en.split(" / ")), (x.strip() for x in bg.split(" / ")), strict=True))
    return out


def test_the_bulgarian_in_short_labels_and_markers_are_the_term_tables_guide_labels():
    table = _guide_labels_table()
    for words in (G.LABELS, G.MARKERS):
        for kind, english in words["en"].items():
            # a marker is written without the label's colon ("Caution" is the table's "Caution:")
            bulgarian = table.get(english) or table[english + ":"].removesuffix(":")
            assert words["bg"][kind] == bulgarian, (kind, english)


def test_the_bulgarian_in_short_blocks_keep_the_form_and_the_word_cap():
    for path in sorted(BG.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        for _, _, anchor in G.headings(text):
            lines = G.in_short(_own(text, anchor), "bg")
            if lines:
                assert G.in_short_problems(lines, "bg") == [], (path.name, anchor)

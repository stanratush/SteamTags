"""The User Guide is kept in step with the export schema and the app (ticket 23), and follows its rules."""

from __future__ import annotations

import re

import pytest

from conftest import REPO
from steamstudy.app.guide import PANEL_SECTIONS, headings, help_markdown, slug
from steamstudy.export.column_index import INDEX_FILE, render
from steamstudy.export.schema import REGISTRY

GUIDE = REPO / "docs" / "user-guide"


def _text(name: str) -> str:
    return (GUIDE / name).read_text(encoding="utf-8")


def _anchors(name: str) -> set[str]:
    return {anchor for _, _, anchor in headings(_text(name))}


def test_committed_column_index_is_not_stale():
    assert _text(INDEX_FILE) == render(), "run: python -m steamstudy.export.column_index"


def test_every_column_has_a_guide_entry_with_a_heading():
    anchors = _anchors("03-metric-reference.md")
    missing = sorted({(s.name, c.name, c.guide_entry) for s in REGISTRY for c in s.columns
                      if not c.guide_entry or c.guide_entry not in anchors})
    assert missing == []


def test_every_column_names_its_app_panel_and_report_section():
    assert all(c.app_panel and c.report_section for s in REGISTRY for c in s.columns)


def test_every_declared_file_has_a_paragraph_in_chapter_4():
    anchors = _anchors("04-files.md")
    missing = sorted({s.name for s in REGISTRY if slug(f"`{s.name}`") not in anchors})
    assert missing == []
    for meta in ("snapshot.json", "build.json", "export.json", "analysis.json"):
        assert slug(f"`{meta}`") in anchors


@pytest.mark.parametrize("panel", sorted(PANEL_SECTIONS))
def test_every_in_app_help_anchor_has_a_guide_heading(panel):
    file, anchor = PANEL_SECTIONS[panel]
    assert anchor in _anchors(file)
    assert help_markdown(panel).startswith("#")


def test_three_rules_and_running_guide_link():
    rules = _text("00-three-rules.md")
    for heading in ("No number shows a cause", "Clusters carry no meaning", "Quote the `state_id` with every network number"):
        assert f"## {heading}" in rules
    assert "../running-guide.md" in _text("README.md")


def test_every_metric_entry_ends_with_one_exact_definition():
    text = _text("03-metric-reference.md")
    entries = re.split(r"^### ", text, flags=re.M)[1:]
    assert len(entries) > 60
    for entry in entries:
        body = entry.split("\n## ")[0]
        assert body.count("**Exact definition:**") == 1, entry.splitlines()[0]
        assert "*Example.*" in body and "*Bounds.*" in body and "*Compare with.*" in body, entry.splitlines()[0]


def test_no_interpretation_bands_in_the_metric_reference():
    text = _text("03-metric-reference.md").lower()
    for phrase in ("excellent", "strong structure", "weak structure", "good division", "moderate recovery",
                   "highly stable", "is significant"):
        assert phrase not in text


def test_unverified_sources_are_never_cited():
    everything = "\n".join(p.read_text(encoding="utf-8") for p in GUIDE.glob("*.md"))
    for name in ("Kaufman", "Steinley", "Shiffler", "Hubert, L.", "Hubert & Arabie", "Rousseeuw 1987",
                 "Rousseeuw, P. J. (1987)"):
        assert name not in everything


def test_required_statements_in_the_metric_reference():
    text = _text("03-metric-reference.md")
    for required in ("0.5 but a member of a twenty-tag cluster only 0.05", "√(n − 1)", "not comparable",
                     "pulled towards 1", "inherited from one strong pair", "mechanical", "n / (K + 1)",
                     "Karrer, Levina & Newman 2008, §I", "Q = 0.414", "0.150"):
        assert required in text, required


def test_known_limitations_chapter_holds_the_full_list():
    text = _text("06-known-limitations.md")
    for item in ("current snapshot", "ranked selection", "coverage gaps", "Delisted games", "under 10,000",
                 "Ties at rank 100", "joke votes", "ids 3 and 4", "Dating Sim rank", "country", "allow-parse-errors",
                 "pre-launch", "Early Access", "not optimised", "screening aid", "single run", "K = 10",
                 "fixed γ grid"):
        assert item in text, item


def test_every_inspector_label_is_a_schema_column_whose_guide_entry_names_it():
    from steamstudy.app.view import INSPECTOR_LABELS
    from steamstudy.export import schema as S

    text = _text("03-metric-reference.md")
    entries = {slug(e.splitlines()[0]): e for e in re.split(r"^### ", text, flags=re.M)[1:]}
    assert len(INSPECTOR_LABELS) >= 25
    for label, columns in INSPECTOR_LABELS.items():
        for file, name in columns:
            entry = entries[S.file(file).column(name).guide_entry]
            shown = next(line for line in entry.splitlines() if line.startswith("Shown in the app as"))
            assert f"“{label}”" in shown, (label, name)
    for word in ("hub", "importance"):
        assert all(word not in label.lower() for label in INSPECTOR_LABELS)


# ----------------------------------------------------------------------------- metric help (In short)

def _glossary_terms() -> list[str]:
    return re.findall(r"^\*\*(.+?)\*\*:", (REPO / "CONTEXT.md").read_text(encoding="utf-8"), flags=re.M)


BANNED = ("good", "bad", "strong", "strongly", "weak", "stable", "robust", "important", "significant", "reliable",
          "excellent")


def test_in_short_parser_reads_labelled_lines_in_order():
    from steamstudy.app.guide import in_short, in_short_problems

    entry = ("### Lift\n\n> **In short.** How often two tags meet, against chance.\n>\n"
             "> **Higher →** above 1: more than chance.\n>\n> **Caution:** rare tags give big values.\n\nColumns: x\n")
    lines = in_short(entry)
    assert lines == [("In short.", "How often two tags meet, against chance."),
                     ("Higher →", "above 1: more than chance."), ("Caution:", "rare tags give big values.")]
    assert in_short_problems(lines) == []
    assert in_short("### X\n\nColumns: x\n") == []
    assert in_short_problems([("Here:", "a"), ("In short.", "b")])
    assert in_short_problems([("In short.", "a"), ("Caution:", "b"), ("Here:", "c")])
    assert in_short_problems([("In short.", "word " * 61)])


def test_every_in_short_block_keeps_the_form_and_avoids_quality_words():
    from steamstudy.app.guide import in_short, in_short_problems

    exempt = [t.lower() for t in _glossary_terms()]
    found = 0
    for path in GUIDE.glob("*.md"):
        for entry in re.split(r"^#{2,3} ", path.read_text(encoding="utf-8"), flags=re.M)[1:]:
            lines = in_short("### " + entry)
            if not lines:
                continue
            found += 1
            assert in_short_problems(lines) == [], (path.name, entry.splitlines()[0])
            text = " ".join(t for _, t in lines).lower()
            for term in exempt:
                text = text.replace(term, "")
            for word in BANNED:
                assert not re.search(rf"\b{word}\b", text), (path.name, entry.splitlines()[0], word)
    assert found >= 6


def test_every_app_help_key_resolves_to_an_entry_with_in_short_and_why_it_matters():
    from steamstudy.app.guide import chapter, in_short_at, section
    from steamstudy.app.help import HELP

    for key, (file, anchor) in HELP.items():
        assert anchor in _anchors(file), key
        assert in_short_at(file, anchor), key
        assert "*Why it matters here.*" in section(chapter(file), anchor), key


# ----------------------------------------------------------------------------- links inside the help modal

@pytest.mark.parametrize("href, expected", [
    ("#modularity-q", "03-metric-reference.md#modularity-q"),
    ("04-files.md#nodescsv", "04-files.md#nodescsv"),
    ("05-citing-and-reproducing.md", "05-citing-and-reproducing.md"),
    ("https://www.python.org/downloads/", None),
    ("../running-guide.md", None),
    ("../../CONTEXT.md", None),
])
def test_in_guide_links_resolve_to_a_modal_target(href, expected):
    from steamstudy.app.guide import resolve_link

    assert resolve_link(href, "03-metric-reference.md") == expected


def test_modal_links_point_in_guide_links_at_the_modal_and_leave_the_rest():
    from steamstudy.app.guide import HELP_LINK, modal_links

    text = "See [Q](#modularity-q), [files](04-files.md) and [Python](https://www.python.org/downloads/)."
    assert modal_links(text, "03-metric-reference.md") == (
        f"See [Q]({HELP_LINK}03-metric-reference.md#modularity-q), [files]({HELP_LINK}04-files.md) "
        "and [Python](https://www.python.org/downloads/).")


def test_a_chapter_without_an_anchor_opens_its_first_section():
    from steamstudy.app.guide import help_markdown_at

    shown = help_markdown_at("03-metric-reference.md")
    assert shown.startswith("# Metric reference")
    assert "## How to read this chapter" in shown and "## Settings that change the numbers" not in shown
    assert help_markdown_at("appendix-b-column-index.md").startswith("# Appendix B")


def test_help_markdown_at_rewrites_the_links_it_shows():
    from steamstudy.app.guide import HELP_LINK, help_markdown_at

    assert f"]({HELP_LINK}03-metric-reference.md#null-model-baseline)" in help_markdown_at(
        "03-metric-reference.md", "modularity-q")


def test_every_in_guide_link_the_modal_follows_points_to_an_existing_heading():
    from steamstudy.app.guide import LINK, resolve_link

    followed, broken = 0, []
    for path in GUIDE.glob("*.md"):
        for _, href in LINK.findall(path.read_text(encoding="utf-8")):
            target = resolve_link(href, path.name)
            if target is None:
                continue
            followed += 1
            file, _, anchor = target.partition("#")
            if not (GUIDE / file).is_file() or (anchor and anchor not in _anchors(file)):
                broken.append((path.name, href))
    assert followed > 200
    assert broken == []


def test_every_inspector_label_resolves_to_an_entry_with_in_short_and_why_it_matters():
    from steamstudy.app.guide import chapter, in_short_at, section
    from steamstudy.app.help import column_entry
    from steamstudy.app.view import INSPECTOR_LABELS

    for label, columns in INSPECTOR_LABELS.items():
        file, anchor = column_entry(columns)
        assert in_short_at(file, anchor), label
        assert "*Why it matters here.*" in section(chapter(file), anchor), label


# ----------------------------------------------------------------------------- analytical controls

CONTROL_ENTRIES = ("Minimum Months Filter", "Minimum games per tag", "Minimum shared games", "Hidden Genre Tags",
                   "Hide defining tag", "Clustering weight", "Clustering algorithm", "Resolution γ", "Seed",
                   "Remove / Restore", "Global / Cluster-separated", "Tidy")


def test_every_analytical_control_has_an_entry_with_the_parts_the_spec_lists():
    from steamstudy.app.guide import in_short, in_short_problems, section

    text = _text("02-app-controls.md")
    explained = section(text, "analytical-controls-explained")
    assert [heading for level, heading, _ in headings(explained) if level == 3] == list(CONTROL_ENTRIES)
    for name in CONTROL_ENTRIES:
        entry = section(explained, slug(name))
        assert in_short(entry) and in_short_problems(in_short(entry)) == [], name
        for part in ("*Why it matters here.*", "*Caution.*", "*Example.*"):
            assert part in entry, (name, part)


def test_the_control_reference_links_each_analytical_row_to_its_entry():
    from steamstudy.app.guide import section

    table = section(_text("02-app-controls.md"), "control-reference")
    for name in CONTROL_ENTRIES:
        assert f"](#{slug(name)})" in table, name


GRAPH_ENTRIES = ("Node size", "Edge thickness", "Cluster colour", "Position", "Grey One-Tag Clusters")


def test_reading_the_graph_explains_each_part_of_the_drawing():
    from steamstudy.app.guide import in_short, section

    reading = section(_text("02-app-controls.md"), "reading-the-graph")
    assert in_short(reading) and "*Why it matters here.*" in reading
    assert [heading for level, heading, _ in headings(reading) if level == 3] == list(GRAPH_ENTRIES)
    for name in GRAPH_ENTRIES:
        entry = section(reading, slug(name))
        assert in_short(entry) and "*Why it matters here.*" in entry, name


def test_plain_keeps_identifiers_whole():
    from steamstudy.app.guide import plain

    assert plain("records it in `layout_source`") == "records it in layout_source"
    assert plain("**bold**, *italic*, _also_ and a [link](#x)") == "bold, italic, also and a link"
    assert plain("n_small / n_large") == "n_small / n_large"


def test_every_metric_entry_opens_with_in_short_and_says_why_it_matters():
    """Issue 08: every entry reads the same way, linked from the app or not."""
    from steamstudy.app.guide import in_short

    entries = re.split(r"^### ", _text("03-metric-reference.md"), flags=re.M)[1:]
    missing = [entry.splitlines()[0] for entry in entries
               if not in_short("### " + entry.split("\n## ")[0]) or "*Why it matters here.*" not in entry.split("\n## ")[0]]
    assert missing == []

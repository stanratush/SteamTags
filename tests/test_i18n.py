"""The Interface Language: the translator, the catalogue parity test and the switch (spec: .scratch/
bilingual-cluster-views/spec.md, "Interface Language")."""

from __future__ import annotations

import json

import pytest

from steamstudy import i18n
from steamstudy.i18n import text

import i18n_done
import i18n_parity as P


# ----------------------------------------------------------------------------- the translator


def test_english_is_the_identity_on_keys_and_formats_named_placeholders():
    tx = text("en")
    assert tx("Genre Tag hidden") == "Genre Tag hidden"
    assert tx("{n} of {total} tags", n=3, total=10) == "3 of 10 tags"


def test_bulgarian_falls_back_to_english_for_a_missing_key(monkeypatch):
    monkeypatch.setitem(i18n.catalogue("bg"), "Seed", "Начално число")
    tx = text("bg")
    assert tx("Seed") == "Начално число"
    assert tx("No such message, {x}", x=1) == "No such message, 1"


def test_bulgarian_placeholders_format(monkeypatch):
    monkeypatch.setitem(i18n.catalogue("bg"), "{n} of {total} tags", "{n} от {total}")
    assert text("bg")("{n} of {total} tags", n=3, total=10) == "3 от 10"


@pytest.mark.parametrize("lang", ["en", "bg"])
def test_counted_messages_pick_one_for_1_and_other_otherwise(lang, monkeypatch):
    monkeypatch.setitem(i18n.catalogue("bg"), "{n} tag", {"one": "{n} таг", "other": "{n} тага"})
    tx = text(lang)
    one, other = ("1 tag", "{} tags") if lang == "en" else ("1 таг", "{} тага")
    assert tx.n(1, one="{n} tag", other="{n} tags") == one
    for count in (0, 2, 5):
        assert tx.n(count, one="{n} tag", other="{n} tags") == other.format(count)


def test_counted_messages_format_other_values():
    assert text("en").n(2, one="{n} game has {tag}", other="{n} games have {tag}", tag="RPG") == "2 games have RPG"


def test_lists_join_in_the_language():
    assert text("en").join(["a", "b", "c"]) == "a, b and c"
    assert text("bg").join(["a", "b", "c"]) == "a, b и c"
    assert text("en").join(["a"]) == "a"
    assert text("en").join(["a", "b"]) == "a and b"
    assert text("en").join([]) == ""


def _old_num(value, digits=2):
    """`view.num` as it was before the Interface Language (the reference for English)."""
    if value is None:
        return "n/a"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, int):
        return str(value)
    return f"{value:.{digits}f}"


@pytest.mark.parametrize("value,digits", [(None, 2), (True, 2), (False, 2), (0, 2), (12345, 2), (-3, 2),
                                          (0.42, 2), (0.4249, 3), (1234.5, 1), (-0.5, 2), (2.0, 0)])
def test_english_numbers_are_exactly_todays(value, digits):
    assert text("en").num(value, digits) == _old_num(value, digits)


def test_bulgarian_numbers_have_a_decimal_comma_no_thousands_separator_and_an_attached_percent():
    tx = text("bg")
    assert tx.num(0.42) == "0,42"
    assert tx.num(12345) == "12345"
    assert tx.num(12345.678, 1) == "12345,7"
    assert tx.num(None) == "н/д"
    assert (tx.num(True), tx.num(False)) == ("да", "не")
    assert tx.pct(0.42) == "42%"
    assert tx.pct(0.425, 1) == "42,5%"
    assert text("en").pct(0.425, 1) == "42.5%"
    assert text("en").pct(0.05) == "5%"


def test_only_english_and_bulgarian_exist():
    assert i18n.LANGS == ("en", "bg")
    with pytest.raises(ValueError):
        text("de")


# ----------------------------------------------------------------------------- catalogue parity


def test_the_catalogue_parity_holds_for_the_source_tree():
    assert P.problems(P.scan(), i18n.areas("bg"), i18n_done.CATALOGUE_DONE) == []


def test_parity_fails_for_a_done_module_with_a_missing_entry():
    found = [P.Message("layout", "Seed", None, "app/layout.py:1")]
    assert P.problems(found, {"layout": {}}, set()) == []  # not done yet: English at runtime
    assert any("missing" in p for p in P.problems(found, {"layout": {}}, {"layout"}))


def test_parity_fails_on_a_placeholder_mismatch_even_before_the_module_is_done():
    found = [P.Message("view", "{n} of {total}", None, "app/view.py:1")]
    assert any("placeholder" in p for p in P.problems(found, {"view": {"{n} of {total}": "{n} от {all}"}}, set()))


def test_parity_fails_on_a_counted_message_without_both_forms():
    found = [P.Message("view", "{n} tag", "{n} tags", "app/view.py:1")]
    assert any("forms" in p for p in P.problems(found, {"view": {"{n} tag": {"one": "{n} таг"}}}, set()))
    assert any("forms" in p for p in P.problems(found, {"view": {"{n} tag": "{n} тага"}}, set()))


def test_parity_fails_on_an_orphaned_key():
    assert any("orphan" in p for p in P.problems([], {"view": {"Gone": "Няма"}}, set()))


def test_the_scan_finds_literals_and_counted_messages(tmp_path):
    source = tmp_path / "steamstudy" / "app" / "view.py"
    source.parent.mkdir(parents=True)
    source.write_text('def f(tx):\n    tx("Hello {name}", name=1)\n    tx.n(2, one="{n} tag", other="{n} tags")\n'
                      '    other("not me")\n', encoding="utf-8")
    found = P.scan(tmp_path / "steamstudy")
    assert [(m.area, m.key, m.other) for m in found] == [("view", "Hello {name}", None),
                                                          ("view", "{n} tag", "{n} tags")]


# ----------------------------------------------------------------------------- the switch and the relabel registry


@pytest.fixture(scope="module")
def app(tagged_build):
    from steamstudy.app.server import create_app

    return create_app(tagged_build)


def _props(app, cookie: str | None = None) -> dict:
    from dash_http import layout_props

    client = app.server.test_client()
    if cookie:
        client.set_cookie(i18n.COOKIE, cookie)
    return layout_props(client.get("/_dash-layout").get_json())


@pytest.mark.parametrize("cookie,lang", [(None, "en"), ("bg", "bg"), ("en", "en"), ("xx", "en")])
def test_the_page_is_served_in_the_cookies_language(app, cookie, lang):
    props = _props(app, cookie)
    assert props["lang"]["data"] == lang and props["lang-switch"]["value"] == lang


def test_the_switch_sits_in_the_header_beside_the_mode_switch(tagged_build):
    from steamstudy.app.layout import build_layout
    from steamstudy.app.loader import load_build

    header = next(c for c in _walk(build_layout(load_build(tagged_build))) if getattr(c, "className", "") == "app-header")
    ids = [getattr(c, "id", None) for c in header.children]
    assert ids.index("lang-box") == ids.index("mode") + 1
    box = {getattr(c, "id", None): c for c in _walk(header.children[ids.index("lang-box")])}
    assert [o["value"] for o in box["lang-switch"].options] == ["en", "bg"]
    assert getattr(box["lang-term"], "data-help") == "02-app-controls.md#interface-language"
    assert json.loads(getattr(box["lang-term"], "data-tip"))[0][0] == "in_short"


def test_a_language_switch_relabels_every_registered_prop_and_recomputes_nothing(app, monkeypatch):
    from steamstudy.app import callbacks as CB
    from steamstudy.app import layout as L

    deps = app.server.test_client().get("/_dash-dependencies").get_json()
    on_lang = [d for d in deps if "lang.data" in [f"{i['id']}.{i['property']}" for i in d["inputs"]]]
    assert on_lang and not any("state-meta" in d["output"] or "graph-data" in d["output"] for d in on_lang)
    recompute = next(d for d in deps if "state-meta.data" in d["output"])
    assert "lang" not in [i["id"] for i in recompute["inputs"]]

    set_ = {}
    monkeypatch.setattr(CB, "set_props", lambda id_, props: set_.setdefault(str(id_), {}).update(props))
    monkeypatch.setitem(i18n.catalogue("bg"), "Language", "Език")
    CB.relabel("bg")
    assert set(set_) == {str(id_) for id_, _, _ in L.RELABEL.values()}
    assert next(iter(L.RELABEL.values()))[:2] == ("lang-term", "data-tip")  # the switch's tooltip comes first
    assert set_["lang-term"]["children"] == "Език" and json.loads(set_["lang-term"]["data-tip"])[0][0] == "in_short"
    assert set_["ui-words"]["data"]["title"] == "Мрежа от тагове"


def _walk(component):
    yield component
    children = getattr(component, "children", None)
    for child in children if isinstance(children, list) else [children] if children is not None else []:
        if hasattr(child, "to_plotly_json"):
            yield from _walk(child)


# ----------------------------------------------------------------------------- the pseudo-language (issues 12-14)


@pytest.fixture
def pseudo(monkeypatch):
    """Bulgarian as a pseudo-language that brackets every message, so text that bypasses `tx` shows up unbracketed."""
    from steamstudy.i18n import Text

    call, counted = Text.__call__, Text.n

    def bracket(self, message, **values):
        out = call(self, message, **values)
        return f"⟦{out}⟧" if self.lang == "bg" else out

    def bracket_n(self, count, *, one, other, **values):
        out = counted(self, count, one=one, other=other, **values)
        return f"⟦{out}⟧" if self.lang == "bg" else out

    monkeypatch.setattr(Text, "__call__", bracket)
    monkeypatch.setattr(Text, "n", bracket_n)


def texts(tree, props=("children", "title", "placeholder", "label")) -> list[str]:
    """Every visible string of a component tree (or of plain data): text nodes, titles, placeholders, option labels."""
    out: list[str] = []

    def walk(node):
        if isinstance(node, str):
            out.append(node)
        elif isinstance(node, (list, tuple)):
            for x in node:
                walk(x)
        elif isinstance(node, dict):
            for k, v in node.items():
                if k in props or k == "options":
                    walk(v)
        elif hasattr(node, "to_plotly_json"):
            data = node.to_plotly_json()["props"]
            for k in (*props, "options"):
                if k in data:
                    walk(data[k])
    walk(tree)
    return out


# Words that stay English in every language: proper names and symbols (spec: "Never translated").
KEPT = {"Louvain", "Leiden", "EN", "BG"}


def unbracketed(strings: list[str], names: set[str] = frozenset()) -> list[str]:
    """The strings with words that did not pass through `tx`: anything with two Latin letters in a row, outside
    ⟦…⟧, that is not a name the spec keeps (tag names, dataset labels, C1…)."""
    import re

    bad = []
    for s in strings:
        rest = re.sub(r"⟦.*⟧|⟦.*$|^.*⟧", "", s, flags=re.S)  # a message split by a bold number keeps one bracket
        for name in sorted(names | KEPT, key=len, reverse=True):
            rest = rest.replace(name, "")
        if re.search(r"[A-Za-z]{2}", rest):
            bad.append(s)
    return bad


def test_every_registered_static_prop_passes_through_the_translator(app, pseudo):
    from steamstudy.app.layout import RELABEL, message_value
    from steamstudy.i18n import text

    tx = text("bg")
    for id_, prop, message in RELABEL.values():
        if prop == "data-tip":  # guide text: checked by the guide's own parity test
            continue
        value = message_value(message, tx)
        if id_ == "ui-words":
            value = {k: v for k, v in value.items() if k != "tip"}  # the tip labels are the guide's label set
            strings = [v for v in value.values() if isinstance(v, str)] + [
                v for p in value["pills"].values() for v in (p if isinstance(p, list) else [p])]
        elif prop == "labels":
            strings = list(value.values())
        else:
            strings = texts(value) if not isinstance(value, str) else [value]
        assert not unbracketed(strings), (id_, prop, strings)


def test_grids_take_the_languages_words_and_number_format(app):
    from steamstudy.app.layout import GRIDS, grid_options
    from steamstudy.i18n import text

    en, bg = GRIDS["nodes-grid"](text("en")), GRIDS["nodes-grid"](text("bg"))
    fmt = lambda defs: {d["field"]: d.get("valueFormatter", {}).get("function") for d in defs}  # noqa: E731
    assert fmt(en)["strength_lift"] == "params.value == null ? '' : d3.format('.3~f')(params.value)"
    assert "d3.formatLocale({decimal: ',', thousands: ''" in fmt(bg)["strength_lift"]
    assert [d["headerName"] for d in en] == [d["headerName"] for d in bg]  # column names never translated
    assert grid_options(text("en"))["localeText"]["noRowsToShow"] == "No Rows To Show"


def test_the_workbench_callbacks_render_their_messages_through_the_translator(tagged_build, pseudo, tmp_path,
                                                                             monkeypatch):
    import base64
    from types import SimpleNamespace

    from steamstudy.app import callbacks as CB
    from steamstudy.app.loader import load_build

    ctx = load_build(tagged_build)
    s = ctx.default_settings("overall")
    values = [s.dataset, s.min_games_per_tag, s.min_shared_games, s.min_months, [], [], s.clustering_weight,
              s.algorithm, s.resolution, s.seed, []]
    meta, tables, base, legend, *rest = CB.recompute(str(tagged_build), *values, None, "bg")
    names = {r["tag"] for r in tables["nodes"]} | {r["tag"] for r in tables["nin"]} | {"Overall", "Puzzle"}
    views = CB.state_views(ctx, meta, tables, __import__("steamstudy.i18n", fromlist=["text"]).text("bg"))
    for key in ("legend", "banners", "filters-summary", "rs-estimate", "export-summary"):
        assert not unbracketed(texts(views[key]), names), key
    assert not unbracketed(texts(CB.show_rs(None, [], None, tables, meta, "bg")), names)
    for selection in (None, {"kind": "node", "id": "999999"}, {"kind": "edge", "id": "x", "source": "1", "target": "2"},
                      {"kind": "cluster", "id": "C999"}):
        body, *_ = CB.inspector(selection, tables, None, str(tagged_build), "overall", 0, meta, "bg")
        assert not unbracketed(texts(body), names), selection
    refused = CB.do_open("data:x;base64," + base64.b64encode(b"not an export").decode("ascii"), "y.json",
                         str(tmp_path), "bg")[-1]
    assert refused.startswith("⟦") and not unbracketed([refused])
    assert not unbracketed([CB.thickness_legend({"weight": "lift"}, [1], "bg")[0]])
    monkeypatch.setattr(CB, "ctx", SimpleNamespace(triggered_id="rs-progress-store"))
    assert not unbracketed([CB.progress_display({"done": 2, "total": 5}, None, None, "bg")[2]])


def test_a_language_switch_re_renders_the_state_text_without_recomputing(app):
    deps = app.server.test_client().get("/_dash-dependencies").get_json()
    on_lang = [d for d in deps if "lang" in [i["id"] for i in d["inputs"]]]
    outputs = " ".join(d["output"] for d in on_lang)
    assert "summary-row.children" in outputs and "inspector-body.children" in outputs and "nodes-grid.columnDefs" in outputs
    assert "graph-data.data" not in outputs and "state-meta.data" not in outputs and "elements-base.data" not in outputs
    for d in deps:  # every computing callback reads the language as State at most
        if any(o in d["output"] for o in ("state-meta.data", "graph-data.data", "rs-done.data", "ps-run-done.data")):
            assert "lang" not in [i["id"] for i in d["inputs"]], d["output"]


def test_the_workbench_views_render_every_word_through_the_translator(tagged_build, pseudo):
    """Issue 13: the Inspector (tag, Cluster, link and missing-tag views), the Network State sentence and table, the
    summary row, the quality boxes and lines, and the search: every word bracketed; names, titles and C1… not."""
    import json as _json

    from steamstudy.app import callbacks as CB
    from steamstudy.app.loader import load_build

    ctx = load_build(tagged_build)
    s = ctx.default_settings("overall")
    values = [s.dataset, s.min_games_per_tag, s.min_shared_games, s.min_months, [], [], s.clustering_weight,
              s.algorithm, s.resolution, s.seed, []]
    first = CB.recompute(str(tagged_build), *values, None, "bg")[1]["nodes"][0]["tag_id"]
    meta, tables, *_ = CB.recompute(str(tagged_build), *values[:-1], [first], None, "bg")  # one tag removed
    games = {g.name for g in ctx.games("overall")}
    names = {r["tag"] for r in tables["nodes"]} | {r["tag"] for r in tables["nin"]} | games | {"Overall", meta["state_id"]}
    views = CB.state_views(ctx, meta, tables, text("bg"))
    for key in ("summary-row", "state-sentence", "quality-detail", "dataset-summary", "tag-search"):
        shown = [x for x in texts(views[key]) if not x.startswith("{" + chr(10))]  # the raw state key is data
        assert not unbracketed(shown, names), key
    node, edge = tables["nodes"][0], tables["edges"][0]
    cluster = next(r for r in tables["clusters"] if r["kind"] == "multi_tag")
    missing = tables["nin"][0]
    rs_row = {"rc_ari": 0.9, "rc_ari_beyond_noise": True, "rc_delta_modularity": 0.01, "rc_silhouette_after": 0.2,
              "rc_silhouette_after_status": None, "rc_delta_silhouette": 0.01, "rc_delta_k": 0, "rc_delta_s": 1,
              "rc_centers_lost": [], "fp_delta_modularity": 0.0, "fp_silhouette_after": None,
              "fp_silhouette_after_status": "too_few", "fp_delta_silhouette": None, "tag_id": node["tag_id"]}
    for selection, rs in (({"kind": "node", "id": str(node["tag_id"])}, {"rows": [rs_row], "state_id": "x"}),
                          ({"kind": "edge", "id": "e", "source": str(edge["source_tag_id"]),
                            "target": str(edge["target_tag_id"])}, None),
                          ({"kind": "cluster", "id": cluster["cluster"]}, None),
                          ({"kind": "nin", "id": str(missing["tag_id"])}, None)):
        body, *_ = CB.inspector(selection, tables, rs, str(tagged_build), "overall", 0, meta, "bg")
        strings = texts(body)
        for block in body:  # the escaped HTML blocks: their text nodes and titles
            html_text = getattr(block, "data-html", None) if hasattr(block, "to_plotly_json") else None
            if html_text:
                import html as markup
                import re

                strings += [markup.unescape(t) for t in re.findall(r">([^<>]+)<", html_text)]
                strings += [markup.unescape(t) for t in re.findall(r'title="([^"]*)"', html_text)]
        assert not unbracketed([x for x in strings if x.strip()], names), selection["kind"]

"""Games within a Cluster (spec: .scratch/bilingual-cluster-views/spec.md, "Games within a Cluster")."""

from __future__ import annotations

import csv
import io

import pytest

from steamstudy.app.export import export_zip, open_export, read_export, recorded_table_hashes_match
from steamstudy.app.loader import load_build
from steamstudy.network.state import compute_state
from steamstudy.network.tables import cluster_game_rows, cluster_games, state_tables


def _states(build):
    ctx = load_build(build)
    s = ctx.default_settings("overall")
    genre = next(t.id for t in ctx.genre_tags)
    for settings in (s, s.with_(min_months=12, hidden_tag_ids=tuple(sorted({*s.hidden_tag_ids, genre})))):
        yield ctx, settings, compute_state(ctx.games("overall"), settings, ctx.context("overall"))


def test_each_clusters_games_are_every_filtered_game_with_one_of_its_tags(tagged_build):
    for ctx, settings, state in _states(tagged_build):
        rows = cluster_game_rows(state)
        nodes = set(state.network.nodes)
        kept = [g for g in ctx.games("overall") if g.months_observed >= settings.min_months]
        clusters = {r["cluster"]: r for r in state_tables(state)["clusters.csv"]}
        assert {r["cluster"] for r in rows} <= set(clusters) and "one_tag_pool" not in {r["cluster"] for r in rows}
        for label, cluster in clusters.items():
            members = cluster["member_tag_ids"]
            brute = {g.appid: [t for t in members if t in g.tag_ids] for g in kept if set(members) & set(g.tag_ids)}
            mine = [r for r in rows if r["cluster"] == label]
            assert {r["appid"]: r["matched_tag_ids"] for r in mine} == brute, label
            for r in mine:
                game = next(g for g in kept if g.appid == r["appid"])
                assert r["matched"] == len(r["matched_tag_ids"]) and r["cluster_size"] == len(members)
                assert r["network_tags"] == len(set(game.tag_ids) & nodes)  # hidden tags never count
                assert r["share_of_game"] == pytest.approx(r["matched"] / r["network_tags"])
            assert [(-r["matched"], r["rank"]) for r in mine] == sorted((-r["matched"], r["rank"]) for r in mine)


def test_a_hidden_tag_never_counts_toward_a_games_network_tags(tagged_build):
    ctx = load_build(tagged_build)
    games = ctx.games("overall")
    game = max(games, key=lambda g: len(g.tag_ids))
    tags = sorted(game.tag_ids)
    rows = cluster_games([game], tags[:2], set(tags[:3]))
    assert rows == [{"appid": game.appid, "name": game.name, "rank": game.rank, "matched": 2, "cluster_size": 2,
                     "network_tags": 3, "share_of_game": 2 / 3, "matched_tag_ids": tags[:2]}]


def test_the_export_carries_the_table_and_reopens_it(build_folder):
    ctx = load_build(build_folder)
    settings = ctx.default_settings("overall")
    _, data = export_zip(ctx, settings)
    export, files = read_export(data)
    rows = list(csv.DictReader(io.StringIO(files["cluster_games.csv"].decode("utf-8-sig"))))
    assert rows and list(rows[0]) == ["cluster", "appid", "name", "rank", "matched", "cluster_size", "network_tags",
                                      "share_of_game", "matched_tag_ids", "matched_tags"]
    opened = open_export(data, builds_root=build_folder.resolve().parents[1])
    assert recorded_table_hashes_match(opened, data)
    without = {k: v for k, v in files.items() if k != "cluster_games.csv"}  # an export made before the table
    out = io.BytesIO()
    import json
    import zipfile

    with zipfile.ZipFile(out, "w") as zf:
        for k, v in without.items():
            zf.writestr(k, v)
        zf.writestr("export.json", json.dumps(export))
    assert recorded_table_hashes_match(opened, out.getvalue())


@pytest.fixture(scope="module")
def build_folder(tagged_build):
    return tagged_build


def test_each_csv_row_is_its_on_screen_row(tagged_build):
    """The Cluster Inspector's Games section and cluster_games.csv come from one function (`tables.cluster_games`):
    the same games, in the same order, with the same Matched, "of its tags" and Tags."""
    import html as markup
    import re

    from steamstudy.app import callbacks as CB
    from steamstudy.i18n import text

    ctx = load_build(tagged_build)
    s = ctx.default_settings("overall")
    values = CB.controls_from_settings(ctx, s)
    meta, tables, *_ = CB.recompute(str(tagged_build), *[values[k] for k in CB.CONTROL_IDS], values["removed"], None,
                                    "en")
    state = compute_state(ctx.games("overall"), s, ctx.context("overall"))
    csv_rows = cluster_game_rows(state)
    en = text("en")
    for cluster in tables["clusters"]:
        body, *_ = CB.inspector({"kind": "cluster", "id": cluster["cluster"]}, tables, None, str(tagged_build),
                                "overall", s.min_months, meta, "en")
        # the Games section's table: the block after its "Games" heading (Connections follows it)
        heading = next(i for i, b in enumerate(body) if getattr(b, "children", None) == "Games")
        block = getattr(body[heading + 2], "data-html")
        cells = [[markup.unescape(c) for c in re.findall(r"<td[^>]*>([^<]*)</td>", row)]
                 for row in re.findall(r"<tr>(.*?)</tr>", block)]
        cells = [c for c in cells if c]  # the header rows (one per table: the first ten, then "Show all")
        mine = [r for r in csv_rows if r["cluster"] == cluster["cluster"]]
        one_tag = cluster["kind"] != "multi_tag"
        expected = [[str(r["rank"]), r["name"]]
                    + ([] if one_tag else [f"{r['matched']} / {r['cluster_size']}"])
                    + [en.pct(r["share_of_game"], 0)]
                    + ([] if one_tag else [", ".join(r["matched_tags"])]) for r in mine]
        assert cells == expected, cluster["cluster"]

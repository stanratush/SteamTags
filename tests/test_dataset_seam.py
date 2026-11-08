"""The dataset seam: `read_dataset`, the Steam adapter, Tag Depth and unchanged Network States."""

from __future__ import annotations

import ast
import tomllib
from pathlib import Path

import pytest

from helpers import World
from steamstudy.app.loader import load_build
from steamstudy.build.core import build
from steamstudy.build.writer import write_build
from steamstudy.config import ALL_FILES, config_from_data, load_config
from steamstudy.dataset import Dataset, FilterField, read_dataset
from steamstudy.network.model import TagContext
from steamstudy.snapshot import Snapshot
from test_build_network import tagged_world

SRC = Path(__file__).resolve().parents[1] / "src" / "steamstudy"


def _config(config_dir, **datasets_keys):
    files = {n: tomllib.loads((config_dir / f"{n}.toml").read_text(encoding="utf-8")) for n in ALL_FILES}
    files["datasets"].update(datasets_keys)
    return config_from_data(files, directory=config_dir)


def _tags(*ids):
    return [(i, f"tag {i}") for i in ids]


def _world():
    w = World()
    for i in range(12):
        w.add(100 + i, avg=900.0 - i, months=12 + i, tags=_tags(*range(500, 512), 1664, 600 + i))
    return w


def _built(tmp_path, cfg):
    return write_build(build(Snapshot(_world().snapshot(tmp_path / "snap")), cfg, "20261005T140000Z-abcdef12"),
                       tmp_path)


def test_read_dataset_returns_items_in_rank_order(tmp_path, config_dir):
    ctx = load_build(_built(tmp_path, load_config(config_dir)))
    ds = read_dataset(ctx, "puzzle")
    assert isinstance(ds, Dataset) and ds.key == "puzzle" and ds.size == 12
    assert [i.rank for i in ds.items] == list(range(1, 13))
    assert ds.defining_attribute == 1664 and ds.tag_depth is None
    assert ds.filter_field == FilterField("Minimum Months Filter", 0, 60) and ds.id_label == "AppID"
    first = ds.items[0]
    assert first.filter_value == 12.0 and first.not_counted == ()
    assert ctx.read("overall").defining_attribute is None
    assert ctx.context("puzzle") == TagContext(1664, frozenset(t.id for t in ctx.genre_tags))
    assert [g.appid for g in ctx.games("puzzle")] == [i.id for i in ds.items]


def test_tag_depth_is_applied_once_and_the_full_list_is_kept(tmp_path, config_dir):
    ctx = load_build(_built(tmp_path, _config(config_dir, tag_depth=10)))
    ds = ctx.read("overall")
    assert ctx.depth_cut == 10 and ds.tag_depth == 10
    item = ds.items[0]
    assert len(item.attribute_ids) == 10 and len(item.all_attribute_ids) == 14
    assert item.not_counted == ("tag 510", "tag 511", "tag 1664", "tag 600")
    assert 1664 in item.all_attribute_ids and 1664 not in item.attribute_ids
    assert all(1664 not in g.tag_ids and len(g.tag_ids) == 10 for g in ctx.games("overall"))
    assert ctx.read("puzzle").size == 0  # Puzzle is the 13th tag of every game, beyond depth 10


def test_a_depth_cut_network_ignores_tags_beyond_the_depth(tmp_path, config_dir):
    from steamstudy.network.state import compute_state

    full = load_build(_built(tmp_path / "a", load_config(config_dir)))
    cut = load_build(_built(tmp_path / "b", _config(config_dir, tag_depth=10)))
    s_full = compute_state(full.games("overall"), full.default_settings("overall"), full.context("overall"))
    s_cut = compute_state(cut.games("overall"), cut.default_settings("overall"), cut.context("overall"))
    assert 600 in {n for g in full.games("overall") for n in g.tag_ids}
    assert not {1664, 600, 601} & {n for g in cut.games("overall") for n in g.tag_ids}
    assert set(s_full.index) == set(range(500, 512)) and set(s_cut.index) == set(range(500, 510))


def test_default_build_states_are_unchanged_by_the_seam(tmp_path, config_dir):
    """The Network State of the test Build is the one the Build stage recorded in analysis.json."""
    import json

    from steamstudy.network.state import compute_state

    result = build(Snapshot(tagged_world().snapshot(tmp_path / "snap")), load_config(config_dir),
                   "20261005T140000Z-abcdef12")
    folder = write_build(result, tmp_path)
    ctx = load_build(folder)
    recorded = json.loads((folder / "analysis" / "analysis.json").read_text(encoding="utf-8"))["datasets"]
    for key in ("overall", "puzzle"):
        state = compute_state(ctx.games(key), ctx.default_settings(key), ctx.context(key))
        assert state.state_id == recorded[key]["state_id"]


def test_an_import_source_has_no_adapter_yet(tmp_path, config_dir):
    ctx = load_build(_built(tmp_path, load_config(config_dir)))
    ctx.build_json["source"] = "import"
    with pytest.raises(NotImplementedError):
        read_dataset(ctx, "overall")


def test_games_from_rows_is_only_called_by_the_steam_adapter():
    callers = []
    for path in SRC.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and getattr(node.func, "id", getattr(node.func, "attr", "")) == "games_from_rows":
                callers.append(path.name)
    assert callers == ["dataset.py"]

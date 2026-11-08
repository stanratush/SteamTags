"""Issues 28-33: the Build menu, the draft dialog, Build runs, the Eligible Pool preview and Import data…."""

from __future__ import annotations

import base64
import copy
import dataclasses
import json
import shutil
from pathlib import Path

import pytest
from dash.exceptions import PreventUpdate

from conftest import CONFIG_DIR
from steamstudy import build_admin as BA
from steamstudy import pool_preview as PP
from steamstudy import toml_text
from steamstudy.app import build_menu as BM
from steamstudy.app import build_runs
from steamstudy.app import draft_dialog as DD
from steamstudy.app import preview as PV
from steamstudy.app.loader import load_build, set_builds_root
from steamstudy.build_tree import build_tree, walk
from steamstudy.config import build_config
from steamstudy.i18n import text

EN = text("en")
CALLS: dict = {}  # set_props calls of the current test, by id


@pytest.fixture(scope="module")
def world(tmp_path_factory) -> Path:
    """A repository-like root: config/, a Snapshot with a lightweight form (S1), a raw-only one (S2)."""
    from steamstudy.lightweight import lighten
    from test_build_network import tagged_world

    root = tmp_path_factory.mktemp("menu")
    shutil.copytree(CONFIG_DIR, root / "config")
    for sid in ("S1", "S2"):
        tagged_world().snapshot(root / "snapshots" / sid)
    lighten(root / "snapshots" / "S1")
    return root


@pytest.fixture
def root(world, tmp_path, monkeypatch) -> Path:
    """A fresh copy of the world per test, served as the app's root; `set_props` calls are recorded."""
    shutil.copytree(world, tmp_path / "r")
    root = tmp_path / "r"
    set_builds_root(root / "builds")
    calls = CALLS
    calls.clear()
    record = lambda id_, props: calls.setdefault(json.dumps(id_, sort_keys=True), {}).update(props)  # noqa: E731
    for module in (BM, DD):
        monkeypatch.setattr(module, "set_props", record)
    return root


def _built(root: Path, name: str, source: str = "S1", from_build: str | None = None) -> str:
    draft = (BA.duplicate(root, from_build, source, name=name) if from_build
             else BA.start_draft(root, source, config_dir=root / "config", name=name))
    draft.description = f"why {name} exists"
    BA.save_draft(root, draft)
    folder = BA.build_draft(root, draft)
    return f"{folder.parent.name}/{folder.name}"


def _ids(tree) -> list:
    found = []

    def walk_(node):
        if isinstance(node, (list, tuple)):
            for n in node:
                walk_(n)
            return
        if hasattr(node, "id") and getattr(node, "id", None) is not None:
            found.append(node.id)
        children = getattr(node, "children", None)
        if children is not None:
            walk_(children)
    walk_(tree)
    return found


def _text(tree) -> str:
    out = []

    def walk_(node):
        if isinstance(node, (list, tuple)):
            for n in node:
                walk_(n)
        elif isinstance(node, (str, int, float)):
            out.append(str(node))
        elif node is not None:
            walk_(getattr(node, "children", None))
    walk_(tree)
    return " ".join(out)


# ----------------------------------------------------------------------------- 28: the tree, Delete, Bundles


def test_the_tree_shows_lineage_orphans_drafts_two_snapshots_and_an_import(root):
    from test_import_builds import _csv, _import

    a = _built(root, "A")
    b = _built(root, "B", from_build=a)
    c = _built(root, "C", from_build=b)
    child_draft = BA.duplicate(root, b, "S1", name="Draft of B")
    BA.start_draft(root, "S1", config_dir=root / "config", name="From defaults")
    _built(root, "Other", source="S2")
    import_id = _import(root, _csv())
    BA.delete_build(root, b, open_build=a)  # C and the draft of B lose their parent

    trees = {t.source_id: t for t in build_tree(root)}
    assert set(trees) == {"S1", "S2", import_id}
    assert trees["S1"].forms == ("raw", "lightweight") and trees["S2"].forms == ("raw",)
    assert trees[import_id].kind == "import" and trees[import_id].root_label == "Import defaults"
    s1 = {n.ref: (depth, n) for depth, n in walk(trees["S1"].builds)}
    assert set(s1) == {a, c} and s1[c][1].orphan == "deleted" and s1[a][1].orphan is None
    assert sum(n.latest for _, n in s1.values()) == 1 and s1[c][1].latest
    assert {d.name for d in trees["S1"].drafts} == {"Draft of B", "From defaults"}
    assert child_draft.parent_build_id == b
    assert "Overall 100" in s1[a][1].top_n
    view = BM.tree_view(a, EN)
    assert "from a deleted Build" in _text(view) and "✓ open in this tab" in _text(view)
    assert {"type": "bm-root", "source": import_id} in _ids(view)


def test_delete_refuses_the_open_build_and_deletes_another(root):
    a = _built(root, "A")
    b = _built(root, "B")
    BM._ask_delete(root, a, a, EN)
    assert "switch to another Build first" in _text(CALLS['"bm-dialog-body"']["children"])
    BM._ask_delete(root, b, a, EN)
    body = _text(CALLS['"bm-dialog-body"']["children"])
    assert "It cannot be undone" in body and b in body
    assert CALLS['"bm-pending"']["data"] == {"action": "delete", "ref": b}
    BA.delete_build(root, b, open_build=a)
    assert [n.ref for _, n in walk(build_tree(root)[0].builds)] == [a]


def test_a_bundle_tree_only_switches_and_hides_for_one_build(root, tmp_path):
    a = _built(root, "A")
    b = _built(root, "B", from_build=a)
    bundle = tmp_path / "bundle"
    shutil.copytree(root / "builds", bundle / "builds", ignore=shutil.ignore_patterns("drafts"))
    (bundle / "bundle.json").write_text("{}", encoding="utf-8")
    set_builds_root(bundle / "builds")
    assert not BM.editable() and BM.menu_visible()
    ids = _ids(BM.tree_view(a, EN))
    assert {"type": "bm-build", "ref": b} in ids
    assert not [i for i in ids if isinstance(i, dict) and i["type"] in ("bm-root", "bm-dup", "bm-del", "bm-draft")]
    assert BM.footer_view(EN) == []
    shutil.rmtree(bundle / "builds" / b)
    assert not BM.menu_visible()  # one Build: nothing to switch to


# ----------------------------------------------------------------------------- 29: the dialog and Build runs


def _fields(draft: BA.Draft, root: Path) -> tuple[list, list]:
    ids = [i for i in _ids(DD.body(draft, root, "start", EN)) if isinstance(i, dict) and i.get("type") == "dd-field"]
    values = {"name": draft.name, "description": draft.description}
    for i in ids:
        name = i["name"]
        if name.startswith("toml:"):
            data = {k: v for k, v in draft.config[name[5:]].items()
                    if not (name == "toml:exclusions" and k in ("global_rank_limit", "allowed_app_types"))}
            values[name] = toml_text.dumps(data)
        elif name.startswith("ds:"):
            _, n, key = name.split(":")
            row = draft.config["datasets"]["dataset"][int(n)]
            values[name] = {"defining": (row.get("defining_tag") or {}).get("name", ""),
                            "list_size": row.get("list_size", 100)}.get(key, row.get(key))
        elif name == "tag_depth":
            values[name] = draft.config["datasets"].get("tag_depth", 20)
        elif name == "tag_depth_all":
            values[name] = []
        elif name == "global_rank_limit":
            values[name] = draft.config["exclusions"].get("global_rank_limit")
        elif name == "app_types":
            values[name] = draft.config["exclusions"].get("allowed_app_types", ["game"])
    return ids, [values.get(i["name"]) for i in ids]


def test_a_draft_edited_in_the_dialog_survives_a_reload_and_review_lists_the_change(root):
    draft = BA.start_draft(root, "S1", config_dir=root / "config", name="Edited")
    ids, values = _fields(draft, root)
    edits = {"description": "a shorter Overall", "ds:0:list_size": 40}
    values = [edits.get(i["name"], v) for i, v in zip(ids, values)]
    marks, bad = DD.save_fields(values, ids, {"source": "S1", "slug": draft.stored_slug}, "en")
    assert bad == {}
    (kept,) = BA.list_drafts(root, "S1")  # read back from disk, as after a reload
    assert kept.description == "a shorter Overall" and kept.config["datasets"]["dataset"][0]["list_size"] == 40
    changes = BA.changed_settings(BA.draft_base(root, kept, root / "config"), kept.config)
    assert [(c.file, c.key) for c in changes] == [("datasets", "dataset")]
    review = _text(CALLS['"dd-review"']["children"])
    assert "datasets.toml" in review and "Top-N" in review
    assert marks[BA.STEPS.index("top_n")] == "dd-mark green" and marks[BA.STEPS.index("start")] == "dd-mark green"


def test_a_build_run_completes_appears_as_latest_and_the_strip_offers_to_open_it(root):
    draft = BA.start_draft(root, "S1", config_dir=root / "config", name="Run me")
    draft.description = "built by a run"
    BA.save_draft(root, draft)
    build_runs.start(root, "S1", draft.stored_slug, draft.name)
    assert build_runs.wait_idle()
    (view,) = [v for v in build_runs.runs() if v["name"] == "Run me"]
    assert view["status"] == "done"
    (node,) = [n for _, n in walk(build_tree(root)[0].builds)]
    assert node.ref == view["ref"] and node.latest and node.info.name == "Run me"
    style, rows = BM.strip(1, "en")
    assert {"type": "strip-open", "ref": view["ref"]} in _ids(rows)
    build_runs.dismiss(view["run_id"])


def test_a_failing_run_keeps_the_draft_and_shows_the_failure(root):
    draft = BA.start_draft(root, "S1", config_dir=root / "config", name="Causal")
    draft.description = "a causal word in the reports"
    draft.config["analysis"]["causal_words"] = ["games"]
    BA.save_draft(root, draft)
    build_runs.start(root, "S1", draft.stored_slug, draft.name)
    assert build_runs.wait_idle()
    (view,) = [v for v in build_runs.runs() if v["name"] == "Causal"]
    assert view["status"] == "failed" and "games" in view["error"]
    (kept,) = BA.list_drafts(root, "S1")
    assert kept.last_failure["kind"] == "message"
    assert "The last Build run failed" in _text(DD.body(kept, root, "start", EN))
    _, rows = BM.strip(1, "en")
    assert {"type": "strip-draft", "source": "S1", "slug": kept.stored_slug} in _ids(rows)
    build_runs.dismiss(view["run_id"])


def test_a_second_build_run_waits_for_the_first(root):
    slugs = []
    for name in ("First", "Second"):
        draft = BA.start_draft(root, "S1", config_dir=root / "config", name=name)
        draft.description = name
        if name == "Second":
            draft.config["datasets"]["dataset"][0]["list_size"] = 50
        BA.save_draft(root, draft)
        slugs.append((draft.stored_slug, name))
    for slug, name in slugs:
        build_runs.start(root, "S1", slug, name)
    assert build_runs.wait_idle()
    first, second = [next(v for v in build_runs.runs() if v["name"] == n) for n in ("First", "Second")]
    assert first["status"] == second["status"] == "done"
    assert second["started"] >= first["finished"]
    for v in (first, second):
        build_runs.dismiss(v["run_id"])


# ----------------------------------------------------------------------------- 30: Top-N and Curation


def test_each_editor_writes_the_config_shape_the_build_reads(root):
    draft = BA.start_draft(root, "S1", config_dir=root / "config", name="Shapes")
    draft.config["exclusion_overrides"] = {"override": [{"appid": 10001, "rule": "software_tag", "reason": "r",
                                                         "evidence": "e"}]}
    rules = copy.deepcopy(draft.config["exclusions"])
    rules.pop("global_rank_limit", None)
    rules.pop("allowed_app_types", None)
    renamed = [r["name"] for r in rules["rule"]].index("software_tag")
    rules["rule"][renamed]["name"] = "software"
    config, bad = DD.apply_fields(draft.config, {
        "ds:1:list_size": 30, "ds:1:defining": "Puzzle", "tag_depth": 10, "tag_depth_all": [],
        "global_rank_limit": 5, "app_types": ["game", "dlc"], "toml:exclusions": toml_text.dumps(rules),
        "toml:exclusion_overrides": toml_text.dumps(draft.config["exclusion_overrides"]),
    }, imported=False)
    assert bad == {}
    built = build_config(config)  # the shape issues 19-20 read
    assert built.tag_depth == 10 and built.exclusions.global_rank_limit == 5
    assert built.datasets[1].list_size == 30 and built.datasets[1].defining_tag.name == "Puzzle"
    assert config["exclusions"]["allowed_app_types"] == ["game", "dlc"]
    assert config["exclusion_overrides"]["override"][0]["rule"] == "software"  # the rename followed


def test_a_duplicate_rule_name_marks_the_step_red_and_review_lists_it(root):
    draft = BA.start_draft(root, "S1", config_dir=root / "config", name="Twice")
    draft.description = "two rules with one name"
    rules = draft.config["exclusions"]["rule"]
    rules[1]["name"] = rules[0]["name"]
    BA.save_draft(root, draft)
    content, marks, can_build = DD.review(root, draft, EN, {})
    assert marks["top_n"] == "red" and not can_build
    assert rules[0]["name"] in _text(content) and "Go to Changes the Top-N" in _text(content)


def test_an_import_draft_shows_no_steam_only_field(root):
    from test_import_builds import _csv, _import

    import_id = _import(root, _csv())
    draft = BA.start_draft(root, import_id, config_dir=root / "config", name="Import draft")
    names = {i["name"] for i in _ids([DD.body(draft, root, s, EN) for s in BA.STEPS])
             if isinstance(i, dict) and i.get("type") == "dd-field"}
    assert "app_types" not in names and "toml:manual_metadata" not in names
    assert {"toml:exclusions", "toml:manual_exclusions", "toml:exclusion_overrides", "tag_depth"} <= names


# ----------------------------------------------------------------------------- 31: grid warnings, sliders


def test_grid_warnings_for_a_small_list_and_saving_stays_allowed(root):
    draft = BA.start_draft(root, "S1", config_dir=root / "config", name="Small")
    draft.config["datasets"]["dataset"][0]["list_size"] = 10
    BA.save_draft(root, draft)
    lines = _text(PV.grid_warnings(root, draft, EN))
    assert "Overall (N = 10): the Parameter Grid's largest g (20) is above N." in lines
    assert "Overall (N = 10): min_support (10)" not in lines  # 10 is not above 10
    draft.config["analysis"]["min_support"] = 11
    assert "Overall (N = 10): min_support (11) is above N." in _text(PV.grid_warnings(root, draft, EN))
    assert not [p for p in BA.draft_problems(root, draft) if p.step == "network"]


def test_a_no_pairs_grid_blocks_build(root):
    draft = BA.start_draft(root, "S1", config_dir=root / "config", name="No pairs")
    draft.description = "s above g"
    draft.config["network"]["parameter_selection"]["s_range"] = [25, 30]
    BA.save_draft(root, draft)
    assert [p.step for p in BA.draft_problems(root, draft)] == ["network"]
    _, marks, can_build = DD.review(root, draft, EN, {})
    assert marks["network"] == "red" and not can_build


def test_the_g_slider_rises_to_the_builds_grid(tagged_build):
    from steamstudy.app.layout import slider_tops

    ctx = load_build(tagged_build)
    assert slider_tops(ctx) == (40, 30)
    ps = dataclasses.replace(ctx.network.parameter_selection, g_range=(3, 50))
    wide = dataclasses.replace(ctx, network=dataclasses.replace(ctx.network, parameter_selection=ps))
    assert slider_tops(wide) == (50, 30)


# ----------------------------------------------------------------------------- 32: the Eligible Pool preview


def _edits(config: dict) -> list[dict]:
    rule_tags = copy.deepcopy(config)
    software = next(r for r in rule_tags["exclusions"]["rule"] if r["name"] == "software_tag")
    software["tags"] = software["tags"] + [{"id": 492, "name": "Indie"}]
    depth = copy.deepcopy(config)
    depth["datasets"]["tag_depth"] = 5
    size = copy.deepcopy(config)
    size["datasets"]["dataset"][0]["list_size"] = 30
    return [config, rule_tags, depth, size]


def test_the_preview_equals_the_build_for_defaults_and_three_edits(root):
    from steamstudy.build.core import build
    from steamstudy.lightweight import open_build_source

    records = PP.load_records(root, "S1")
    assert records is not None
    base = BA.start_draft(root, "S1", config_dir=root / "config", name="Base").config
    for settings in _edits(base):
        pv = PP.preview(records, settings)
        assert pv.error is None
        result = build(open_build_source(root / "snapshots", "S1").source, build_config(settings),
                       "20261108T000000Z-preview0")
        for key, r in result.ranked.items():
            assert pv.pools[key][0] == len(r.eligible)
            assert pv.tops[key] == r.top and pv.ties[key] == r.ties


def test_build_stays_off_while_the_previews_key_is_stale(root):
    draft = BA.start_draft(root, "S1", config_dir=root / "config", name="Stale")
    draft.description = "stale key"
    BA.save_draft(root, draft)
    ref = {"source": "S1", "slug": draft.stored_slug}
    with pytest.raises(PreventUpdate):
        DD.build_now(1, ref, "not the current key")
    assert not [v for v in build_runs.runs() if v["name"] == "Stale"]
    key = PV.for_review(root, draft).key
    DD.build_now(1, ref, key)
    assert build_runs.wait_idle()
    (view,) = [v for v in build_runs.runs() if v["name"] == "Stale"]
    assert view["status"] == "done"
    build_runs.dismiss(view["run_id"])


def test_a_raw_only_snapshot_is_not_previewed(root):
    draft = BA.start_draft(root, "S2", config_dir=root / "config", name="Raw")
    pv = PV.for_review(root, draft)
    assert pv.not_previewed and pv.buildable and PV.pool_text(pv, "overall", EN) == "Not previewed"
    assert "Not previewed: this Snapshot has no lightweight form" in _text(PV.review_block(pv, EN))


def test_an_invalid_rule_shows_a_dash_with_the_reason(root):
    draft = BA.start_draft(root, "S1", config_dir=root / "config", name="Bad rule")
    draft.config["exclusions"]["rule"][0]["name"] = "Not A Name!"
    pv = PV.for_review(root, draft)
    assert pv.error and "Not A Name!" in pv.error and pv.error_step == "top_n"
    assert PV.pool_text(pv, "overall", EN) == "—" and not pv.buildable
    assert "— Cannot preview:" in _text(PV.review_block(pv, EN))


# ----------------------------------------------------------------------------- 33: Import data…


def _upload(text_: str) -> str:
    return "data:text/csv;base64," + base64.b64encode(text_.encode("utf-8")).decode("ascii")


def test_a_valid_upload_creates_the_import_and_an_invalid_one_shows_the_table(root):
    from test_import_builds import _csv

    a = _built(root, "A")
    out = BM.import_go(1, _upload(_csv()), "items.csv", None, None, "months", a, "en")
    imports = [p for p in (root / "imports").iterdir() if (p / "import.json").is_file()]
    assert len(imports) == 1 and "Made Import" in _text(out)
    assert json.loads((imports[0] / "import.json").read_text(encoding="utf-8"))["filter_field"] == "months"
    assert any(t.kind == "import" for t in build_tree(root))
    again = BM.import_go(1, _upload(_csv()), "items.csv", None, None, "months", a, "en")
    assert "already Import" in _text(again)
    bad = "id,name,attributes\nx1,One,a\n" + "".join(f"{i},Item {i},a;b\n" for i in range(2, 13))
    refused = BM.import_go(1, _upload(bad), "bad.csv", None, None, "", a, "bg")
    assert "Идентификаторът не е положително цяло число." in _text(refused)  # the code's message, in bg
    assert (root / "imports" / "failed").is_dir() and any((root / "imports" / "failed").rglob("errors.csv"))
    options, value, _ = BM.import_columns(_upload(_csv()), "items.csv", "en")
    assert [o["value"] for o in options] == ["", "months", "price"] and value == ""

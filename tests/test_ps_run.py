"""The Parameter Selection cache, the Run and Validate drivers and Clear app cache (issue 24)."""

from __future__ import annotations

import shutil

import pytest

from steamstudy.i18n import text
from steamstudy.app import app_cache, ps_cache, ps_run
from steamstudy.app.loader import load_build
from steamstudy.network import selection as SEL

EN = text("en")

DATASETS = ["overall", "puzzle"]


def small_settings(ctx):
    base = SEL.load_selection_settings(ctx.network, (t.id for t in ctx.genre_tags), ctx.build_id)
    return base.with_(g_range=(15, 17), s_range=(2, 4), replicates=2, subsamples=2)


@pytest.fixture
def build(tagged_build, tmp_path):
    """A private copy of the test Build, so every test starts with an empty app cache."""
    folder = tmp_path / "root" / "builds" / tagged_build.parent.name / tagged_build.name
    shutil.copytree(tagged_build, folder, ignore=shutil.ignore_patterns("app_cache"))
    return folder


def _files(cache_root):
    folder = ps_cache.root(cache_root)
    return {p.relative_to(folder).as_posix(): p.read_text(encoding="utf-8")
            for p in sorted(folder.rglob("*.json"))}


def _comparable(files):
    """File contents with timings and `computed_with` left out."""
    import json

    out = {}
    for name, text in files.items():
        data = json.loads(text)
        data.pop("seconds", None)
        data.pop("computed_with", None)
        out[name] = SEL.canonical_json(data)
    return out


def test_a_run_writes_the_layout_and_a_second_run_computes_nothing(build):
    ctx = load_build(build)
    settings = small_settings(ctx)
    progress = []
    outcomes = ps_run.run(ctx, settings, DATASETS, on_progress=progress.append)
    assert [o.grid for o in outcomes] == ["complete", "complete"] and all(o.done == 9 for o in outcomes)
    files = _files(ctx.app_cache)
    grids = {name.split("/")[1] for name in files if name.startswith("grids/")}
    assert len(grids) == 2 and all(f"grids/{g}/manifest.json" in files for g in grids)
    for o in outcomes:
        key = settings.grid_key(o.dataset, ctx.context(o.dataset))
        assert ps_cache.grid_state(ctx.app_cache, key, 9).status == "complete"
        if o.chosen is not None:
            assert o.validation == "done"
            assert ps_cache.read_validation(ctx.app_cache, settings.validation_key(
                o.dataset, ctx.context(o.dataset), *o.chosen))["summary"]["null"]["replicates"] == 2
    assert any(o.validation == "done" for o in outcomes)
    # progress: monotonic, ends with everything done
    dones = [r["weight_done"] for r in progress]
    assert dones == sorted(dones) and progress[-1]["weight_done"] == pytest.approx(progress[-1]["weight_total"])
    assert {r["phase"] for r in progress} == {"grid", "validation"}
    again = []
    outcomes2 = ps_run.run(ctx, settings, DATASETS, on_progress=again.append)
    assert again == [] and _files(ctx.app_cache) == files
    assert [o.validation for o in outcomes2] == [o.validation.replace("done", "cached") for o in outcomes]


def test_a_cancelled_grid_resumes_to_the_same_files(build, tmp_path):
    ctx = load_build(build)
    settings = small_settings(ctx).with_(replicates=2, subsamples=2)
    reference = tmp_path / "reference"
    ps_run.run(ctx, settings, ["overall"], cache_root=reference)
    ticks = []
    first = ps_run.run(ctx, settings, ["overall"], on_progress=ticks.append, should_stop=lambda: len(ticks) >= 2)
    assert first[0].grid == "partial" and 0 < first[0].done < 9
    on_disk = len(list((ps_cache.root(ctx.app_cache)).rglob("graphs/*.json")))
    assert on_disk == len(ticks) - 1  # the first record is the start
    resumed = []
    second = ps_run.run(ctx, settings, ["overall"], on_progress=resumed.append)
    assert second[0].grid == "complete"
    assert (resumed[0]["done"], resumed[0]["weight_done"]) == (first[0].done, 0.0)  # starts from the files on disk
    assert resumed[1]["done"] > first[0].done
    assert _comparable(_files(ctx.app_cache)) == _comparable(_files(reference))


def test_a_cancelled_validation_writes_no_file(build):
    ctx = load_build(build)
    settings = small_settings(ctx)
    outcomes = ps_run.run(ctx, settings, ["overall"], should_stop=lambda: False, map_fn=map)
    chosen = outcomes[0].chosen
    assert chosen is not None
    folder = ps_cache.root(ctx.app_cache) / "validation"
    shutil.rmtree(folder)
    ticks = []
    state = ps_run.validate_pair(ctx, settings, "overall", *chosen, on_progress=ticks.append,
                                 should_stop=lambda: len(ticks) >= 1)
    assert state == "stopped" and not list(folder.glob("*.json"))
    assert ps_run.validate_pair(ctx, settings, "overall", *chosen) == "done" and len(list(folder.glob("*.json"))) == 1


def test_serial_and_a_pool_of_two_write_identical_caches(build, tmp_path):
    import multiprocess as mp

    ctx = load_build(build)
    settings = small_settings(ctx)
    ps_run.run(ctx, settings, ["overall"], cache_root=tmp_path / "serial")
    with mp.Pool(2) as pool:
        ps_run.run(ctx, settings, ["overall"], map_fn=pool.imap_unordered, cache_root=tmp_path / "pool")
    assert _comparable(_files(tmp_path / "serial")) == _comparable(_files(tmp_path / "pool"))


def test_eta_text_thresholds():
    record = {"weight_done": 1.0, "weight_total": 100.0, "elapsed": 5.0}
    assert ps_run.eta_text(record, EN) == "estimating…"
    assert ps_run.eta_text({**record, "elapsed": 12.0}, EN) == "about 20 min left"
    assert ps_run.eta_text({**record, "weight_done": 50.0, "elapsed": 30.0}, EN) == "less than a minute left"
    assert ps_run.eta_text({**record, "weight_done": 0.0, "elapsed": 60.0}, EN) == "estimating…"


def test_clear_all_removes_both_kinds_and_the_cli_reports_them(build, caplog):
    import logging

    from steamstudy.app import rs_cache
    from steamstudy.cli import main

    ctx = load_build(build)
    one = small_settings(ctx).with_(g_range=(16, 16), s_range=(2, 2))
    ps_run.run(ctx, one, ["overall"])
    rs_cache.save(ctx.app_cache, rs_cache.CachedRun({"k": 1}, "m", 1))
    assert app_cache.clear_all(ctx.app_cache) == {"removal_sensitivity": 1, "parameter_selection": 1}
    assert app_cache.clear_all(ctx.app_cache) == {"removal_sensitivity": 0, "parameter_selection": 0}
    ps_run.run(ctx, one, ["overall"])
    with caplog.at_level(logging.INFO):
        assert main(["--root", str(build.parents[2]), "app", "--clear-cache", "--build",
                     f"{build.parent.name}/{build.name}"]) == 0
    assert "Cleared 0 cached Removal Sensitivity result(s) and 1 Parameter Selection result(s)" in caplog.text
    assert not ps_cache.root(ctx.app_cache).exists()

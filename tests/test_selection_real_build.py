"""Real-Build regression for Automatic Parameter Selection (slow; skipped without the full Build on disk)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from steamstudy.app.loader import load_build
from steamstudy.network import selection as SEL

REAL_BUILD = Path(__file__).resolve().parents[1] / "builds" / "20261005T062558Z-full" / "20261008T221504Z-7a23ae9f"

# The spec's chosen pairs under the default Selection Settings and Pair Constraints, with their Neighbour Agreement.
CHOSEN = {"overall": ((17, 2), 0.974), "puzzle": ((14, 2), 0.980), "rpg": ((7, 5), 0.774),
          "simulation": ((14, 5), 0.981), "strategy": ((14, 2), 1.000)}


@pytest.mark.slow
@pytest.mark.skipif(not REAL_BUILD.is_dir(), reason="the full Build 20261008T221504Z-7a23ae9f is not on disk")
def test_default_settings_choose_the_spec_pairs_on_the_real_build():
    import multiprocess as mp

    ctx = load_build(REAL_BUILD)
    settings = SEL.load_selection_settings(ctx.network, (t.id for t in ctx.genre_tags), ctx.build_id)
    constraints = SEL.default_constraints(ctx.network)
    workers = max(1, (os.cpu_count() or 2) - 1)
    with mp.Pool(workers) as pool:
        for dataset, (pair, na_value) in CHOSEN.items():
            run = SEL.run_grid(ctx.games(dataset), settings, dataset, ctx.context(dataset),
                               map_fn=pool.imap_unordered)
            grid = SEL.Grid(dataset, run.pair_hash, run.results)
            na = SEL.neighbour_agreement(grid, SEL.neighbour_links(grid))
            choice = SEL.choose(grid, na, constraints)
            assert choice.chosen == pair, dataset
            assert na[pair].value == pytest.approx(na_value, abs=5e-4), dataset

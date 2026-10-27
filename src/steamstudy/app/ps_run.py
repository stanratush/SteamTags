"""The Dash-free Parameter Selection drivers: Run and Validate this pair.

Both the app's background jobs and `steamstudy bundle` call these with an injected `map_fn` (a pool's
`imap_unordered`, or the serial `map`), `on_progress`, `should_stop` and a cache root. Only this, the parent,
process writes the cache. Progress is weighted (edges × scan length) over the whole job, for the ETA.
"""

from __future__ import annotations

import os
import platform
import time
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from steamstudy.app import ps_cache
from steamstudy.app.loader import BuildContext
from steamstudy.network import selection as SEL
from steamstudy.network import validation as V
from steamstudy.versions import software_versions

Progress = Callable[[dict[str, Any]], None]
ESTIMATE_SHARE, ESTIMATE_SECONDS = 0.05, 10.0


def computed_with() -> dict[str, Any]:
    """Recorded with every result, never keyed."""
    return {"versions": software_versions(), "system": platform.system(), "machine": platform.machine(),
            "utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")}


def worker_count(configured: int) -> int:
    """`[parameter_selection] workers`: 0 = os.cpu_count() - 1 (at least 1)."""
    return configured if configured > 0 else max(1, (os.cpu_count() or 2) - 1)


def eta_text(record: Mapping[str, Any]) -> str:
    done, total, elapsed = record["weight_done"], record["weight_total"], record["elapsed"]
    if done <= 0 or (done < ESTIMATE_SHARE * total and elapsed < ESTIMATE_SECONDS):
        return "estimating…"
    left = elapsed * max(0.0, total - done) / done
    return "less than a minute left" if left < 60 else f"about {round(left / 60)} min left"


def elapsed_text(seconds: float) -> str:
    minutes, secs = divmod(int(seconds), 60)
    return f"{minutes} min {secs:02d} s elapsed" if minutes else f"{secs} s elapsed"


@dataclass
class _Meter:
    """Weighted progress over the whole job."""

    on_progress: Progress | None
    n_datasets: int
    weight_total: float
    started: float = field(default_factory=time.perf_counter)
    weight_done: float = 0.0

    def tick(self, dataset: str, index: int, phase: str, done: int, total: int, weight: float) -> None:
        self.weight_done += weight
        if self.on_progress is not None:
            self.on_progress({"dataset": dataset, "dataset_index": index, "n_datasets": self.n_datasets,
                              "phase": phase, "done": done, "total": total, "weight_done": self.weight_done,
                              "weight_total": self.weight_total, "elapsed": time.perf_counter() - self.started})


@dataclass
class DatasetOutcome:
    dataset: str
    grid: str  # complete or partial
    done: int
    total: int
    chosen: tuple[int, int] | None = None
    validation: str = "not_run"  # not_run, cached, done, stopped, none (no chosen pair)


def _choose_default(ctx: BuildContext, grid: SEL.Grid,
                    na: dict[tuple[int, int], SEL.NeighbourAgreement]) -> tuple[int, int] | None:
    return SEL.choose(grid, na, SEL.default_constraints(ctx.network)).chosen


def run(ctx: BuildContext, settings: SEL.SelectionSettings, datasets: Iterable[str], *,
        map_fn: Callable[..., Iterable[Any]] = map, on_progress: Progress | None = None,
        should_stop: Callable[[], bool] | None = None, cache_root: Path | None = None) -> list[DatasetOutcome]:
    """Phase 1: every requested dataset's grid (resuming from graph files on disk), then NA and `choose` under the
    default constraints. Phase 2: each chosen pair's validation, unless cached. Cached work is skipped."""
    cache_root = Path(cache_root or ctx.app_cache)
    stop = should_stop or (lambda: False)
    datasets = list(datasets)
    seeds = SEL.selection_seeds(settings)
    stamp = computed_with()
    plans = []
    for d in datasets:
        key = settings.grid_key(d, ctx.context(d))
        state = ps_cache.grid_state(cache_root, key, len(settings.pairs()))
        pair_hash, tasks = SEL.grid_tasks(ctx.games(d), settings, d, ctx.context(d), skip=state.graph_hashes)
        plans.append((d, key, state, pair_hash, tasks))
    replicates = settings.replicates + settings.subsamples
    grid_weight = sum(t.weight for *_, tasks in plans for t in tasks)
    # Validation's weight is known once a pair is chosen; until then each dataset counts its mean grid task.
    estimates = {d: replicates * (sum(t.weight for t in tasks) / len(tasks) if tasks else 0.0)
                 for d, *_, tasks in plans}
    meter = _Meter(on_progress, len(datasets), grid_weight + sum(estimates.values()))
    outcomes: list[DatasetOutcome] = []
    if grid_weight and plans:
        first = next(p for p in plans if p[4])
        meter.tick(first[0], plans.index(first) + 1, "grid", first[2].done, len(first[3]), 0.0)  # the panel shows now

    for index, (d, key, state, pair_hash, tasks) in enumerate(plans, start=1):
        ps_cache.write_manifest(cache_root, key, pair_hash, stamp)
        on_disk = set(state.graph_hashes)
        done = sum(h in on_disk for h in pair_hash.values())
        total = len(pair_hash)

        def on_result(h: str, result: SEL.GraphResult, ticked: int, weight: float, d: str = d, index: int = index,
                      key: dict[str, Any] = key) -> None:
            nonlocal done
            ps_cache.write_graph(cache_root, key, result)
            on_disk.add(h)
            done += ticked
            meter.tick(d, index, "grid", done, total, weight)

        if tasks and not stop():
            SEL.run_grid(ctx.games(d), settings, d, ctx.context(d), map_fn=map_fn, on_result=on_result,
                         should_stop=stop, skip=state.graph_hashes)
        complete = all(h in on_disk for h in pair_hash.values())
        outcome = DatasetOutcome(d, "complete" if complete else "partial", done, total)
        outcomes.append(outcome)
        if not complete:
            continue
        loaded = ps_cache.load_grid(cache_root, key, d)
        if loaded is None:
            grid = SEL.Grid(d, pair_hash, ps_cache.load_results(cache_root, key, set(pair_hash.values())))
            links = SEL.neighbour_links(grid)
            na = SEL.neighbour_agreement(grid, links)
            ps_cache.write_complete(cache_root, key, links, na)
        else:
            grid, links, na = loaded
        outcome.chosen = _choose_default(ctx, grid, na)

    todo = []
    for index, outcome in enumerate(outcomes, start=1):
        d = outcome.dataset
        if outcome.grid != "complete":
            continue
        if outcome.chosen is None:
            outcome.validation = "none"
        elif ps_cache.read_validation(cache_root, settings.validation_key(d, ctx.context(d), *outcome.chosen)):
            outcome.validation = "cached"
        else:
            todo.append((index, outcome))
            continue
        meter.weight_total -= estimates[d]  # settled before any validation, so the last record ends at the total
    for index, outcome in todo:
        d = outcome.dataset
        assert outcome.chosen is not None
        g, s = outcome.chosen
        if stop():
            outcome.validation = "stopped"
            continue
        outcome.validation = _validate(ctx, settings, d, g, s, seeds, meter, index, estimates[d], map_fn, stop,
                                       cache_root)
    return outcomes


def _validate(ctx: BuildContext, settings: SEL.SelectionSettings, dataset: str, g: int, s: int,
              seeds: tuple[list[int], list[int], list[int]], meter: _Meter, index: int, estimate: float,
              map_fn: Callable[..., Iterable[Any]], stop: Callable[[], bool], cache_root: Path) -> str:
    context = ctx.context(dataset)
    key = settings.grid_key(dataset, context)
    loaded = ps_cache.load_grid(cache_root, key, dataset)
    if loaded is None:
        raise ValueError(f"{dataset}: validation needs a complete grid")
    observed = loaded[0].at(g, s)
    tasks = V.validation_tasks(ctx.games(dataset), settings, dataset, context, g, s, observed, seeds)
    meter.weight_total += sum(t.weight for t in tasks) - estimate
    count = 0

    def on_result(record: dict[str, Any], weight: float) -> None:
        nonlocal count
        count += 1
        meter.tick(dataset, index, "validation", count, len(tasks), weight)

    records = V.run_validation(tasks, map_fn=map_fn, on_result=on_result, should_stop=stop)
    if records is None:
        return "stopped"
    ps_cache.write_validation(cache_root, settings.validation_key(dataset, context, g, s),
                              V.summary_from_records(observed, records), records, computed_with())
    return "done"


def validate_pair(ctx: BuildContext, settings: SEL.SelectionSettings, dataset: str, g: int, s: int, *,
                  map_fn: Callable[..., Iterable[Any]] = map, on_progress: Progress | None = None,
                  should_stop: Callable[[], bool] | None = None, cache_root: Path | None = None) -> str:
    """"Validate this pair": needs a complete cached grid and a Selected Partition. All-or-nothing: a cancel writes
    nothing. Returns done, cached or stopped."""
    cache_root = Path(cache_root or ctx.app_cache)
    context = ctx.context(dataset)
    vkey = settings.validation_key(dataset, context, g, s)
    if ps_cache.read_validation(cache_root, vkey) is not None:
        return "cached"
    meter = _Meter(on_progress, 1, 0.0)
    return _validate(ctx, settings, dataset, g, s, SEL.selection_seeds(settings), meter, 1, 0.0, map_fn,
                     should_stop or (lambda: False), cache_root)

"""The Parameter Selection cache in `<build>/app_cache/parameter_selection/`.

    grids/<grid_key_hash>/manifest.json            grid key, (g, s) -> graph hash, total, computed_with;
                                                   neighbour links and Neighbour Agreement once complete
    grids/<grid_key_hash>/graphs/<graph_hash>.json one per finished distinct graph
    validation/<validation_key_hash>.json          one per (dataset, pair), written only when complete

Every write is atomic (tmp + replace) and only the job's parent process writes. Never evicted automatically;
"Clear app cache" (`app_cache.clear_all`) deletes it, shipped results included.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from steamstudy.network import selection as SEL

RESULTS_DIR = "parameter_selection"


def root(cache_root: Path) -> Path:
    return Path(cache_root) / RESULTS_DIR


def grid_dir(cache_root: Path, grid_key: dict[str, Any]) -> Path:
    return root(cache_root) / "grids" / SEL.key_hash(grid_key)


def validation_path(cache_root: Path, validation_key: dict[str, Any]) -> Path:
    return root(cache_root) / "validation" / f"{SEL.key_hash(validation_key)}.json"


def dumps(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(dumps(data), encoding="utf-8")
    tmp.replace(path)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None


def _pair_text(pair: tuple[int, int]) -> str:
    return f"{pair[0]},{pair[1]}"


def _pair_of(text: str) -> tuple[int, int]:
    g, s = text.split(",")
    return int(g), int(s)


# ----------------------------------------------------------------------------- grids


def write_manifest(cache_root: Path, grid_key: dict[str, Any], pair_hash: dict[tuple[int, int], str],
                   computed_with: dict[str, Any]) -> None:
    """The grid's plan; kept if it exists, so a resumed run keeps its first `computed_with`."""
    path = grid_dir(cache_root, grid_key) / "manifest.json"
    if path.is_file():
        return
    write_json(path, {"grid_key": grid_key, "pairs": {_pair_text(p): h for p, h in sorted(pair_hash.items())},
                      "total": len(pair_hash), "computed_with": computed_with, "complete": False})


def write_graph(cache_root: Path, grid_key: dict[str, Any], result: SEL.GraphResult) -> None:
    write_json(grid_dir(cache_root, grid_key) / "graphs" / f"{result.graph_hash}.json", result.to_json())


def write_complete(cache_root: Path, grid_key: dict[str, Any], links: list[SEL.Link],
                   na: dict[tuple[int, int], SEL.NeighbourAgreement]) -> None:
    """Neighbour links and Neighbour Agreement, computed once per complete grid."""
    path = grid_dir(cache_root, grid_key) / "manifest.json"
    manifest = read_json(path)
    manifest.update({"complete": True, "links": [asdict(x) for x in links],
                     "neighbour_agreement": {_pair_text(p): asdict(v) for p, v in sorted(na.items())}})
    write_json(path, manifest)


@dataclass
class GridState:
    """What the cache holds for one grid key."""

    grid_key: dict[str, Any]
    status: str  # absent, partial, complete
    total: int
    pair_hash: dict[tuple[int, int], str] = field(default_factory=dict)
    graph_hashes: set[str] = field(default_factory=set)  # graph files on disk
    computed_with: dict[str, Any] | None = None
    manifest: dict[str, Any] | None = None

    @property
    def done(self) -> int:
        """Pairs whose graph is on disk."""
        return sum(h in self.graph_hashes for h in self.pair_hash.values())


def grid_state(cache_root: Path, grid_key: dict[str, Any], total: int) -> GridState:
    folder = grid_dir(cache_root, grid_key)
    manifest = read_json(folder / "manifest.json")
    if manifest is None:
        return GridState(grid_key, "absent", total)
    hashes = {p.stem for p in (folder / "graphs").glob("*.json")} if (folder / "graphs").is_dir() else set()
    pair_hash = {_pair_of(k): v for k, v in manifest["pairs"].items()}
    state = GridState(grid_key, "partial", int(manifest["total"]), pair_hash, hashes, manifest["computed_with"],
                      manifest)
    if manifest.get("complete") and state.done == state.total:
        state.status = "complete"
    elif state.done == 0:
        state.status = "absent" if not hashes else "partial"
    return state


def load_results(cache_root: Path, grid_key: dict[str, Any], hashes: set[str]) -> dict[str, SEL.GraphResult]:
    folder = grid_dir(cache_root, grid_key) / "graphs"
    return {h: SEL.GraphResult.from_json(read_json(folder / f"{h}.json")) for h in sorted(hashes)}


def load_grid(cache_root: Path, grid_key: dict[str, Any], dataset: str) -> tuple[
        SEL.Grid, list[SEL.Link], dict[tuple[int, int], SEL.NeighbourAgreement]] | None:
    """A complete grid with its links and Neighbour Agreement, or None."""
    manifest = read_json(grid_dir(cache_root, grid_key) / "manifest.json")
    if manifest is None or not manifest.get("complete"):
        return None
    pair_hash = {_pair_of(k): v for k, v in manifest["pairs"].items()}
    grid = SEL.Grid(dataset, pair_hash, load_results(cache_root, grid_key, set(pair_hash.values())))
    links = [SEL.Link(**{**x, "p": tuple(x["p"]), "q": tuple(x["q"])}) for x in manifest["links"]]
    na = {_pair_of(k): SEL.NeighbourAgreement(**v) for k, v in manifest["neighbour_agreement"].items()}
    return grid, links, na


# ----------------------------------------------------------------------------- validation


def write_validation(cache_root: Path, validation_key: dict[str, Any], summary: dict[str, Any],
                     records: list[dict[str, Any]], computed_with: dict[str, Any]) -> None:
    write_json(validation_path(cache_root, validation_key),
               {"validation_key": validation_key, "summary": summary, "records": records,
                "computed_with": computed_with})


def read_validation(cache_root: Path, validation_key: dict[str, Any]) -> dict[str, Any] | None:
    return read_json(validation_path(cache_root, validation_key))


# ----------------------------------------------------------------------------- listing and clearing


def grids_for(cache_root: Path, settings_key: dict[str, Any]) -> list[dict[str, Any]]:
    """Manifests of every grid made under this settings key."""
    folder = root(cache_root) / "grids"
    out = []
    for path in sorted(folder.glob("*/manifest.json")) if folder.is_dir() else []:
        manifest = read_json(path)
        key = {k: v for k, v in manifest["grid_key"].items() if k not in ("dataset", "hidden_tag_ids")}
        if key == settings_key:
            out.append(manifest)
    return out


def clear(cache_root: Path) -> int:
    """Delete every Parameter Selection result (grids and validations); returns how many were removed."""
    folder = root(cache_root)
    if not folder.is_dir():
        return 0
    count = len(list(folder.glob("grids/*/"))) + len(list(folder.glob("validation/*.json")))
    shutil.rmtree(folder)
    return count

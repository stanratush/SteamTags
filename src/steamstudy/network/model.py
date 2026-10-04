"""Network State settings, the canonical state key and `state_id`."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field, replace
from typing import Any

# Bumped whenever a method or code change would alter results for the same key.
KEY_VERSION = 1

KEY_FIELDS = (
    "build_id", "dataset", "min_months", "min_games_per_tag", "min_shared_games", "hidden_tag_ids",
    "removed_tag_ids", "clustering_weight", "algorithm", "resolution", "seed", "null_replicates", "noise_seeds",
    "key_version",
)


@dataclass(frozen=True)
class Game:
    """One row of a loaded Top-100 Dataset, as far as the network needs it."""

    appid: int
    name: str
    rank: int
    months_observed: int
    tag_ids: tuple[int, ...]
    tags: tuple[str, ...]


def games_from_rows(rows: Iterable[Mapping[str, Any]]) -> list[Game]:
    """Typed rows following the `top100_<dataset>.csv` contract, in rank order."""
    games = [
        Game(int(r["appid"]), str(r["name"]), int(r["rank"]), int(r["months_observed"]),
             tuple(int(t) for t in r["tag_ids"] or ()), tuple(str(t) for t in r["tags"] or ()))
        for r in rows
    ]
    return sorted(games, key=lambda g: g.rank)


@dataclass(frozen=True)
class TagContext:
    """Config facts the reasons need, fixed by the Build (and so by `build_id` in the key)."""

    defining_tag_id: int | None = None
    genre_tag_ids: frozenset[int] = field(default_factory=frozenset)


@dataclass(frozen=True)
class Settings:
    """Everything that fixes one Tag Network result (the Network State)."""

    build_id: str
    dataset: str
    min_months: int = 0
    min_games_per_tag: int = 8
    min_shared_games: int = 8
    hidden_tag_ids: tuple[int, ...] = ()
    removed_tag_ids: tuple[int, ...] = ()
    clustering_weight: str = "shared_games"
    algorithm: str = "louvain"
    resolution: float = 1.0
    seed: int = 0
    null_replicates: int = 20
    noise_seeds: int = 10

    def __post_init__(self) -> None:
        object.__setattr__(self, "hidden_tag_ids", tuple(sorted(set(self.hidden_tag_ids))))
        object.__setattr__(self, "removed_tag_ids", tuple(sorted(set(self.removed_tag_ids))))
        object.__setattr__(self, "resolution", float(resolution_text(self.resolution)))
        if self.clustering_weight not in ("shared_games", "lift"):
            raise ValueError(f"clustering_weight must be shared_games or lift, not {self.clustering_weight!r}")
        if self.algorithm not in ("louvain", "leiden"):
            raise ValueError(f"algorithm must be louvain or leiden, not {self.algorithm!r}")
        if self.null_replicates < 2 or self.noise_seeds < 2:
            raise ValueError("null_replicates and noise_seeds must be >= 2")
        if self.seed < 0:
            raise ValueError("seed must be a non-negative integer")

    def with_(self, **changes: Any) -> Settings:
        return replace(self, **changes)

    def key(self) -> dict[str, Any]:
        return {
            "build_id": self.build_id,
            "dataset": self.dataset,
            "min_months": self.min_months,
            "min_games_per_tag": self.min_games_per_tag,
            "min_shared_games": self.min_shared_games,
            "hidden_tag_ids": list(self.hidden_tag_ids),
            "removed_tag_ids": list(self.removed_tag_ids),
            "clustering_weight": self.clustering_weight,
            "algorithm": self.algorithm,
            "resolution": resolution_text(self.resolution),
            "seed": self.seed,
            "null_replicates": self.null_replicates,
            "noise_seeds": self.noise_seeds,
            "key_version": KEY_VERSION,
        }

    @classmethod
    def from_key(cls, key: Mapping[str, Any]) -> Settings:
        if int(key.get("key_version", -1)) != KEY_VERSION:
            raise ValueError(f"key_version {key.get('key_version')} differs from this software's {KEY_VERSION}")
        return cls(
            build_id=str(key["build_id"]), dataset=str(key["dataset"]), min_months=int(key["min_months"]),
            min_games_per_tag=int(key["min_games_per_tag"]), min_shared_games=int(key["min_shared_games"]),
            hidden_tag_ids=tuple(int(t) for t in key["hidden_tag_ids"]),
            removed_tag_ids=tuple(int(t) for t in key["removed_tag_ids"]),
            clustering_weight=str(key["clustering_weight"]), algorithm=str(key["algorithm"]),
            resolution=float(key["resolution"]), seed=int(key["seed"]),
            null_replicates=int(key["null_replicates"]), noise_seeds=int(key["noise_seeds"]),
        )


def resolution_text(gamma: float | str) -> str:
    return f"{float(gamma):.2f}"


def canonical_key_json(key: Mapping[str, Any]) -> str:
    """Canonical JSON: sorted keys, no whitespace."""
    return json.dumps(dict(key), sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def state_id_of(key: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_key_json(key).encode("utf-8")).hexdigest()[:12]

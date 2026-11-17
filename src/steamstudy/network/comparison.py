"""Cluster Comparison: how the Multi-Tag Clusters of one Top-N Dataset match those of another (Dash-free).

`compare_pair(A, B)` takes two resolved partitions (`Partition`) and returns everything the mode and the
export show for that dataset pair (`PairResult`). Similarity is computed on Tag sets only; games are listed,
never scored.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass, replace
from functools import cached_property
from typing import Any

from sklearn.metrics import adjusted_rand_score

from steamstudy.network.cluster import Cluster, label_order
from steamstudy.network.model import Game, resolution_text, state_id_of

# Bumped whenever a method or code change would alter a comparison for the same key.
COMPARISON_KEY_VERSION = 1
SOURCES = ("pick", "cell", "hand", "no_run")


@dataclass(frozen=True)
class Partition:
    """One dataset's resolved partition at its settings: everything the comparison reads of it."""

    dataset: str
    clusters: tuple[Cluster, ...]  # the whole partition, One-Tag Clusters included, labelled C1…
    edged: frozenset[int]  # network Tags with at least one edge
    hidden: frozenset[int]  # Tags hidden in this dataset (hidden Genre Tags and its own defining Tag)
    games: tuple[Game, ...]  # after the shared Minimum Months Filter, in rank order
    min_games_per_tag: int  # g

    @cached_property
    def nodes(self) -> frozenset[int]:
        return frozenset(t for c in self.clusters for t in c.members)

    @property
    def multi(self) -> tuple[Cluster, ...]:
        return tuple(c for c in self.clusters if c.size >= 2)

    @cached_property
    def cluster_of(self) -> dict[int, Cluster]:
        return {t: c for c in self.clusters for t in c.members}

    @cached_property
    def tag_counts(self) -> Counter[int]:
        """Games of this dataset (after the filter) carrying each Tag."""
        return Counter(t for g in self.games for t in set(g.tag_ids))


GROUPS = ("other_cluster", "one_tag", "not_in_network", "hidden")


@dataclass(frozen=True)
class TagPlace:
    """Where an unshared Tag of one Cluster of a match sits in the other dataset."""

    tag_id: int
    group: str  # other_cluster | one_tag | not_in_network | hidden (set aside: in no figure)
    cluster: str | None = None  # other_cluster: that Multi-Tag Cluster's label
    n_games: int | None = None  # not_in_network: its games in the other dataset
    minimum: int | None = None  # not_in_network: the other dataset's minimum games per tag (g)


def place_in(tag: int, other: Partition) -> TagPlace:
    """The Tag group of an unshared Tag, labelled against the other dataset."""
    if tag in other.hidden:
        return TagPlace(tag, "hidden")
    cluster = other.cluster_of.get(tag)
    if cluster is None:
        return TagPlace(tag, "not_in_network", n_games=other.tag_counts[tag], minimum=other.min_games_per_tag)
    if cluster.size >= 2:
        return TagPlace(tag, "other_cluster", cluster=cluster.label)
    return TagPlace(tag, "one_tag")


@dataclass(frozen=True)
class GameRow:
    """One game in both Clusters of a match."""

    appid: int
    name: str
    rank_a: int
    rank_b: int
    matched_a: tuple[int, ...]  # its Tags of Cluster a, as counted in A's network
    matched_b: tuple[int, ...]
    tags: tuple[int, ...]  # its Tags from either Cluster
    shared: tuple[int, ...]  # of those, the match's shared Tags

    def swapped(self) -> GameRow:
        return replace(self, rank_a=self.rank_b, rank_b=self.rank_a, matched_a=self.matched_b, matched_b=self.matched_a)


def _game_order(r: GameRow) -> tuple[int, int, int]:
    return -(len(r.matched_a) + len(r.matched_b)), r.rank_a, r.rank_b


@dataclass(frozen=True)
class MatchGames:
    """The games in both Top-N Datasets split by the match's two Clusters; only those in both are listed."""

    n_in_common: int
    rows: tuple[GameRow, ...]  # Matched in A + Matched in B descending, then rank in A, then rank in B
    n_only_a: int
    n_only_b: int
    n_neither: int

    def swapped(self) -> MatchGames:
        return MatchGames(self.n_in_common, tuple(sorted((r.swapped() for r in self.rows), key=_game_order)),
                          self.n_only_b, self.n_only_a, self.n_neither)


def match_games(A: Partition, B: Partition, a: frozenset[int], b: frozenset[int]) -> MatchGames:
    """`cluster_games`' rule on each side: a game counts for a Cluster with at least one of its Tags.

    `a` and `b` are the Clusters' Tag sets with set-aside Tags already out: a defining Tag hidden in B would
    otherwise make nearly every game of B count for `a`, and Matched in A is read against that same |a|."""
    in_b = {g.appid: g for g in B.games}
    shared = a & b
    rows, only_a, only_b, neither = [], 0, 0, 0
    for ga in A.games:
        gb = in_b.get(ga.appid)
        if gb is None:
            continue
        ma, mb = tuple(sorted(set(ga.tag_ids) & a)), tuple(sorted(set(gb.tag_ids) & b))
        if ma and mb:
            tags = tuple(sorted({*ma, *mb}))
            rows.append(GameRow(ga.appid, ga.name, ga.rank, gb.rank, ma, mb, tags,
                                tuple(t for t in tags if t in shared)))
        elif ma:
            only_a += 1
        elif mb:
            only_b += 1
        else:
            neither += 1
    rows.sort(key=_game_order)
    n = len(rows) + only_a + only_b + neither
    return MatchGames(n, tuple(rows), only_a, only_b, neither)


@dataclass(frozen=True)
class Match:
    """One Cluster Match: Multi-Tag Cluster `cluster_a` of A and `cluster_b` of B sharing at least one Tag."""

    cluster_a: str
    cluster_b: str
    n_tags_a: int
    n_tags_b: int
    n_shared: int
    jaccard: float  # Match Jaccard: n / (|a| + |b| - n)
    share_a: float  # Shared, % of A: n / |a|
    share_b: float
    n_comparable_a: int  # |a'|: the Cluster's Comparable Tags
    n_comparable_b: int
    comparable_share_a: float | None  # n / |a'|; None below two Comparable Tags in that Cluster
    comparable_share_b: float | None
    comparable_jaccard: float | None  # n / (|a'| + |b'| - n); None below two Comparable Tags in either Cluster
    expected_overlap: float  # E = |a'| * |b'| / N
    overlap_vs_expected: float  # n / E
    shared_tags: tuple[int, ...]
    only_a: tuple[TagPlace, ...]  # A's unshared Tags (set-aside ones included, as "hidden"), by group then id
    only_b: tuple[TagPlace, ...]
    games: MatchGames

    def swapped(self) -> Match:
        return Match(
            cluster_a=self.cluster_b, cluster_b=self.cluster_a, n_tags_a=self.n_tags_b, n_tags_b=self.n_tags_a,
            n_shared=self.n_shared, jaccard=self.jaccard, share_a=self.share_b, share_b=self.share_a,
            n_comparable_a=self.n_comparable_b, n_comparable_b=self.n_comparable_a,
            comparable_share_a=self.comparable_share_b, comparable_share_b=self.comparable_share_a,
            comparable_jaccard=self.comparable_jaccard, expected_overlap=self.expected_overlap,
            overlap_vs_expected=self.overlap_vs_expected, shared_tags=self.shared_tags, only_a=self.only_b,
            only_b=self.only_a, games=self.games.swapped(),
        )

    @property
    def group_counts_a(self) -> dict[str, int]:
        return _group_counts(self.only_a)

    @property
    def group_counts_b(self) -> dict[str, int]:
        return _group_counts(self.only_b)


def _group_counts(places: tuple[TagPlace, ...]) -> dict[str, int]:
    counts = Counter(p.group for p in places)
    return {g: counts[g] for g in GROUPS}


@dataclass(frozen=True)
class ClusterFlag:
    """One Multi-Tag Cluster of one side against the other dataset (set-aside Tags ignored)."""

    cluster: str
    n_tags: int
    n_matches: int
    best_jaccard: float | None  # its best Match Jaccard; None without a match
    flag: str  # outside_network | only_one_tag_clusters | "" (the flags that do not depend on the minimum)
    n_in_one_tag_clusters: int  # its Comparable Tags that are One-Tag Clusters in the other dataset
    n_not_in_network: int  # its Tags not in the other dataset's network

    def flag_at(self, minimum: float) -> str:
        """The flag shown at a Minimum Match Jaccard: adds below_minimum to a Cluster whose matches are all weaker."""
        if self.flag or self.best_jaccard is None or self.best_jaccard >= minimum:
            return self.flag
        return "below_minimum"


def _flags(mine: Partition, other: Partition, best: dict[str, list[float]]) -> tuple[ClusterFlag, ...]:
    out = []
    for c in mine.multi:
        tags = c.members - other.hidden
        comparable = tags & other.nodes
        one_tag = sum(other.cluster_of[t].size == 1 for t in comparable)
        scores = best.get(c.label, [])
        if not comparable:
            flag = "outside_network"
        elif one_tag == len(comparable):
            flag = "only_one_tag_clusters"
        else:
            flag = ""
        out.append(ClusterFlag(c.label, len(tags), len(scores), max(scores, default=None), flag, one_tag,
                               len(tags - other.nodes)))
    return tuple(out)


@dataclass(frozen=True)
class PairResult:
    """Everything one dataset pair shows: the overview, every Cluster Match and each side's flags."""

    dataset_a: str
    dataset_b: str
    comparable: tuple[int, ...]  # C: the Tags in both networks, One-Tag Clusters included
    set_aside_a: tuple[int, ...]  # A's network Tags hidden in B: removed from every figure, flag and count
    set_aside_b: tuple[int, ...]
    matches: tuple[Match, ...]  # ranked by Match Jaccard, highest first
    flags_a: tuple[ClusterFlag, ...]  # each Multi-Tag Cluster of A against B, by label
    flags_b: tuple[ClusterFlag, ...]
    comparable_share_a: float | None  # the Comparable Tags as a share of A's network Tags; None for an empty network
    comparable_share_b: float | None
    ari: float | None  # ARI (comparable Tags), on those with an edge in either network; None below two
    n_games_in_common: int  # games in both Top-N Datasets after the shared Minimum Months Filter

    @property
    def n_comparable(self) -> int:
        """N = |C|."""
        return len(self.comparable)

    @property
    def n_matches(self) -> int:
        return len(self.matches)

    def swapped(self) -> PairResult:
        """The same pair with B on the left (the ⇄ button): derived, never recomputed."""
        return PairResult(
            dataset_a=self.dataset_b, dataset_b=self.dataset_a, comparable=self.comparable,
            set_aside_a=self.set_aside_b, set_aside_b=self.set_aside_a,
            matches=tuple(sorted((m.swapped() for m in self.matches), key=_match_order)),
            flags_a=self.flags_b, flags_b=self.flags_a, comparable_share_a=self.comparable_share_b,
            comparable_share_b=self.comparable_share_a, ari=self.ari, n_games_in_common=self.n_games_in_common,
        )


def _match_order(m: Match) -> tuple[float, int, int]:
    return -m.jaccard, label_order(m.cluster_a), label_order(m.cluster_b)


def _share(n: int, size: int) -> float | None:
    return n / size if size >= 2 else None


def _places(tags: frozenset[int], other: Partition) -> tuple[TagPlace, ...]:
    return tuple(sorted((place_in(t, other) for t in tags), key=lambda p: (GROUPS.index(p.group), p.tag_id)))


def _match(A: Partition, B: Partition, ca: Cluster, cb: Cluster, comparable: frozenset[int]) -> Match:
    a, b = ca.members - B.hidden, cb.members - A.hidden  # set-aside Tags out
    n = len(a & b)
    a2, b2 = len(a & comparable), len(b & comparable)
    expected = a2 * b2 / len(comparable)
    return Match(
        cluster_a=ca.label, cluster_b=cb.label, n_tags_a=len(a), n_tags_b=len(b), n_shared=n,
        jaccard=n / (len(a) + len(b) - n), share_a=n / len(a), share_b=n / len(b),
        n_comparable_a=a2, n_comparable_b=b2, comparable_share_a=_share(n, a2), comparable_share_b=_share(n, b2),
        comparable_jaccard=n / (a2 + b2 - n) if a2 >= 2 and b2 >= 2 else None,
        expected_overlap=expected, overlap_vs_expected=n / expected,
        shared_tags=tuple(sorted(a & b)), only_a=_places(ca.members - b, B), only_b=_places(cb.members - a, A),
        games=match_games(A, B, a, b),
    )


def _coverage(comparable: frozenset[int], p: Partition) -> float | None:
    return len(comparable) / len(p.nodes) if p.nodes else None


def comparable_ari(a: Partition, b: Partition) -> float | None:
    """ARI on the Comparable Tags with an edge in at least one of the two networks (`selection.link`'s set)."""
    compared = sorted(t for t in a.nodes & b.nodes if t in a.edged or t in b.edged)
    if len(compared) < 2:
        return None
    return float(adjusted_rand_score([a.cluster_of[t].label for t in compared],
                                     [b.cluster_of[t].label for t in compared]))


def compare_pair(a: Partition, b: Partition) -> PairResult:
    """One dataset pair, A = `a`; `PairResult.swapped` gives the other orientation."""
    comparable = a.nodes & b.nodes
    matches = []
    for ca in a.multi:
        for cb in b.multi:
            if ca.members & cb.members:
                matches.append(_match(a, b, ca, cb, comparable))
    matches.sort(key=_match_order)
    by_a: dict[str, list[float]] = {}
    by_b: dict[str, list[float]] = {}
    for m in matches:
        by_a.setdefault(m.cluster_a, []).append(m.jaccard)
        by_b.setdefault(m.cluster_b, []).append(m.jaccard)
    return PairResult(
        dataset_a=a.dataset, dataset_b=b.dataset, comparable=tuple(sorted(comparable)),
        set_aside_a=tuple(sorted(a.nodes & b.hidden)), set_aside_b=tuple(sorted(b.nodes & a.hidden)),
        matches=tuple(matches), flags_a=_flags(a, b, by_a), flags_b=_flags(b, a, by_b),
        comparable_share_a=_coverage(comparable, a), comparable_share_b=_coverage(comparable, b),
        ari=comparable_ari(a, b), n_games_in_common=len({g.appid for g in a.games} & {g.appid for g in b.games}),
    )


def compare_all(partitions: Sequence[Partition]) -> dict[tuple[str, str], PairResult]:
    """Every unordered pair of the included datasets once, in the Build's order, the earlier dataset as A."""
    return {(a.dataset, b.dataset): compare_pair(a, b)
            for i, a in enumerate(partitions) for b in partitions[i + 1:]}


# ----------------------------------------------------------------------------- the Comparison State


@dataclass(frozen=True)
class SharedSettings:
    """The settings shared by every dataset of a comparison (the mode's header row)."""

    clustering_weight: str
    algorithm: str
    min_months: int
    genre_hidden: tuple[int, ...]  # the hidden Genre Tag ids (each dataset's defining Tag is always hidden too)
    removed_tag_ids: tuple[int, ...]

    def key(self) -> dict[str, Any]:
        return {"clustering_weight": self.clustering_weight, "algorithm": self.algorithm,
                "min_months": self.min_months, "genre_hidden": sorted(set(self.genre_hidden)),
                "removed_tag_ids": sorted(set(self.removed_tag_ids))}


@dataclass(frozen=True)
class DatasetValues:
    """One included dataset's source and values."""

    dataset: str
    source: str  # pick | cell | hand | no_run
    g: int
    s: int
    resolution: float  # γ: the Selected Resolution on a cell, as typed or the network default otherwise
    selection_key: dict[str, Any] | None = None  # on a cell: its Parameter Selection settings key
    seed: int | None = None  # set by hand or no run: the Build's main seed

    def __post_init__(self) -> None:
        if self.source not in SOURCES:
            raise ValueError(f"source must be one of {SOURCES}, not {self.source!r}")

    @property
    def on_cell(self) -> bool:
        return self.source in ("pick", "cell")

    def key(self) -> dict[str, Any]:
        """Pick vs. selected cell, and hand vs. no run, are not in the key: only what fixes the partition."""
        values = {"dataset": self.dataset, "g": self.g, "s": self.s, "resolution": resolution_text(self.resolution)}
        if self.on_cell:
            return {**values, "selection_key": self.selection_key}
        return {**values, "seed": self.seed}


def comparison_key(build_id: str, shared: SharedSettings, datasets: Sequence[DatasetValues]) -> dict[str, Any]:
    """Everything that fixes one Cluster Comparison result; `datasets` in the Build's dataset order."""
    return {"build_id": build_id, "shared": shared.key(), "datasets": [d.key() for d in datasets],
            "key_version": COMPARISON_KEY_VERSION}


def comparison_id(key: dict[str, Any]) -> str:
    """The first 12 hex of the SHA-256 of the key's canonical JSON, made as `state_id` is."""
    return state_id_of(key)

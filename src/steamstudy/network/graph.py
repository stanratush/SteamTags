"""Building the Tag Network from games: filter, nodes, edges, Not-in-network reasons, Clustering Weight."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from itertools import combinations

import networkx as nx

from steamstudy.network.model import Game, Settings, TagContext

REASON_ORDER = ("removed", "defining_tag_hidden", "genre_tag_hidden", "below_min_games")
WEIGHT_ATTR = {"shared_games": "shared", "lift": "lift"}


@dataclass(frozen=True)
class Edge:
    u: int  # u < v
    v: int
    shared: int
    lift: float


@dataclass(frozen=True)
class NotInNetwork:
    tag_id: int
    tag: str
    n_games: int
    reasons: tuple[str, ...]


@dataclass
class TagNetwork:
    games: list[Game]  # after the Minimum Months Filter, in rank order
    tag_names: dict[int, str]
    tag_games: dict[int, frozenset[int]]  # tag -> AppIDs among the N games (every tag of the dataset)
    nodes: list[int]  # sorted
    edges: list[Edge]  # sorted by (u, v)
    not_in_network: list[NotInNetwork]

    @property
    def n_games(self) -> int:
        return len(self.games)

    def n(self, tag: int) -> int:
        return len(self.tag_games.get(tag, ()))

    def edge_appids(self, u: int, v: int) -> list[int]:
        """AppIDs of the games having both tags, in dataset rank order."""
        both = self.tag_games.get(u, frozenset()) & self.tag_games.get(v, frozenset())
        return [g.appid for g in self.games if g.appid in both]


def filter_games(games: list[Game], min_months: int) -> list[Game]:
    """The Minimum Months Filter: drops games below the threshold; never re-ranks or backfills."""
    return [g for g in games if g.months_observed >= min_months]


def build_network(games: list[Game], settings: Settings, context: TagContext) -> TagNetwork:
    kept = filter_games(games, settings.min_months)
    names: dict[int, str] = {}
    for g in games:  # every tag on at least one game of the dataset, filtered or not
        for tag_id, name in zip(g.tag_ids, g.tags):
            names.setdefault(tag_id, name)
    tag_sets: dict[int, set[int]] = {t: set() for t in names}
    for g in kept:
        for tag_id in g.tag_ids:
            tag_sets[tag_id].add(g.appid)
    tag_games = {t: frozenset(s) for t, s in tag_sets.items()}

    hidden, removed = set(settings.hidden_tag_ids), set(settings.removed_tag_ids)
    nodes, out = [], []
    for tag in sorted(names):
        reasons = []
        if tag in removed:
            reasons.append("removed")
        if tag in hidden and tag == context.defining_tag_id:
            reasons.append("defining_tag_hidden")
        if tag in hidden and tag in context.genre_tag_ids:
            reasons.append("genre_tag_hidden")
        if tag in hidden and not ({"defining_tag_hidden", "genre_tag_hidden"} & set(reasons)):
            reasons.append("genre_tag_hidden")  # a hidden tag is always a Genre Tag or the defining tag
        if len(tag_games[tag]) < settings.min_games_per_tag:
            reasons.append("below_min_games")
        if reasons:
            out.append(NotInNetwork(tag, names[tag], len(tag_games[tag]), tuple(r for r in REASON_ORDER if r in reasons)))
        else:
            nodes.append(tag)

    edges = shared_edges(kept, nodes, tag_games, settings.min_shared_games)
    return TagNetwork(kept, names, tag_games, nodes, edges, out)


def shared_edges(games: list[Game], nodes: list[int], tag_games: dict[int, frozenset[int]], min_shared: int) -> list[Edge]:
    node_set = set(nodes)
    counts: Counter[tuple[int, int]] = Counter()
    for g in games:
        present = sorted(t for t in set(g.tag_ids) if t in node_set)
        counts.update(combinations(present, 2))
    n = len(games)
    edges = []
    for (u, v), shared in sorted(counts.items()):
        if shared >= min_shared:
            lift = shared * n / (len(tag_games[u]) * len(tag_games[v]))
            edges.append(Edge(u, v, shared, lift))
    return edges


def to_graph(nodes: list[int], edges: list[Edge], clustering_weight: str) -> nx.Graph:
    """Canonical order: nodes sorted, edges sorted by (u, v); attribute `w` is the active Clustering Weight."""
    g = nx.Graph()
    g.add_nodes_from(sorted(nodes))
    attr = WEIGHT_ATTR[clustering_weight]
    for e in sorted(edges, key=lambda e: (e.u, e.v)):
        g.add_edge(e.u, e.v, shared=float(e.shared), lift=e.lift, w=float(e.shared) if attr == "shared" else e.lift)
    return g

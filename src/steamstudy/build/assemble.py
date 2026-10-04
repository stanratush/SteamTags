"""Row builders for the Build's dataset and report files."""

from __future__ import annotations

import statistics
from collections import Counter
from typing import Any

from steamstudy.build.datasets import RankedDataset, month_index, store_month_index, would_be_rank
from steamstudy.build.exclusion import Evaluation
from steamstudy.build.games import Game
from steamstudy.build.parse import MonthlyHistory, TagVocabulary
from steamstudy.build.score import Score, Window
from steamstudy.export.schema import DATASET_KEYS


class GameTable:
    """Shared lookups for the row builders."""

    def __init__(self, scores: dict[int, Score], games: dict[int, Game], histories: dict[int, MonthlyHistory],
                 listing_rank: dict[int, int], ranked: dict[str, RankedDataset], flags: dict[int, list[str]]):
        self.scores, self.games, self.histories = scores, games, histories
        self.listing_rank, self.ranked, self.flags = listing_rank, ranked, flags

    def would_be_ranks(self, appid: int) -> dict[str, int | None]:
        return {f"would_be_rank_{key}": would_be_rank(self.ranked[key], appid, self.scores, self.games)
                if key in self.ranked else None for key in DATASET_KEYS}


def top100_rows(t: GameTable, ranked: RankedDataset) -> list[dict[str, Any]]:
    rows = []
    for rank, appid in enumerate(ranked.top, start=1):
        g, s = t.games[appid], t.scores[appid]
        rows.append({
            "dataset": ranked.key, "rank": rank, "appid": appid, "name": g.name,
            "mean_monthly_players": s.mean_monthly_players, "months_observed": s.months_observed,
            "release_month": s.release_month, "store_release_date": g.release_date, "is_free": g.is_free,
            "app_type": g.app_type, "tag_ids": [x.tag_id for x in g.tags], "tags": [x.name for x in g.tags],
            "genre_ids": [x.genre_id for x in g.genres], "genres": [x.name for x in g.genres],
            "content_flags": t.flags.get(appid, []), "metadata_source": g.metadata_source,
            "top_listing_rank": t.listing_rank.get(appid),
        })
    return rows


def ties_rows(t: GameTable) -> list[dict[str, Any]]:
    rows = []
    for ranked in t.ranked.values():
        for appid in ranked.ties:
            s = t.scores[appid]
            rows.append({"dataset": ranked.key, "position": ranked.eligible.index(appid) + 1, "appid": appid,
                         "name": t.games[appid].name, "mean_monthly_players": s.mean_monthly_players,
                         "months_observed": s.months_observed})
    return rows


def members(t: GameTable) -> list[int]:
    return sorted({a for r in t.ranked.values() for a in r.top})


def monthly_players_rows(t: GameTable, window: Window) -> list[dict[str, Any]]:
    rows = []
    for appid in members(t):
        release = t.scores[appid].release_month
        for r in t.histories[appid].rows:
            if not r.is_placeholder and r.month >= release and r.month in window:
                rows.append({"appid": appid, "month": r.month, "avg_players": r.avg, "peak_players": r.peak})
    return rows


def exclusion_rows(t: GameTable, evaluations: dict[int, Evaluation]) -> list[dict[str, Any]]:
    rows = []
    for appid in sorted(evaluations):
        ev = evaluations[appid]
        for m in ev.matches:
            rows.append({"appid": appid, "name": t.games[appid].name, "reason": m.rule, "detail": m.detail,
                         "primary_reason": ev.primary_reason,
                         "mean_monthly_players": t.scores[appid].mean_monthly_players, **t.would_be_ranks(appid)})
    return rows


def impact_removal_rows(t: GameTable, evaluations: dict[int, Evaluation]) -> list[dict[str, Any]]:
    rows = []
    for appid in sorted(evaluations):
        ev = evaluations[appid]
        for m in ev.matches:
            for label, tag_id in m.signals:
                rows.append({"rule": m.rule, "signal": label, "tag_id": tag_id, "appid": appid,
                             "name": t.games[appid].name, "is_primary_reason": m.rule == ev.primary_reason,
                             **t.would_be_ranks(appid)})
    rows.sort(key=lambda r: (r["rule"], r["signal"], r["appid"]))
    return rows


def near_miss_rows(t: GameTable, evaluations: dict[int, Evaluation]) -> list[dict[str, Any]]:
    rows = []
    for appid in sorted(evaluations):
        ev = evaluations[appid]
        for nm in ev.near_misses:
            rows.append({"rule": nm.rule, "tag_id": nm.tag.tag_id, "tag": nm.tag.name, "appid": appid,
                         "name": t.games[appid].name, "position": nm.tag.position, "rank_limit": nm.rank_limit,
                         "excluded": ev.excluded, **t.would_be_ranks(appid)})
    return rows


def adult_signal_rows(t: GameTable, evaluations: dict[int, Evaluation]) -> list[dict[str, Any]]:
    rows = []
    for appid in sorted(evaluations):
        ev = evaluations[appid]
        s = ev.adult_signals
        if s and s["adult_only_notice"] != s["content_descriptor_3"]:
            rows.append({"appid": appid, "name": t.games[appid].name, **s, "excluded": ev.excluded,
                         **t.would_be_ranks(appid)})
    return rows


def unexcluded_rows(t: GameTable, genre_kind: dict[int, str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for ranked in t.ranked.values():
        for rank, appid in enumerate(ranked.top, start=1):
            g = t.games[appid]
            signals = [f"content_descriptor_{i}" for i in (1, 4) if i in g.descriptor_ids]
            signals += [f"software_genre:{x.name}" for x in g.genres if genre_kind.get(x.genre_id) == "software"]
            signals += [f"content_flag:{code}" for code in t.flags.get(appid, [])]
            rows.extend({"dataset": ranked.key, "rank": rank, "appid": appid, "name": g.name, "signal": sig}
                        for sig in signals)
    return rows


def tag_vocabulary_rows(games: dict[int, Game], vocabulary: TagVocabulary | None) -> list[dict[str, Any]]:
    tags: Counter[tuple[int, str]] = Counter()
    genres: Counter[tuple[int, str]] = Counter()
    for g in games.values():
        if not g.has_data:
            continue
        tags.update({(x.tag_id, x.name) for x in g.tags})
        genres.update({(x.genre_id, x.name) for x in g.genres})
    rows = [{"kind": "tag", "id": i, "name": n, "app_count": c,
             "in_vocabulary": (i in vocabulary.tags) if vocabulary else None}
            for (i, n), c in sorted(tags.items(), key=lambda kv: (-kv[1], kv[0]))]
    rows += [{"kind": "genre", "id": i, "name": n, "app_count": c, "in_vocabulary": None}
             for (i, n), c in sorted(genres.items(), key=lambda kv: (-kv[1], kv[0]))]
    return rows


def release_month_check_rows(t: GameTable, threshold: int) -> list[dict[str, Any]]:
    rows = []
    for appid in members(t):
        g, s = t.games[appid], t.scores[appid]
        store = store_month_index(g.release_date)
        apart = None if store is None else store - month_index(s.release_month)
        if apart is None or abs(apart) > threshold:
            rows.append({"appid": appid, "release_month": s.release_month, "store_release_date": g.release_date,
                         "months_apart": apart})
    return rows


def manual_metadata_rows(games: dict[int, Game]) -> list[dict[str, Any]]:
    return [c for appid in sorted(games) for c in games[appid].citations]


def depth_check_rows(t: GameTable) -> list[dict[str, Any]]:
    rows = []
    for ranked in t.ranked.values():
        ranks = [t.listing_rank[a] for a in ranked.top if a in t.listing_rank]

        def row(item: str, value: int, note: str) -> dict[str, Any]:
            return {"section": "depth_check", "item": item, "dataset": ranked.key, "value": value, "note": note}

        rows.append(row("members", len(ranked.top), "games in this Top-100 Dataset"))
        rows.append(row("members_without_listing_rank", len(ranked.top) - len(ranks),
                        "members not in the /top listing (test-mode edge cases)"))
        if ranks:
            rows.append(row("deepest_top_listing_rank", max(ranks), "deepest /top rank of any member"))
            rows.append(row("median_top_listing_rank", int(statistics.median_low(ranks)),
                            "median /top rank of the members (lower median)"))
            for depth in (1000, 5000, 10000):
                rows.append(row(f"members_beyond_rank_{depth}", sum(r > depth for r in ranks),
                                f"members whose best /top rank is deeper than {depth}"))
    return rows

"""Feature-analysis tables for one full Top-100 Dataset (every game counted once, no Minimum Months Filter).

Frequencies are compared with the Eligible Pool (Top 100 included). The defining tag is listed at 100%
in the tag-frequency table and left out of combinations and associations.
"""

from __future__ import annotations

import json
import math
import statistics
from collections import Counter
from functools import cache
from importlib import resources
from itertools import combinations
from typing import Any

from scipy.stats import fisher_exact

Rows = list[dict[str, Any]]


@cache
def archived_categories() -> dict[str, list[str]]:
    text = resources.files("steamstudy.analysis").joinpath("archived_tag_categories.json").read_text(encoding="utf-8")
    return dict(json.loads(text)["categories"])


def _ratio(share: float, baseline: float) -> float | None:
    return share / baseline if baseline else None


def tag_frequency(dataset: str, top: Rows, pool: Rows, defining_tag: int | None) -> Rows:
    """top/pool: rows with `tag_ids` and `tags` (display order)."""
    n, n_pool = len(top), len(pool)
    counts: Counter[int] = Counter()
    positions: dict[int, list[int]] = {}
    names: dict[int, str] = {}
    for row in top:
        for position, (tag_id, name) in enumerate(zip(row["tag_ids"], row["tags"]), start=1):
            counts[tag_id] += 1
            positions.setdefault(tag_id, []).append(position)
            names.setdefault(tag_id, name)
    baseline: Counter[int] = Counter(t for row in pool for t in set(row["tag_ids"]))
    categories = archived_categories()
    out: Rows = []
    for tag_id, count in counts.items():
        share = count / n
        base_share = baseline[tag_id] / n_pool if n_pool else 0.0
        out.append({
            "dataset": dataset, "tag_id": tag_id, "tag": names[tag_id], "count": count, "share": share,
            "median_position": float(statistics.median(positions[tag_id])),
            "defining_tag": tag_id == defining_tag, "baseline_count": baseline[tag_id], "baseline_share": base_share,
            "share_ratio": _ratio(share, base_share),
            "archived_category": " / ".join(categories.get(names[tag_id].strip(), [])) or None,
        })
    out.sort(key=lambda r: (-r["count"], r["tag"], r["tag_id"]))
    return out


def genre_frequency(dataset: str, top: Rows, pool: Rows, kinds: dict[int, str]) -> Rows:
    n, n_pool = len(top), len(pool)
    counts: Counter[int] = Counter()
    names: dict[int, str] = {}
    for row in top:
        for genre_id, name in zip(row["genre_ids"], row["genres"]):
            counts[genre_id] += 1
            names.setdefault(genre_id, name)
    baseline: Counter[int] = Counter(g for row in pool for g in set(row["genre_ids"]))
    out: Rows = []
    for genre_id, count in counts.items():
        share = count / n
        base_share = baseline[genre_id] / n_pool if n_pool else 0.0
        out.append({"dataset": dataset, "genre_id": genre_id, "genre": names[genre_id],
                    "kind": kinds.get(genre_id, "unmapped"), "count": count, "share": share,
                    "baseline_count": baseline[genre_id], "baseline_share": base_share,
                    "share_ratio": _ratio(share, base_share)})
    out.sort(key=lambda r: (-r["count"], r["genre"], r["genre_id"]))
    return out


def _tag_sets(top: Rows, defining_tag: int | None) -> tuple[list[frozenset[int]], dict[int, str]]:
    names: dict[int, str] = {}
    sets = []
    for row in top:
        tags = frozenset(t for t in row["tag_ids"] if t != defining_tag)
        sets.append(tags)
        for tag_id, name in zip(row["tag_ids"], row["tags"]):
            names.setdefault(tag_id, name)
    return sets, names


def combinations_table(dataset: str, top: Rows, defining_tag: int | None, max_size: int, min_support: int) -> Rows:
    n = len(top)
    sets, names = _tag_sets(top, defining_tag)
    counts: Counter[int] = Counter(t for s in sets for t in s)
    frequent = {frozenset([t]): c for t, c in counts.items() if c >= min_support}
    support: dict[frozenset[int], int] = dict(frequent)
    level = sorted(frequent, key=lambda s: sorted(s))
    out: Rows = []
    for k in range(2, max_size + 1):
        items = sorted({t for s in level for t in s})
        candidates = [frozenset(c) for c in combinations(items, k)
                      if all(frozenset(sub) in support for sub in combinations(c, k - 1))]
        level = []
        for cand in candidates:
            s = sum(1 for game in sets if cand <= game)
            if s < min_support:
                continue
            support[cand] = s
            level.append(cand)
            if k >= 3 and any(support[frozenset(sub)] == s for sub in combinations(sorted(cand), 2)):
                continue  # dropped: the triple adds nothing beyond one of its pairs
            members = sorted(cand)
            lift = s * n ** (k - 1) / math.prod(counts[t] for t in members)
            row: dict[str, Any] = {
                "dataset": dataset, "size": k, "tag_ids": members, "tags": [names[t] for t in members],
                "support_count": s, "support_share": s / n, "lift": lift,
                "confidence_a_to_b": s / counts[members[0]] if k == 2 else None,
                "confidence_b_to_a": s / counts[members[1]] if k == 2 else None,
            }
            out.append(row)
    out.sort(key=lambda r: (-r["support_count"], r["size"], r["tag_ids"]))
    return out


def benjamini_hochberg(pvalues: list[float]) -> list[float]:
    m = len(pvalues)
    order = sorted(range(m), key=lambda i: pvalues[i])
    q = [0.0] * m
    running = 1.0
    for rank in range(m, 0, -1):
        i = order[rank - 1]
        running = min(running, pvalues[i] * m / rank)
        q[i] = min(running, 1.0)
    return q


def associations_table(dataset: str, top: Rows, defining_tag: int | None, min_support: int) -> Rows:
    n = len(top)
    sets, names = _tag_sets(top, defining_tag)
    counts: Counter[int] = Counter(t for s in sets for t in s)
    tags = sorted(t for t, c in counts.items() if c >= min_support)
    pair_counts: Counter[tuple[int, int]] = Counter()
    for s in sets:
        pair_counts.update(combinations(sorted(t for t in s if counts[t] >= min_support), 2))
    out: Rows = []
    for a, b in combinations(tags, 2):
        ca, cb, cab = counts[a], counts[b], pair_counts[(a, b)]
        n11, n10, n01 = cab, ca - cab, cb - cab
        n00 = n - n11 - n10 - n01
        denom = ca * (n - ca) * cb * (n - cb)
        phi = (n11 * n00 - n10 * n01) / math.sqrt(denom) if denom else None
        p = float(fisher_exact([[n11, n10], [n01, n00]], alternative="two-sided").pvalue)
        out.append({"dataset": dataset, "tag_id_a": a, "tag_a": names[a], "tag_id_b": b, "tag_b": names[b],
                    "count_a": ca, "count_b": cb, "count_ab": cab, "phi": phi, "lift": cab * n / (ca * cb),
                    "jaccard": cab / (ca + cb - cab), "fisher_p": min(p, 1.0), "bh_q": None})
    for row, q in zip(out, benjamini_hochberg([r["fisher_p"] for r in out])):
        row["bh_q"] = q
    out.sort(key=lambda r: (r["phi"] is None, -abs(r["phi"]) if r["phi"] is not None else 0.0,
                            r["tag_id_a"], r["tag_id_b"]))
    return out


def content_flag_rows(dataset: str, top: Rows, flags: list[str]) -> tuple[Rows, dict[str, int]]:
    rows = [{"dataset": dataset, "flag": flag, "appid": r["appid"], "name": r["name"], "rank": r["rank"]}
            for flag in flags for r in top if flag in r["content_flags"]]
    return rows, {flag: sum(1 for r in top if flag in r["content_flags"]) for flag in flags}

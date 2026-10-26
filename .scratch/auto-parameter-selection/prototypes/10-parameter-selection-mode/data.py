"""PROTOTYPE (throwaway) data for the Parameter Selection mode prototype: real grid results, the selection rule,
live per-pair detail, and validation numbers. Nothing imports this outside the prototype.

- The grid: `../05-grid-run/pairs.csv` and the Neighbour Agreement CSV (ticket 05's run of the decided procedure).
- The selection: ticket 06's Pair Constraints, near-best set and tie-break, recomputed here on every confirm.
- An inspected pair's Admissible Partitions and Clusters: computed live by the grid-run prototype's `compute_pair`
  (0.2-4 s, then cached in memory).
- Validation: the ticket 07 pilot (5 nulls + 5 subsamples) for the five default-constraint pairs; any other pair
  gets seeded illustrative numbers. Per-Cluster Jaccard is always illustrative (the pilot didn't compute it).
"""

from __future__ import annotations

import csv
import functools
import hashlib
import os
import random
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
GRID = HERE.parent / "05-grid-run"

DATASETS = ("overall", "puzzle", "rpg", "simulation", "strategy")
G_VALUES = list(range(3, 21))
S_VALUES = list(range(2, 13))
PAIRS = [(g, s) for g in G_VALUES for s in S_VALUES if s <= g]  # 153, row-major: the simulated job's order
BUILD_ID = "20261008T221504Z-7a23ae9f"

DEFAULTS = {"retention_min": 0.50, "isolated_max": 0.10, "lcc_min": 0.90, "neighbours_min": 2, "mtc_max": None,
            "tolerance": 0.05}
CONSTRAINT_LABEL = {
    "retention_min": "Minimum Information Retention", "isolated_max": "Maximum share of isolated tags",
    "lcc_min": "Minimum LCC share", "neighbours_min": "Minimum comparable neighbours (different graph)",
    "mtc_max": "Maximum Multi-Tag Clusters", "tolerance": "Tolerance (absolute ARI)",
}
# reason code -> (one-letter heatmap mark, plain words); order = the cumulative exclusion order
REASONS = {
    "no_selected_partition": ("P", "no Selected Partition"),
    "no_neighbour_agreement": ("A", "no Neighbour Agreement"),
    "too_few_comparable_neighbours": ("N", "too few comparable neighbours"),
    "retention_below_min": ("R", "Information Retention below the minimum"),
    "isolated_share_above_max": ("I", "isolated share above the maximum"),
    "lcc_share_below_min": ("L", "LCC share below the minimum"),
    "too_many_clusters": ("K", "too many Multi-Tag Clusters"),
}

METRICS = {  # key -> (column, label, descriptive?, higher is better?)
    "na": ("na_mean", "Neighbour Agreement", False, True),
    "na_min": ("na_min", "Neighbour Agreement (minimum)", False, True),
    "retention": ("Information Retention", "Information Retention", False, True),
    "isolated": ("Isolated share of tags", "Fragmentation: isolated share", False, False),
    "mtc": ("Multi-Tag Clusters (Selected Partition)", "Fragmentation: Multi-Tag Clusters", False, None),
    "snf": ("Seed-Noise Floor (min ARI)", "Seed-Noise Floor", False, True),
    "width": ("Domain width (b − a)", "Optimality Domain width", False, True),
    "gamma": ("Selected Resolution", "Selected Resolution", False, None),
    "tags": ("Tags", "Tags", False, None),
    "q": ("Q at the Selected Resolution (descriptive)", "Q", True, None),
    "coverage": ("Weighted Coverage (descriptive)", "Weighted Coverage", True, None),
    "silhouette": ("Jaccard silhouette (descriptive)", "Jaccard silhouette", True, None),
}


def _num(x: str):
    if x in ("", None):
        return None
    if x in ("True", "False"):
        return x == "True"
    try:
        return int(x)
    except ValueError:
        try:
            return float(x)
        except ValueError:
            return x


@functools.cache
def grid() -> dict[tuple[str, int, int], dict]:
    rows = {}
    with open(GRID / "pairs.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows[(r["dataset"], int(r["g"]), int(r["s"]))] = {k: _num(v) for k, v in r.items()}
    with open(GRID / "neighbour-agreement-by-pair.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            row = rows[(r["dataset"], int(r["g"]), int(r["s"]))]
            row["na_mean"], row["na_min"] = _num(r["mean_ari"]), _num(r["min_ari"])
    for row in rows.values():
        row["has_partition"] = not row["no_selection_reason"]
        row["neighbours_diff"] = (row["na_comparable"] or 0) - (row["na_identical_comparable"] or 0)
    return rows


def reasons(row: dict, c: dict) -> list[str]:
    out = []
    if not row["has_partition"]:
        out.append("no_selected_partition")
    if row["na_mean"] is None:
        out.append("no_neighbour_agreement")
    if row["neighbours_diff"] < c["neighbours_min"]:
        out.append("too_few_comparable_neighbours")
    if row["Information Retention"] is None or row["Information Retention"] < c["retention_min"] - 1e-12:
        out.append("retention_below_min")
    if row["Isolated share of tags"] is None or row["Isolated share of tags"] > c["isolated_max"] + 1e-12:
        out.append("isolated_share_above_max")
    lcc = row["LCC share of non-isolated tags"]
    if lcc is None or lcc < c["lcc_min"] - 1e-12:
        out.append("lcc_share_below_min")
    mtc = row["Multi-Tag Clusters (Selected Partition)"]
    if c["mtc_max"] is not None and mtc is not None and mtc > c["mtc_max"]:
        out.append("too_many_clusters")
    return out


def select(dataset: str, c: dict, done: set[tuple[int, int]] | None = None) -> dict:
    """Ticket 06 over the computed pairs. `done` limits it to a partial grid (the result is then marked partial)."""
    rows = grid()
    pairs = [p for p in PAIRS if done is None or p in done]
    why = {p: reasons(rows[(dataset, *p)], c) for p in pairs}
    qual = [p for p in pairs if not why[p]]
    alone = {k: sum(k in why[p] for p in pairs) for k in REASONS}
    cumulative, left = {}, set(pairs)
    for k in REASONS:
        hit = {p for p in left if k in why[p]}
        cumulative[k] = len(hit)
        left -= hit
    res = {"dataset": dataset, "constraints": dict(c), "why": why, "qualifying": qual, "alone": alone,
           "cumulative": cumulative, "n_pairs": len(pairs), "partial": done is not None and len(pairs) < len(PAIRS),
           "n_with_partition": sum(rows[(dataset, *p)]["has_partition"] for p in pairs)}
    if not qual:
        res.update(status="no_qualifying_pair", chosen=None, near_best=[], max_na=None, max_at=[])
        return res
    na = {p: rows[(dataset, *p)]["na_mean"] for p in qual}
    top = max(na.values())
    near = sorted(p for p in qual if na[p] >= top - c["tolerance"] - 1e-12)
    res.update(status="ok", chosen=min(near), near_best=near, max_na=top,
               max_at=sorted(p for p in qual if abs(na[p] - top) <= 1e-12))
    return res


def is_custom(c: dict) -> list[str]:
    return [k for k in DEFAULTS if c.get(k) != DEFAULTS[k]]


def neighbours_done(p: tuple[int, int], done: set) -> bool:
    g, s = p
    nb = [(g - 1, s), (g + 1, s), (g, s - 1), (g, s + 1)]
    return p in done and all(q in done for q in nb if q in set(PAIRS))


# ----------------------------------------------------------------------------- the Workbench γ and seed (ticket 09)

# Facts from prototypes/09-apply-reproduction for the five chosen pairs; every other pair: the prototype assumes
# the main seed reproduces at the Workbench resolution (the real search is cached per graph).
WB_SEED = {("puzzle", 14, 2): "scan seed 2"}
NOT_REPRODUCED = {("rpg", 9, 7): 0.83}  # PROTOTYPE: an invented example of the 6 `not_reproduced` pairs


def workbench(dataset: str, g: int, s: int) -> dict:
    row = grid()[(dataset, g, s)]
    key = (dataset, g, s)
    if not row["has_partition"]:
        return {"ok": False, "reason": row["no_selection_reason"]}
    if key in NOT_REPRODUCED:
        return {"ok": True, "gamma": round(row["Selected Resolution"], 2), "seed": "main seed",
                "reproduced": False, "ari": NOT_REPRODUCED[key]}
    return {"ok": True, "gamma": row["workbench_resolution"], "seed": WB_SEED.get(key, "main seed"),
            "reproduced": True}


# ----------------------------------------------------------------------------- live per-pair detail


_READY = False


def _init():
    global _READY, G
    if _READY:
        return
    os.chdir(REPO)
    sys.path.insert(0, str(GRID))
    import grid_run as G  # noqa: N812

    G.init_worker(DATASETS)
    _READY = True


@functools.cache
def tag_names(dataset: str) -> dict[int, str]:
    _init()
    from steamstudy.network.graph import build_network

    games, context, base = G._W["data"][dataset]
    return build_network(games, base, context).tag_names


@functools.cache
def pair_detail(dataset: str, g: int, s: int) -> dict:
    """Admissible Partitions (for the CHAMP plot) and the Selected Partition's Clusters, computed live."""
    _init()
    from steamstudy.network.cluster import label_clusters

    rec = G.compute_pair((dataset, g, s, False))
    names = tag_names(dataset)
    out = {"two_m": rec.get("two_m"), "admissible": rec.get("admissible", []), "clusters": [], "n_one": 0}
    sel = rec.get("selected")
    if sel:
        m = sel["membership"]
        nodes = rec["nodes"]
        comms = [frozenset(nodes[i] for i, x in enumerate(m) if x == c) for c in range(max(m) + 1)]
        for cl in label_clusters(comms):
            if cl.size >= 2:
                out["clusters"].append({"label": cl.label, "tags": sorted(names[t] for t in cl.members)})
            else:
                out["n_one"] += 1
    return out


# ----------------------------------------------------------------------------- validation (ticket 07 template)

# The ticket 07 pilot (prototypes/07-validation-pilot/output.txt): 5 nulls and 5 subsamples, not 100 + 100.
PILOT = {
    "overall": dict(pair=(17, 2), obs_q=0.067, null_q=[-.015, -.012, -.017, -.018, -.021], obs_w=0.158,
                    null_w=[.020, .028, .021], null_fail={"too_few_multi_tag_clusters": 2}, gs=(13, 2),
                    resel=[.692, .567, .646, .716, .725], fixed=[.859, .567, .812, .902, .859], degenerate=0),
    "puzzle": dict(pair=(14, 2), obs_q=0.091, null_q=[.013, .009, .010, .007, .012], obs_w=0.092,
                   null_w=[.045, .065, .087, .069, .084], null_fail={}, gs=(11, 2),
                   resel=[.511, .894, .618, .381, .410], fixed=[.444, .894, .618, .381, .500], degenerate=0),
    "rpg": dict(pair=(14, 12), obs_q=0.131, null_q=[.017, .008, .019, .031, .025], obs_w=0.666,
                null_w=[.301, .281, .181, .257, .184], null_fail={}, gs=(11, 9),
                resel=[.424, .643, .607, .714, .583], fixed=[.608, .644, .588, .764, .626], degenerate=0),
    "simulation": dict(pair=(14, 5), obs_q=0.303, null_q=[.145, .153, .159, .144, .152], obs_w=0.469,
                       null_w=[.046, .122, .059, .119, .059], null_fail={}, gs=(11, 4),
                       resel=[1.0, 1.0, .908, .573, .504], fixed=[1.0, 1.0, .908, .845, .915], degenerate=0),
    "strategy": dict(pair=(14, 2), obs_q=0.158, null_q=[.036, .040, .042, .038, .042], obs_w=0.260,
                     null_w=[.037, .058, .054, .063, .067], null_fail={}, gs=(11, 2),
                     resel=[.884, .515, .679, .668], fixed=[.932, .329, .679, .558, .668], degenerate=1),
}


def _rng(*key) -> random.Random:
    return random.Random(int(hashlib.sha256(repr(key).encode()).hexdigest()[:12], 16))


def validation(dataset: str, g: int, s: int) -> dict:
    p = PILOT.get(dataset)
    row = grid()[(dataset, g, s)]
    if p and p["pair"] == (g, s):
        v = dict(p, illustrative=False)
    else:  # PROTOTYPE: seeded illustrative numbers in the pilot's ranges
        r = _rng(dataset, g, s)
        q = row["Q at the Selected Resolution (descriptive)"] or 0.1
        w = row["Domain width (b − a)"] or 0.1
        v = dict(pair=(g, s), obs_q=q, null_q=[q * r.uniform(-.3, .55) for _ in range(5)], obs_w=w,
                 null_w=[w * r.uniform(.1, .7) for _ in range(r.randint(3, 5))], null_fail={}, gs=(g * 4 // 5, max(2, s * 4 // 5)),
                 resel=[r.uniform(.4, .95) for _ in range(5)], fixed=[r.uniform(.5, 1) for _ in range(5)], degenerate=0,
                 illustrative=True)
    v["n_null"] = len(v["null_q"])
    v["n_null_with"] = len(v["null_w"])
    v["reach"] = sum(x >= v["obs_q"] for x in v["null_q"])
    v["wider_than"] = sum(v["obs_w"] > x for x in v["null_w"])
    v["n_sub"] = len(v["resel"]) + v["degenerate"]
    return v


def cluster_jaccard(dataset: str, g: int, s: int, labels: list[str]) -> list[dict]:
    """PROTOTYPE: illustrative per-Cluster Hennig Jaccard, both arms (the pilot never computed it)."""
    r = _rng("jac", dataset, g, s)
    out = []
    for lab in labels:
        base = r.uniform(.35, .98)
        out.append({"label": lab, "resel": base, "fixed": min(1.0, base + r.uniform(0, .2)),
                    "low_resel": r.randint(0, 40) if base > .5 else r.randint(50, 90),
                    "retention": r.uniform(.85, 1.0), "absent": r.choice([0, 0, 0, 1])})
    return out


def pct(xs: list[float], q: float) -> float:
    xs = sorted(xs)
    return xs[min(len(xs) - 1, max(0, round(q * (len(xs) - 1))))]


def med(xs: list[float]) -> float:
    return statistics.median(xs)

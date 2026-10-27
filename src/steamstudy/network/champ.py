"""CHAMP, the self-consistent γ estimate and the Selected Partition, in numpy (no Leiden here).

Each partition is a line Q(γ) = Â − γP̂ with Â = 2·(internal weight) and P̂ = Σ_c κ_c²/2m [Weir et al. 2017
eq. 2]. The upper envelope over [0, γ_end] gives each Admissible Partition its Optimality Domain [a, b]
[Weir et al. 2017 §2]. γ̂ = (ω_in − ω_out)/(ln ω_in − ln ω_out) [Newman 2016 eqs. 15–18] is evaluated once per
partition, and a partition is stable when a ≤ γ̂ ≤ b [Gibson & Mucha 2022]. The scan ends at Gibson & Mucha's
γ_max(K) at K = n_e [GM22 SI §J].
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass
from functools import lru_cache
from typing import Any, Protocol

import numpy as np

RTOL = 1e-12


# ----------------------------------------------------------------------------- γ range


@lru_cache(maxsize=None)
def gamma_max_K(K: int) -> float:
    """GM22 SI §J: the maximum of γ̂(ω_in, ω_out) on ω_in + (K − 1)·ω_out = K, ω_out ∈ (0, 1). Undefined for K < 2."""
    from scipy.optimize import minimize_scalar

    if K < 2:
        raise ValueError(f"γ_max(K) needs K >= 2, got {K}")

    def gamma_hat(w_out: float) -> float:
        w_in = K - (K - 1) * w_out
        return (w_in - w_out) / (math.log(w_in) - math.log(w_out))

    res = minimize_scalar(lambda x: -gamma_hat(x), bounds=(1e-12, 1 - 1e-12), method="bounded",
                          options={"xatol": 1e-12})
    return float(-res.fun)


def scan_gammas(n_e: int, step: float) -> list[float]:
    """round(step·i, 2) for i = 0 … ⌈γ_max(n_e)/step − 1e-9⌉."""
    return [round(step * i, 2) for i in range(math.ceil(gamma_max_K(n_e) / step - 1e-9) + 1)]


# ----------------------------------------------------------------------------- scan dedup


class _Run(Protocol):
    @property
    def gamma(self) -> float: ...
    @property
    def seed(self) -> int: ...
    @property
    def membership(self) -> np.ndarray: ...
    @property
    def capped(self) -> bool: ...


def canonical(membership: Sequence[int] | np.ndarray) -> np.ndarray:
    """Labels renumbered in order of first occurrence."""
    labels = np.asarray(membership)
    _, first, inverse = np.unique(labels, return_index=True, return_inverse=True)
    rank = np.empty(len(first), dtype=np.int64)
    rank[np.argsort(first)] = np.arange(len(first))
    return rank[inverse]


@dataclass
class Scan:
    """The scan's unique partitions (canonical, all tags), each with its first (γ, seed) and hit count."""

    memberships: list[np.ndarray]
    first: list[tuple[float, int]]
    hits: list[int]
    n_runs: int
    capped_runs: int


def dedup(runs: Iterable[_Run]) -> Scan:
    """Runs in scan order (γ ascending, then seeds)."""
    index: dict[bytes, int] = {}
    scan = Scan([], [], [], 0, 0)
    for run in runs:
        m = canonical(run.membership)
        scan.n_runs += 1
        scan.capped_runs += bool(run.capped)
        key = m.tobytes()
        if key in index:
            scan.hits[index[key]] += 1
        else:
            index[key] = len(scan.memberships)
            scan.memberships.append(m)
            scan.first.append((float(run.gamma), int(run.seed)))
            scan.hits.append(1)
    return scan


# ----------------------------------------------------------------------------- coefficients


@dataclass(frozen=True)
class EdgeArrays:
    """A graph as node count and edge arrays (u < v, node indices in sorted tag order)."""

    n: int
    u: np.ndarray
    v: np.ndarray
    w: np.ndarray

    @property
    def strength(self) -> np.ndarray:
        return np.bincount(self.u, self.w, self.n) + np.bincount(self.v, self.w, self.n)

    @property
    def edged(self) -> np.ndarray:
        return (np.bincount(self.u, minlength=self.n) + np.bincount(self.v, minlength=self.n)) > 0

    @property
    def n_e(self) -> int:
        return int(self.edged.sum())

    @property
    def two_m(self) -> float:
        return float(self.strength.sum())


def edge_arrays(n: int, edges: Iterable[tuple[int, int, float]]) -> EdgeArrays:
    rows = list(edges)
    return EdgeArrays(n, np.array([e[0] for e in rows], dtype=np.int64), np.array([e[1] for e in rows], dtype=np.int64),
                      np.array([float(e[2]) for e in rows], dtype=np.float64))


def partition_coefficients(memberships: Sequence[np.ndarray], g: EdgeArrays) -> tuple[np.ndarray, np.ndarray]:
    """(Â, P̂) per partition. Isolated tags have no strength and change neither."""
    k, two_m = g.strength, g.two_m
    a = np.empty(len(memberships))
    p = np.empty(len(memberships))
    for i, m in enumerate(memberships):
        a[i] = 2.0 * float(g.w[m[g.u] == m[g.v]].sum())
        p[i] = float((np.bincount(m, k) ** 2).sum()) / two_m
    return a, p


# ----------------------------------------------------------------------------- envelope


@dataclass(frozen=True)
class Domain:
    index: int  # into the memberships given
    a: float
    b: float
    clipped_high: bool


def tolerance(a_hat: np.ndarray, p_hat: np.ndarray, gamma_end: float) -> float:
    """One relative tolerance scaled to the size of Q over the range."""
    if len(a_hat) == 0:
        return RTOL
    return RTOL * max(1.0, float(np.abs(a_hat).max()), float(np.abs(p_hat).max()) * gamma_end)


def admissible(a_hat: np.ndarray, p_hat: np.ndarray, memberships: Sequence[np.ndarray],
               gamma_end: float) -> tuple[list[Domain], int]:
    """The upper envelope over [0, γ_end]: Optimality Domains of positive width, and the twins dropped.

    Twins (identical Â, P̂) keep the canonical membership that sorts first. At a breakpoint the smallest P̂ wins.
    """
    tol = tolerance(a_hat, p_hat, gamma_end)
    kept: list[int] = []
    for i in sorted(range(len(memberships)), key=lambda i: tuple(memberships[i].tolist())):
        if kept and np.any((np.abs(a_hat[kept] - a_hat[i]) <= tol) & (np.abs(p_hat[kept] - p_hat[i]) <= tol)):
            continue
        kept.append(i)
    idx = np.array(sorted(kept), dtype=np.int64)
    a, p = a_hat[idx], p_hat[idx]
    q = a.copy()  # Q at γ = 0
    cand = np.flatnonzero(q >= q.max() - tol)
    cur = int(cand[np.argmin(p[cand])])
    start = 0.0
    out: list[Domain] = []
    while True:
        dp = p[cur] - p
        ok = dp > tol  # only flatter lines can overtake as γ grows
        x = np.full(len(a), np.inf)
        x[ok] = (a[cur] - a[ok]) / dp[ok]
        x = np.maximum(x, start)
        nxt = float(x.min())
        if nxt >= gamma_end:
            if gamma_end > start + tol:
                out.append(Domain(int(idx[cur]), start, gamma_end, True))
            return out, len(memberships) - len(kept)
        cand = np.flatnonzero(x <= nxt + tol)
        new = int(cand[np.argmin(p[cand])])
        if nxt > start + tol:  # partitions on top at only one point are dropped
            out.append(Domain(int(idx[cur]), start, nxt, False))
        cur, start = new, nxt


# ----------------------------------------------------------------------------- γ̂


@dataclass(frozen=True)
class Estimate:
    omega_in: float | None
    omega_out: float | None
    gamma_hat: float | None
    reason: str | None  # no_edges, one_group, no_cross_weight, not_assortative


def estimate(a_hat: float, p_hat: float, membership: np.ndarray, g: EdgeArrays) -> Estimate:
    """Newman eq. 15 with eqs. 17–18, once (Gibson & Mucha's fixed-point test). The guards use counts."""
    if len(g.w) == 0:
        return Estimate(None, None, None, "no_edges")
    if len(np.unique(membership[g.edged])) < 2:
        return Estimate(None, None, None, "one_group")
    if not bool((membership[g.u] != membership[g.v]).any()):
        return Estimate(None, None, None, "no_cross_weight")
    two_m = g.two_m
    w_in, w_out = a_hat / p_hat, (two_m - a_hat) / (two_m - p_hat)
    if a_hat <= p_hat:
        return Estimate(w_in, w_out, None, "not_assortative")
    return Estimate(w_in, w_out, (w_in - w_out) / (math.log(w_in) - math.log(w_out)), None)


# ----------------------------------------------------------------------------- results


@dataclass(frozen=True)
class AdmissiblePartition:
    membership: tuple[int, ...]  # canonical, all tags in node order
    a_hat: float
    p_hat: float
    a: float
    b: float
    clipped_high: bool
    omega_in: float | None
    omega_out: float | None
    gamma_hat: float | None
    reason: str | None
    target: int | None  # the Admissible Partition whose domain holds γ̂, else none
    stable: bool
    n_multi: int
    n_one: int
    n_one_isolated: int
    first_gamma: float
    first_seed: int
    hits: int

    @property
    def width(self) -> float:
        return self.b - self.a

    @property
    def midpoint(self) -> float:
        return (self.a + self.b) / 2


@dataclass(frozen=True)
class ChampResult:
    two_m: float
    gamma_end: float
    n_unique: int
    n_twins: int
    admissible: tuple[AdmissiblePartition, ...]
    selected: int | None  # index into `admissible`
    reason: str | None  # no_edges, no_stable_partition, too_few_multi_tag_clusters

    @property
    def selected_partition(self) -> AdmissiblePartition | None:
        return None if self.selected is None else self.admissible[self.selected]

    @property
    def selected_resolution(self) -> float | None:
        """The exact midpoint of the Selected Partition's domain."""
        p = self.selected_partition
        return None if p is None else p.midpoint

    def envelope_at(self, gamma: float) -> AdmissiblePartition | None:
        """The Admissible Partition on top at γ (the lower one at a breakpoint), or None outside [0, γ_end]."""
        return next((p for p in self.admissible if p.a <= gamma <= p.b), None)

    def q_at(self, gamma: float) -> float | None:
        """The envelope's normalised Q at γ: (Â − γP̂)/2m of the partition on top."""
        p = self.envelope_at(gamma)
        return None if p is None else (p.a_hat - gamma * p.p_hat) / self.two_m


def select(partitions: Sequence[AdmissiblePartition], min_multi: int, tol: float) -> tuple[int | None, str | None]:
    """Stable Partitions with ≥ min_multi Multi-Tag Clusters; the widest domain, then the lower midpoint, then
    canonical membership order."""
    stable = [i for i, p in enumerate(partitions) if p.stable]
    if not stable:
        return None, "no_stable_partition"
    enough = [i for i in stable if partitions[i].n_multi >= min_multi]
    if not enough:
        return None, "too_few_multi_tag_clusters"
    widest = max(partitions[i].width for i in enough)
    ties = [i for i in enough if partitions[i].width >= widest - tol]
    return min(ties, key=lambda i: (partitions[i].midpoint, partitions[i].membership)), None


def champ(scan: Scan, g: EdgeArrays, gamma_end: float, min_multi: int) -> ChampResult:
    """Admissible Partitions over [0, γ_end], their γ̂ and stability, and the Selected Partition."""
    if len(g.w) == 0:
        return ChampResult(0.0, gamma_end, len(scan.memberships), 0, (), None, "no_edges")
    a_hat, p_hat = partition_coefficients(scan.memberships, g)
    domains, n_twins = admissible(a_hat, p_hat, scan.memberships, gamma_end)
    edged = g.edged
    top = gamma_max_K(g.n_e)
    rows = []
    for d in domains:
        m = scan.memberships[d.index]
        est = estimate(float(a_hat[d.index]), float(p_hat[d.index]), m, g)
        if est.gamma_hat is not None:
            assert est.gamma_hat <= top * (1 + 1e-9) and top <= gamma_end + 1e-9, "γ̂ above γ_max(n_e) (GM22 §J.2)"
        sizes = np.bincount(m)
        in_one = sizes[m] == 1
        rows.append((d, m, est, int((sizes >= 2).sum()), int((sizes == 1).sum()), int((in_one & ~edged).sum())))
    out = []
    for d, m, est, n_multi, n_one, n_one_isolated in rows:
        g_hat = est.gamma_hat
        target = None if g_hat is None else next((j for j, (o, *_) in enumerate(rows) if o.a <= g_hat <= o.b), None)
        out.append(AdmissiblePartition(
            membership=tuple(int(x) for x in m), a_hat=float(a_hat[d.index]), p_hat=float(p_hat[d.index]),
            a=float(d.a), b=float(d.b), clipped_high=d.clipped_high, omega_in=est.omega_in, omega_out=est.omega_out,
            gamma_hat=g_hat, reason=est.reason, target=target, stable=g_hat is not None and d.a <= g_hat <= d.b,
            n_multi=n_multi, n_one=n_one, n_one_isolated=n_one_isolated, first_gamma=scan.first[d.index][0],
            first_seed=scan.first[d.index][1], hits=scan.hits[d.index]))
    selected, reason = select(out, min_multi, tolerance(a_hat, p_hat, gamma_end))
    return ChampResult(g.two_m, gamma_end, len(scan.memberships), n_twins, tuple(out), selected, reason)


def to_json(result: ChampResult) -> dict[str, Any]:
    data = asdict(result)
    for p in data["admissible"]:
        p["membership"] = list(p["membership"])
    return data


def from_json(data: dict[str, Any]) -> ChampResult:
    parts = tuple(AdmissiblePartition(**{**p, "membership": tuple(p["membership"])}) for p in data["admissible"])
    return ChampResult(**{**data, "admissible": parts})

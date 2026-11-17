"""PROTOTYPE (throwaway) for ticket 04: "Which measures survive on the real Builds?"

Reads the stored Automatic Parameter Selection runs of one Build, takes each dataset's pick (the starred
cell under the default Pair Constraints) and its stored Selected Partition, and scores every Cluster Match
between every two datasets with Jaccard and the shortlisted measures of research 01.

Run:  uv run python .scratch/cluster-comparison/prototypes/04-measures-on-real-builds/run.py
Out:  report.md and matches.csv beside this file. Nothing else is written.
"""

from __future__ import annotations

import csv
import itertools
import statistics
import sys
from pathlib import Path

from scipy.stats import spearmanr
from sklearn.metrics import adjusted_mutual_info_score, adjusted_rand_score

from steamstudy.app import ps_cache, ps_view
from steamstudy.app.loader import load_build
from steamstudy.network import selection as SEL

HERE = Path(__file__).parent
ROOT = HERE.parents[3]
BUILD = ROOT / "builds" / "20261005T062558Z-full" / "20261008T221504Z-7a23ae9f"
ps_cache.NAME_LENGTH = 64  # this Build's cache predates the 16-digit folder names (in memory only)
MINIMA = (0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5)


def f(x, nd=2):
    return "—" if x is None else f"{x:.{nd}f}"


def load(ctx):
    settings, constraints = ps_view.defaults_of(ctx)
    out = {}
    for d in [x.key for x in ctx.datasets]:
        view = ps_view.dataset_view(ctx, settings, d, constraints, constraints)
        if view.star is None:
            print(f"{d}: no pick ({view.status})", file=sys.stderr)
            continue
        r = view.result(view.star)
        games = ctx.games(d)
        names, count = {}, {}
        for g in games:
            for t, n in zip(g.tag_ids, g.tags):
                names[t] = n
                count[t] = count.get(t, 0) + 1
        clusters = SEL.clusters_of(r.nodes, r.selected)
        out[d] = dict(
            key=d, pair=view.star, gamma=r.selected_resolution, nodes=set(r.nodes), edged=set(r.edged),
            label=dict(zip(r.nodes, r.selected)), clusters=clusters, names=names, count=count,
            multi=[c for c in clusters if c.size >= 2], n_one=sum(c.size == 1 for c in clusters),
            floor=(r.seed_noise or {}).get("floor"), hidden=set(settings.hidden_tag_ids(ctx.context(d))),
            defining=ctx.context(d).defining_tag_id, wb=(r.workbench or {}).get("flag"),
        )
    return out


def matches(A, B):
    """Every Cluster Match of A's Multi-Tag Clusters with B's, scored both ways (ticket 02)."""
    common = A["nodes"] & B["nodes"]
    N = len(common)
    rows = []
    for ca in A["multi"]:
        for cb in B["multi"]:
            shared = ca.members & cb.members
            n = len(shared)
            if not n:
                continue
            a, b = ca.size, cb.size
            a2, b2 = len(ca.members & common), len(cb.members & common)
            judged = a2 >= 2 and b2 >= 2
            exp = a2 * b2 / N
            rows.append(dict(
                A=A["key"], B=B["key"], ca=ca.label, cb=cb.label, a=a, b=b, n=n, a_common=a2, b_common=b2,
                jaccard=n / (a + b - n), cont_a=n / a, cont_b=n / b, cont_min=min(n / a, n / b),
                cont_max=max(n / a, n / b),
                jaccard_common=n / (a2 + b2 - n) if judged else None,
                expected=exp, lift=n / exp, N=N,
                shared=sorted(A["names"][t] for t in shared),
                only_a=sorted(A["names"][t] for t in ca.members - shared),
                only_b=sorted(B["names"][t] for t in cb.members - shared),
            ))
    return rows


def flags(A, B, rows, minimum):
    """Per Multi-Tag Cluster of A: best match, and the flags of ticket 02."""
    common = A["nodes"] & B["nodes"]
    in_multi_b = set().union(*[c.members for c in B["multi"]]) if B["multi"] else set()
    out = []
    for ca in A["multi"]:
        mine = [r for r in rows if r["ca"] == ca.label]
        best = max((r["jaccard"] for r in mine), default=None)
        if not (ca.members & common):
            flag = "not in B's network"
        elif not (ca.members & in_multi_b):
            flag = "no overlap"
        elif best < minimum:
            flag = "no match above the minimum"
        else:
            flag = ""
        out.append(dict(label=ca.label, size=ca.size, n_matches=len(mine), best=best, flag=flag,
                        n_above=sum(r["jaccard"] >= minimum for r in mine)))
    return out


def overview(A, B, rows):
    common = A["nodes"] & B["nodes"]
    compared = sorted(t for t in common if t in (A["edged"] | B["edged"]))
    la, lb = [A["label"][t] for t in compared], [B["label"][t] for t in compared]
    ok = len(compared) >= 2

    def mean_best(X, side):  # Tag-weighted mean of each Multi-Tag Cluster's best Jaccard
        tot = sum(c.size for c in X["multi"])
        best = {c.label: 0.0 for c in X["multi"]}
        for r in rows:
            best[r[side]] = max(best[r[side]], r["jaccard"])
        return sum(best[c.label] * c.size for c in X["multi"]) / tot if tot else None

    return dict(
        A=A["key"], B=B["key"], n_a=len(A["nodes"]), n_b=len(B["nodes"]), common=len(common),
        share_a=len(common) / len(A["nodes"]), share_b=len(common) / len(B["nodes"]),
        compared=len(compared), k_a=len(A["multi"]), k_b=len(B["multi"]), n_matches=len(rows),
        ari=adjusted_rand_score(la, lb) if ok else None,
        ami=adjusted_mutual_info_score(la, lb) if ok else None,
        best_a=mean_best(A, "ca"), best_b=mean_best(B, "cb"),
    )


def main():
    ctx = load_build(BUILD)
    D = load(ctx)
    keys = list(D)
    L = []
    w = L.append
    w(f"# Prototype 04: measures on Build `{ctx.build_id}`\n")
    w("Each dataset is on its pick (default Pair Constraints) and shows the stored Selected Partition. "
      "Lift, Leiden, no Minimum Months Filter, Genre Tags and the defining Tag hidden.\n")

    w("## 1. The datasets\n")
    w("| Dataset | g | s | γ | Tags in network | Multi-Tag Clusters (sizes) | One-Tag | Seed-Noise Floor | Workbench flag |")
    w("|---|---|---|---|---|---|---|---|---|")
    for d in D.values():
        sizes = ", ".join(str(c.size) for c in d["multi"])
        w(f"| {d['key']} | {d['pair'][0]} | {d['pair'][1]} | {f(d['gamma'])} | {len(d['nodes'])} | "
          f"{len(d['multi'])} ({sizes}) | {d['n_one']} | {f(d['floor'])} | {d['wb'] or 'reproduced'} |")
    w("")
    w("Defining Tag of each dataset, and where it sits in the others:\n")
    w("| Dataset | Defining Tag | Hidden here | " + " | ".join(f"in {k}" for k in keys) + " |")
    w("|---|---|---|" + "---|" * len(keys))
    for d in D.values():
        t = d["defining"]
        if t is None:
            continue
        cells = []
        for k in keys:
            o = D[k]
            if t in o["nodes"]:
                c = next(c for c in o["clusters"] if t in c.members)
                cells.append(f"{c.label} ({c.size})")
            elif t in o["hidden"]:
                cells.append(f"hidden ({o['count'].get(t, 0)} games)")
            else:
                cells.append(f"not in network ({o['count'].get(t, 0)} games)")
        w(f"| {d['key']} | {d['names'].get(t, t)} | {'yes' if t in d['hidden'] else 'no'} | " + " | ".join(cells) + " |")
    w("")

    all_rows, over = [], []
    per_pair = {}
    for ka, kb in itertools.combinations(keys, 2):
        rows = matches(D[ka], D[kb])
        per_pair[(ka, kb)] = rows
        all_rows += rows
        over.append(overview(D[ka], D[kb], rows))

    w("## 2. Pair overview\n")
    w("ARI and AMI on the `selection.link` set (Common Tags with an edge in at least one network). "
      "\"Mean best J\" is the Tag-weighted mean, over a dataset's Multi-Tag Clusters, of each Cluster's best whole-Cluster Jaccard.\n")
    w("| A | B | Tags A | Tags B | Common | % of A | % of B | Compared | Clusters A/B | Matches | ARI | AMI | Mean best J (A) | Mean best J (B) |")
    w("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for o in over:
        w(f"| {o['A']} | {o['B']} | {o['n_a']} | {o['n_b']} | {o['common']} | {o['share_a']:.0%} | {o['share_b']:.0%} | "
          f"{o['compared']} | {o['k_a']}/{o['k_b']} | {o['n_matches']} | {f(o['ari'])} | {f(o['ami'])} | "
          f"{f(o['best_a'])} | {f(o['best_b'])} |")
    w("")
    if len(over) > 2:
        xs = [(o["ari"], o["ami"], (o["best_a"] + o["best_b"]) / 2, min(o["share_a"], o["share_b"])) for o in over]
        w(f"Spearman across the {len(over)} pairs: ARI vs AMI {spearmanr([x[0] for x in xs], [x[1] for x in xs])[0]:.2f}; "
          f"ARI vs mean best J {spearmanr([x[0] for x in xs], [x[2] for x in xs])[0]:.2f}; "
          f"ARI vs smaller Common-Tag share {spearmanr([x[0] for x in xs], [x[3] for x in xs])[0]:.2f}.\n")

    w("## 3. All matches: how the measures relate\n")
    J = [r["jaccard"] for r in all_rows]
    w(f"{len(all_rows)} Cluster Matches over {len(over)} pairs of datasets. "
      f"Jaccard: median {statistics.median(J):.2f}, quartiles {statistics.quantiles(J, n=4)[0]:.2f}–{statistics.quantiles(J, n=4)[2]:.2f}, max {max(J):.2f}.\n")
    w("| Measure vs whole-Cluster Jaccard | Spearman ρ |")
    w("|---|---|")
    for name in ("cont_min", "cont_max", "lift"):
        w(f"| {name} | {spearmanr(J, [r[name] for r in all_rows])[0]:.2f} |")
    jc = [(r["jaccard"], r["jaccard_common"]) for r in all_rows if r["jaccard_common"] is not None]
    w(f"| jaccard_common ({len(jc)} judged) | {spearmanr([x[0] for x in jc], [x[1] for x in jc])[0]:.2f} |")
    w("")
    gaps = [b - a for a, b in jc]
    w(f"Common-Tag Jaccard − Jaccard: median {statistics.median(gaps):.2f}, max {max(gaps):.2f}; "
      f"{sum(g >= 0.1 for g in gaps)} of {len(gaps)} matches gain 0.10 or more. "
      f"{len(all_rows) - len(jc)} matches show \"—\" (a Cluster with fewer than two Common Tags).\n")
    one = [r for r in all_rows if r["n"] == 1]
    w(f"One-shared-Tag matches: {len(one)} of {len(all_rows)} ({len(one) / len(all_rows):.0%}); "
      f"their Jaccard max {max((r['jaccard'] for r in one), default=0):.2f}, their Lift median "
      f"{statistics.median([r['lift'] for r in one]) if one else 0:.1f}, max {max((r['lift'] for r in one), default=0):.1f}. "
      f"Matches with n ≥ 2: Lift median {statistics.median([r['lift'] for r in all_rows if r['n'] >= 2]):.1f}.\n")
    nested = [r for r in all_rows if r["cont_max"] == 1.0 and r["n"] >= 2]
    w(f"Nested matches (one Cluster wholly inside the other, n ≥ 2): {len(nested)}; "
      f"of these {sum(r['jaccard'] < 0.5 for r in nested)} have Jaccard < 0.5 and {sum(r['jaccard'] < 0.3 for r in nested)} < 0.3.\n")

    w("### Matches surviving a minimum, by measure\n")
    w("| Minimum | Jaccard ≥ | of which n = 1 | Clusters with ≥ 2 surviving matches | Clusters flagged \"no match above the minimum\" | min containment ≥ | max containment ≥ |")
    w("|---|---|---|---|---|---|---|")
    n_clusters = sum(len(D[a]["multi"]) + len(D[b]["multi"]) for a, b in per_pair)
    for m in MINIMA:
        multi_side, flagged = 0, 0
        for (ka, kb), rows in per_pair.items():
            for X, Y, sw in ((D[ka], D[kb], False), (D[kb], D[ka], True)):
                rr = rows if not sw else [dict(r, ca=r["cb"], cb=r["ca"]) for r in rows]
                for fl in flags(X, Y, rr, m):
                    multi_side += fl["n_above"] >= 2
                    flagged += fl["flag"] == "no match above the minimum"
        w(f"| {m:.2f} | {sum(j >= m for j in J)} | {sum(r['jaccard'] >= m and r['n'] == 1 for r in all_rows)} | "
          f"{multi_side} of {n_clusters} | {flagged} of {n_clusters} | "
          f"{sum(r['cont_min'] >= m for r in all_rows)} | {sum(r['cont_max'] >= m for r in all_rows)} |")
    w("")

    w("### Where the measures disagree on rank (per Cluster, its matches ranked)\n")
    dis = {"cont_min": 0, "cont_max": 0, "lift": 0}
    tot = 0
    for (ka, kb), rows in per_pair.items():
        for side in ("ca", "cb"):
            for lab in {r[side] for r in rows}:
                mine = [r for r in rows if r[side] == lab]
                if len(mine) < 2:
                    continue
                tot += 1
                top = max(mine, key=lambda r: r["jaccard"])
                for k in dis:
                    dis[k] += max(mine, key=lambda r: r[k]) is not top and max(r[k] for r in mine) > top[k]
    w(f"Clusters with two or more matches: {tot}. Top match differs from Jaccard's when ranked by: "
      + ", ".join(f"{k} {v}" for k, v in dis.items()) + ".\n")

    w("## 4. Flags per pair (minimum = Jaccard 0.20)\n")
    w("| A → B | Multi-Tag Clusters of A | not in B's network | no overlap | no match above 0.20 | matched |")
    w("|---|---|---|---|---|---|")
    for (ka, kb), rows in per_pair.items():
        for X, Y, sw in ((D[ka], D[kb], False), (D[kb], D[ka], True)):
            rr = rows if not sw else [dict(r, ca=r["cb"], cb=r["ca"]) for r in rows]
            fl = flags(X, Y, rr, 0.2)
            c = lambda s: sum(x["flag"] == s for x in fl)
            w(f"| {X['key']} → {Y['key']} | {len(fl)} | {c(chr(110) + 'ot in B' + chr(39) + 's network')} | {c('no overlap')} | "
              f"{c('no match above the minimum')} | {c('')} |")
    w("")

    w("## 5. Every match, pair by pair (ranked by Jaccard)\n")
    w("a, b = Cluster sizes; n = shared Tags; a′, b′ = Common Tags of each Cluster; E = expected overlap a′b′/N.\n")
    for (ka, kb), rows in per_pair.items():
        o = next(x for x in over if x["A"] == ka and x["B"] == kb)
        w(f"### {ka} × {kb}  (Common Tags {o['common']}, ARI {f(o['ari'])})\n")
        w(f"| {ka} | {kb} | a | b | n | J | % of A | % of B | min | a′ | b′ | J common | E | Lift | Shared Tags |")
        w("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
        for r in sorted(rows, key=lambda r: -r["jaccard"]):
            w(f"| {r['ca']} | {r['cb']} | {r['a']} | {r['b']} | {r['n']} | {r['jaccard']:.2f} | {r['cont_a']:.0%} | "
              f"{r['cont_b']:.0%} | {r['cont_min']:.2f} | {r['a_common']} | {r['b_common']} | {f(r['jaccard_common'])} | "
              f"{r['expected']:.1f} | {r['lift']:.1f} | {', '.join(r['shared'])} |")
        w("")

    (HERE / "report.md").write_text("\n".join(L), encoding="utf-8")
    cols = ["A", "B", "ca", "cb", "a", "b", "n", "a_common", "b_common", "N", "jaccard", "cont_a", "cont_b",
            "cont_min", "cont_max", "jaccard_common", "expected", "lift", "shared", "only_a", "only_b"]
    with (HERE / "matches.csv").open("w", newline="", encoding="utf-8") as fh:
        wr = csv.DictWriter(fh, cols)
        wr.writeheader()
        for r in all_rows:
            wr.writerow({k: ("; ".join(v) if isinstance(v, list) else v) for k, v in r.items()})
    print(f"{len(all_rows)} matches, {len(over)} pairs -> {HERE / 'report.md'}")


if __name__ == "__main__":
    main()

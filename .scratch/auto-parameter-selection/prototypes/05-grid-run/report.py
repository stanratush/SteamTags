"""Throwaway: turns the grid_run.py JSON into results.md (tables, g × s heatmaps) and pairs.csv.

    .venv/Scripts/python.exe .scratch/auto-parameter-selection/prototypes/05-grid-run/report.py <runs dir>

<runs dir> holds parallel/, serial/ and compare80/ from grid_run.py.
"""

from __future__ import annotations

import csv
import json
import statistics
import sys
from collections import Counter
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
MIN_MULTI = 3
DATASETS = ("overall", "puzzle", "rpg", "simulation", "strategy")
G_RANGE = range(3, 21)
S_RANGE = range(2, 13)


def load(run: Path) -> dict[str, dict]:
    return {d: json.loads((run / f"{d}.json").read_text(encoding="utf-8")) for d in DATASETS
            if (run / f"{d}.json").is_file()}


def sel(r, key):
    return r["selected"][key] if r["selected"] is not None else None


METRICS = {  # name -> (getter, format)
    "Tags": (lambda r: r["n_tags"], "{:.0f}"),
    "Edges": (lambda r: r["n_edges"], "{:.0f}"),
    "Multi-Tag Clusters (Selected Partition)": (lambda r: sel(r, "n_multi"), "{:.0f}"),
    "Domain width (b − a)": (lambda r: sel(r, "width"), "{:.3f}"),
    "Selected Resolution": (lambda r: sel(r, "selected_resolution"), "{:.3f}"),
    "Information Retention": (lambda r: r["retention"], "{:.3f}"),
    "Share of games with an edged tag": (lambda r: r["games_with_edged_tag_share"], "{:.3f}"),
    "Isolated share of tags": (lambda r: r["isolated_share"], "{:.3f}"),
    "LCC share of non-isolated tags": (lambda r: r["lcc_share_non_isolated"], "{:.3f}"),
    "Components with ≥ 2 tags": (lambda r: r["n_components_2plus"], "{:.0f}"),
    "Neighbour Agreement (mean ARI)": (lambda r: r["neighbour_agreement"]["mean"], "{:.3f}"),
    "Neighbour Agreement (min ARI, descriptive)": (lambda r: r["neighbour_agreement"]["min"], "{:.3f}"),
    "Comparable neighbours": (lambda r: r["neighbour_agreement"]["n_comparable"], "{:.0f}"),
    "Seed-Noise Floor (min ARI)": (lambda r: sel(r, "seed_noise_floor"), "{:.3f}"),
    "Seed-noise exact reproductions (of 10)": (lambda r: sel(r, "seed_noise_exact"), "{:.0f}"),
    "Hits of the Selected Partition (of 560)": (lambda r: sel(r, "hits"), "{:.0f}"),
    "Unique partitions": (lambda r: r.get("n_unique"), "{:.0f}"),
    "Admissible Partitions": (lambda r: r.get("n_admissible"), "{:.0f}"),
    "Stable Partitions": (lambda r: r.get("n_stable"), "{:.0f}"),
    "Stable with ≥ 3 Multi-Tag Clusters": (lambda r: r.get("n_stable_qualifying"), "{:.0f}"),
    "Share of edges with Lift < 1": (lambda r: r["lift_below_1_share"], "{:.3f}"),
    "Q at the Selected Resolution (descriptive)": (lambda r: sel(r, "Q"), "{:.3f}"),
    "Weighted Coverage (descriptive)": (lambda r: sel(r, "coverage"), "{:.3f}"),
    "Jaccard silhouette (descriptive)": (lambda r: sel(r, "silhouette"), "{:.3f}"),
}

BLIND = ("Neighbour Agreement (mean ARI)", "Neighbour Agreement (min ARI, descriptive)")
NA_HEATMAPS = [
    ("Neighbour Agreement", "Mean ARI over comparable neighbours; `—` = unavailable.",
     lambda r: r["neighbour_agreement"]["mean"], "{:.2f}"),
    ("Neighbour Agreement minimum (descriptive)", "Minimum ARI over comparable neighbours.",
     lambda r: r["neighbour_agreement"]["min"], "{:.2f}"),
]

HEATMAPS = [
    ("Selected Partition: Multi-Tag Clusters", "Multi-Tag Clusters of the Selected Partition; `—` = no Selected "
     "Partition (reason code in the table above).", lambda r: sel(r, "n_multi"), "{:.0f}"),
    ("Domain width", "Plain-γ width b − a of the Selected Partition's domain; `*` marks a domain clipped at a "
     "range end.", None, None),
    ("Information Retention", "Visible game–tag assignments kept by tags with ≥ 1 edge.",
     lambda r: r["retention"], "{:.2f}"),
    ("Isolated share of tags", "Isolated tags over all tags of the network.", lambda r: r["isolated_share"], "{:.2f}"),
    ("LCC share of non-isolated tags", "Largest connected component over the non-isolated tags.",
     lambda r: r["lcc_share_non_isolated"], "{:.2f}"),
    ("Neighbour counts", "`c/m/i`: comparable neighbours / missing (neighbour has no Selected Partition) / "
     "comparable neighbours with an identical graph.", None, None),
    ("Seed-Noise Floor", "Minimum ARI of the 10 noise-seed runs at the exact Selected Resolution against the "
     "Selected Partition.", lambda r: sel(r, "seed_noise_floor"), "{:.2f}"),
]


def quantiles(values: list[float]) -> list[float]:
    a = np.array(values, dtype=float)
    return [float(x) for x in np.quantile(a, [0, 0.1, 0.25, 0.5, 0.75, 0.9, 1.0])]


def heat_cell(r, name, getter, fmt):
    if r is None:
        return ""
    if name == "Domain width":
        if r["selected"] is None:
            return "—"
        clip = "*" if r["selected"]["clipped_low"] or r["selected"]["clipped_high"] else ""
        return f"{r['selected']['width']:.2f}{clip}"
    if name == "Neighbour counts":
        na = r["neighbour_agreement"]
        return f"{na['n_comparable']}/{na['n_missing']}/{na['n_identical_comparable']}"
    v = getter(r)
    return "—" if v is None else fmt.format(v)


def heatmap(by_pair, name, getter, fmt) -> list[str]:
    lines = ["| g \\ s | " + " | ".join(str(s) for s in S_RANGE) + " |",
             "|---:|" + "---:|" * len(S_RANGE)]
    for g in G_RANGE:
        cells = [heat_cell(by_pair.get((g, s)), name, getter, fmt) for s in S_RANGE]
        lines.append(f"| **{g}** | " + " | ".join(cells) + " |")
    return lines


def fmt_q(qs, fmt):
    return " | ".join(fmt.format(q) for q in qs)


def comparable(a: dict, b: dict) -> bool:
    """Same records except timing fields."""
    strip = lambda r: {k: v for k, v in r.items() if k not in ("seconds", "scan_seconds")}
    return all(strip(x) == strip(y) for x, y in zip(a["records"], b["records"])) and a["links"] == b["links"]


def main() -> None:
    runs = Path(sys.argv[1])
    par, ser, c80 = load(runs / "parallel"), load(runs / "serial"), load(runs / "compare80")
    out: list[str] = []
    w = out.append

    # ---- pairs.csv
    with (HERE / "pairs.csv").open("w", newline="", encoding="utf-8") as f:
        cols = ["dataset", "g", "s", "no_selection_reason", "not_representable", "clipped", "workbench_resolution",
                "na_status", "na_in_grid", "na_comparable", "na_missing", "na_too_few_tags", "na_identical_comparable",
                "graph_hash", *(m for m in METRICS if m not in BLIND)]
        wr = csv.writer(f)
        wr.writerow(cols)
        for d, doc in par.items():
            for r in doc["records"]:
                na = r["neighbour_agreement"]
                s_ = r["selected"]
                row = [d, r["g"], r["s"], r.get("no_selection_reason") or "",
                       "" if s_ is None else s_["not_representable"],
                       "" if s_ is None else (s_["clipped_low"] or s_["clipped_high"]),
                       "" if s_ is None or s_["workbench_resolution"] is None else s_["workbench_resolution"],
                       na["status"], na["n_in_grid"], na["n_comparable"], na["n_missing"], na["n_too_few_tags"],
                       na["n_identical_comparable"], r["graph_hash"][:12]]
                for name, (getter, _) in METRICS.items():
                    if name in BLIND:
                        continue
                    v = getter(r)
                    row.append("" if v is None else (round(v, 6) if isinstance(v, float) else v))
                wr.writerow(row)

    with (HERE / "neighbour-agreement-by-pair.csv").open("w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(["dataset", "g", "s", "status", "mean_ari", "min_ari"])
        for d, doc in par.items():
            for r in doc["records"]:
                na = r["neighbour_agreement"]
                wr.writerow([d, r["g"], r["s"], na["status"], "" if na["mean"] is None else round(na["mean"], 6),
                             "" if na["min"] is None else round(na["min"], 6)])
    na_md = ["# Neighbour Agreement by pair\n",
             "**Open this only after [Eligibility constraints and selection defaults](../../issues/06-eligibility-and-"
             "selection-defaults.md) has fixed its defaults.** Ticket 06 requires the defaults to be fixed before "
             "looking at which pair they select; these tables show where Neighbour Agreement peaks, and so which pair "
             "a given set of constraints would select. The distribution (quantiles) is in [results.md](results.md). "
             "Per-pair values: [neighbour-agreement-by-pair.csv](neighbour-agreement-by-pair.csv).\n"]
    for name, caption, getter, fmt in NA_HEATMAPS:
        na_md += [f"## {name}\n", caption + "\n"]
        for d, doc in par.items():
            na_md.append(f"**{d}**\n")
            na_md += heatmap({(r["g"], r["s"]): r for r in doc["records"]}, name, getter, fmt)
            na_md.append("")
    (HERE / "neighbour-agreement-by-pair.md").write_text("\n".join(na_md) + "\n", encoding="utf-8")

    # ---- header
    any_doc = next(iter(par.values()))
    w("# Exploratory grid run: results\n")
    w("Facts only, for [Eligibility constraints and selection defaults](../../issues/06-eligibility-and-selection-defaults.md). "
      "No default is chosen here. Produced by [grid_run.py](grid_run.py) and [report.py](report.py) for "
      "[Exploratory grid run on the current Build](../../issues/05-exploratory-grid-run.md); every pair's numbers are "
      "in [pairs.csv](pairs.csv).\n")
    w("Neighbour Agreement appears here only as a distribution. Its per-pair values, which show which pair a set of "
      "constraints would select, are kept apart in [neighbour-agreement-by-pair.md](neighbour-agreement-by-pair.md), "
      "to be opened only after ticket 06 has fixed its defaults.\n")
    w("## Setup\n")
    w("- Build `20261008T221504Z-7a23ae9f`, all five Top-100 Datasets. Fixed settings: Genre Tags and the defining "
      "tag hidden, Minimum Months 0, Clustering Weight Lift, Leiden (`RBConfigurationVertexPartition`, "
      "`n_iterations=-1`).")
    w("- Parameter Grid: 3 ≤ g ≤ 20, 2 ≤ s ≤ 12, s ≤ g: 153 pairs per dataset, 765 in all.")
    w("- Procedure exactly as [Resolution-selection rules](../../issues/03-resolution-selection-rules.md): 56 γ "
      "(0.25 to 3.00, step 0.05) × 10 scan seeds = 560 Leiden runs per pair; dedup over all tags; CHAMP on "
      "[0.25, 3.00] with rtol 1e-12; γ̂ once per Admissible Partition with the four guards; minimum 3 Multi-Tag "
      "Clusters after stability; widest domain, ties to the lower midpoint.")
    w(f"- Scan seeds: `derive_seeds(20261003, stream=3, 10, exclude=replicate ∪ noise seeds)` = "
      f"`{any_doc['scan_seeds']}`. Stream 3 is this script's assumption; no ticket has fixed the stream number.")
    w("- Metrics exactly as [Per-pair metric definitions](../../issues/04-pair-metric-definitions.md). Seed-Noise "
      "Floor: `noise_seeds(20261003, 10, 20)` at the exact, unrounded Selected Resolution.")
    w("- The script calls `leidenalg.find_partition` on an igraph built once per pair rather than going through "
      "`cluster.detect` per run. On 9 (γ, seed) runs of one graph the memberships were identical to `detect`'s.")
    w("- Machine: 12 logical cores, Windows 11, Python 3.14.8, leidenalg 0.12.0, igraph 1.0.0, multiprocess "
      "0.70.19.\n")

    # ---- headline
    allr = [r for doc in par.values() for r in doc["records"]]
    withsel = [r for r in allr if r["selected"]]
    lcc = [r["lcc_share_non_isolated"] for r in allr if r["lcc_share_non_isolated"] is not None]
    iso0 = sum(r["n_isolated"] == 0 for r in allr)
    ret = [r["retention"] for r in allr]
    k3 = sum(r["selected"]["n_multi"] == MIN_MULTI for r in withsel)
    hits1 = sum(r["selected"]["hits"] == 1 for r in withsel)
    w("## Headline facts\n")
    w(f"- {len(withsel)} of {len(allr)} pairs have a Selected Partition. None has a clipped domain or is "
      f"`not_representable`.")
    w(f"- The largest connected component holds every non-isolated tag in all {len(lcc)} pairs (LCC share "
      f"min {min(lcc):.3f}). {iso0} of {len(allr)} pairs have no isolated tag.")
    w(f"- Information Retention runs from {min(ret):.3f} to {max(ret):.3f}.")
    w(f"- {k3} Selected Partitions have exactly {MIN_MULTI} Multi-Tag Clusters, the minimum; {hits1} were found "
      f"by only 1 of the 560 scan runs.")
    w("- Every pair with a Selected Partition has at least 2 comparable neighbours. Only the four neighbours of rpg "
      "g=18 s=4 (`too_few_multi_tag_clusters`, the one pair without a Selected Partition) have a missing neighbour.")
    if ser:
        w(f"- Wall-clock for all 765 pairs: {sum(d['pairs_seconds'] for d in ser.values()):.0f} s serial, "
          f"{sum(d['pairs_seconds'] for d in par.values()):.0f} s on 12 workers; 94–95% of the time is the "
          f"Leiden scan.")
    w("")

    # ---- selection outcome
    w("## 1. Which pairs have a Selected Partition\n")
    w("| Dataset | Pairs | With a Selected Partition | `no_stable_partition` | `too_few_multi_tag_clusters` | "
      "`no_edges` | Clipped domain | `not_representable` |")
    w("|---|---:|---:|---:|---:|---:|---:|---:|")
    for d, doc in par.items():
        rs = doc["records"]
        reasons = Counter(r.get("no_selection_reason") for r in rs if r["selected"] is None)
        withsel = [r for r in rs if r["selected"] is not None]
        clipped = sum(r["selected"]["clipped_low"] or r["selected"]["clipped_high"] for r in withsel)
        nrep = sum(r["selected"]["not_representable"] for r in withsel)
        w(f"| {d} | {len(rs)} | {len(withsel)} | {reasons.get('no_stable_partition', 0)} | "
          f"{reasons.get('too_few_multi_tag_clusters', 0)} | {reasons.get('no_edges', 0)} | {clipped} | {nrep} |")
    w("")

    # stable-partition reasons among admissible partitions
    w("Reason codes over all Admissible Partitions (all pairs pooled per dataset):\n")
    w("| Dataset | Admissible | Stable | `one_group` | `no_cross_weight` | `not_assortative` | "
      "`estimate_above_range` | `estimate_below_range` | estimate outside own domain | Twins dropped |")
    w("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for d, doc in par.items():
        adm = [x for r in doc["records"] for x in r.get("admissible", [])]
        rc = Counter(x["reason"] for x in adm)
        outside = sum(x["reason"] is None and not x["stable"] for x in adm)
        twins = sum(r.get("n_twins", 0) for r in doc["records"])
        w(f"| {d} | {len(adm)} | {sum(x['stable'] for x in adm)} | {rc.get('one_group', 0)} | "
          f"{rc.get('no_cross_weight', 0)} | {rc.get('not_assortative', 0)} | {rc.get('estimate_above_range', 0)} | "
          f"{rc.get('estimate_below_range', 0)} | {outside} | {twins} |")
    w("")
    sel_hits = [r["selected"]["hits"] for doc in par.values() for r in doc["records"] if r["selected"]]
    w(f"- The Selected Partition's hit count (of 560 runs) over all {len(sel_hits)} pairs with one: "
      f"min {min(sel_hits)}, median {statistics.median(sel_hits):.0f}, max {max(sel_hits)}; "
      f"{sum(h == 1 for h in sel_hits)} pairs select a partition found exactly once, "
      f"{sum(h < 10 for h in sel_hits)} one found fewer than 10 times.")
    qd = [abs(r["selected"]["Q"] - r["selected"]["Q_champ"]) for doc in par.values() for r in doc["records"]
          if r["selected"] and r["selected"]["Q"] is not None]
    w(f"- `metrics.modularity` against CHAMP's (Â − γP̂)/2m at the Selected Resolution: max |difference| "
      f"{max(qd):.1e} over {len(qd)} pairs.\n")

    # ---- distributions
    w("## 2. Distribution of each metric per dataset\n")
    w("Quantiles over the pairs where the metric is available (n). Metrics marked descriptive are not comparable "
      "across pairs and are shown only for completeness.\n")
    for name, (getter, fmt) in METRICS.items():
        w(f"**{name}**\n")
        w("| Dataset | n | min | p10 | p25 | median | p75 | p90 | max |")
        w("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
        for d, doc in par.items():
            vals = [getter(r) for r in doc["records"]]
            vals = [v for v in vals if v is not None]
            if vals:
                w(f"| {d} | {len(vals)} | {fmt_q(quantiles(vals), fmt)} |")
            else:
                w(f"| {d} | 0 | | | | | | | |")
        w("")

    na_status = {d: Counter(r["neighbour_agreement"]["status"] for r in doc["records"]) for d, doc in par.items()}
    w("Neighbour Agreement status and neighbour counts:\n")
    w("| Dataset | `ok` | `no_selected_partition` | `no_comparable_neighbours` | pairs with exactly 1 comparable "
      "neighbour | pairs whose comparable neighbours all have an identical graph | links `ok` | links missing | "
      "links `too_few_compared_tags` |")
    w("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for d, doc in par.items():
        rs = doc["records"]
        one = sum(r["neighbour_agreement"]["n_comparable"] == 1 for r in rs)
        all_ident = sum(r["neighbour_agreement"]["n_comparable"] > 0 and r["neighbour_agreement"]["n_comparable"]
                        == r["neighbour_agreement"]["n_identical_comparable"] for r in rs)
        lc = Counter(x["status"] for x in doc["links"])
        s = na_status[d]
        w(f"| {d} | {s.get('ok', 0)} | {s.get('no_selected_partition', 0)} | {s.get('no_comparable_neighbours', 0)} | "
          f"{one} | {all_ident} | {lc.get('ok', 0)} | {lc.get('neighbour_has_no_selected_partition', 0)} | "
          f"{lc.get('too_few_compared_tags', 0)} |")
    w("")
    w("Neighbour links by direction (all datasets pooled): ARI of `ok` links and the share with an identical graph.\n")
    w("| Direction | links `ok` | identical graph | ARI median (non-identical) | ARI p10 (non-identical) | "
      "tag Jaccard median |")
    w("|---|---:|---:|---:|---:|---:|")
    for label, test in (("g → g+1", lambda x: x["q"][0] == x["p"][0] + 1), ("s → s+1", lambda x: x["q"][1] == x["p"][1] + 1)):
        ls = [x for doc in par.values() for x in doc["links"] if test(x) and x["status"] == "ok"]
        ni = [x["ari"] for x in ls if not x["identical_graph"]]
        jac = [x["jaccard"] for x in ls]
        w(f"| {label} | {len(ls)} | {sum(x['identical_graph'] for x in ls)} | "
          f"{statistics.median(ni):.3f} | {quantiles(ni)[1]:.3f} | {statistics.median(jac):.3f} |")
    w("")

    # ---- heatmaps
    w("## 3. Heatmaps (rows g = Minimum Games per Tag, columns s = Minimum Shared Games)\n")
    for name, caption, getter, fmt in HEATMAPS:
        w(f"### {name}\n")
        w(caption + "\n")
        for d, doc in par.items():
            by_pair = {(r["g"], r["s"]): r for r in doc["records"]}
            w(f"**{d}**\n")
            out.extend(heatmap(by_pair, name, getter, fmt))
            w("")

    # ---- identical graphs
    w("## 4. Pairs sharing an identical graph (room for caching)\n")
    w("Two pairs share a graph when their tag sets and edge sets are equal. Identical graphs give identical scans, "
      "so one scan per distinct graph would suffice.\n")
    w("| Dataset | Pairs | Distinct graphs | Pairs in a shared group | Largest group | Scans saved |")
    w("|---|---:|---:|---:|---:|---:|")
    tot_pairs = tot_graphs = 0
    for d, doc in par.items():
        hc = Counter(r["graph_hash"] for r in doc["records"])
        shared = sum(c for c in hc.values() if c > 1)
        tot_pairs += len(doc["records"])
        tot_graphs += len(hc)
        w(f"| {d} | {len(doc['records'])} | {len(hc)} | {shared} | {max(hc.values())} | "
          f"{len(doc['records']) - len(hc)} |")
    w(f"| all | {tot_pairs} | {tot_graphs} | | | {tot_pairs - tot_graphs} |\n")

    # ---- timing
    w("## 5. Wall-clock time\n")
    w("Pair stage = network, 560-run scan, CHAMP, γ̂, Seed-Noise Floor and descriptive metrics for all 153 pairs; "
      "neighbour stage = Neighbour Agreement over the finished pairs (in the parent process). Parallel = a "
      "`multiprocess.Pool` of 12 workers, one pair per task, workers already holding the Build. The serial and "
      "parallel runs were separate, one after the other, on an otherwise idle machine.\n")
    w("| Dataset | Serial pair stage (s) | Parallel pair stage (s) | Speed-up | Neighbour stage (s) | "
      "Serial s/pair: median | p90 | max | Scan share of serial pair time |")
    w("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    st = pt = 0.0
    for d in par:
        sd, pd = ser.get(d), par[d]
        if sd is None:
            w(f"| {d} | (no serial run) | {pd['pairs_seconds']:.1f} | | {pd['neighbour_seconds']:.2f} | | | | |")
            continue
        secs = [r["seconds"] for r in sd["records"]]
        scan = sum(r.get("scan_seconds", 0) for r in sd["records"])
        q = quantiles(secs)
        st += sd["pairs_seconds"]
        pt += pd["pairs_seconds"]
        w(f"| {d} | {sd['pairs_seconds']:.1f} | {pd['pairs_seconds']:.1f} | "
          f"{sd['pairs_seconds'] / pd['pairs_seconds']:.1f}× | {pd['neighbour_seconds']:.2f} | {q[3]:.2f} | "
          f"{q[5]:.2f} | {q[6]:.2f} | {scan / sum(secs):.0%} |")
    if st:
        w(f"| all | {st:.1f} | {pt:.1f} | {st / pt:.1f}× | | | | | |")
    w("")
    w(f"- Start-up (load the Build; with 12 workers, start the pool and load it in every worker): serial "
      f"{next(iter(ser.values()))['init_seconds']:.1f} s, parallel {any_doc['init_seconds']:.1f} s." if ser else "")
    if ser:
        same = {d: comparable(ser[d], par[d]) for d in ser if d in par}
        w(f"- Serial and parallel results are identical, record for record, apart from timing: "
          f"{', '.join(f'{d} {'yes' if v else 'NO'}' for d, v in same.items())}.")
    w("")

    # ---- 56 vs 80
    if c80:
        w("## 6. The 56-value scan against Research 01's 80-value input set\n")
        w("[Resolution-selection rules](../../issues/03-resolution-selection-rules.md) asked this run to check "
          "whether the coarser 0.05 grid changes outcomes. Arm: `numpy.linspace(0.25, 3.0, 80)` × the same 10 scan "
          "seeds, the same rules otherwise.\n")
        w("| Dataset | Both have a Selected Partition | Only 56 | Only 80 | Neither | Same Selected Partition | "
          "ARI 56 vs 80: median | min | Stable partitions 56 / 80 (sum) | Stable in both |")
        w("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
        for d, doc in c80.items():
            rs = doc["records"]
            both = [r for r in rs if r["selected"] and r["compare80"].get("width") is not None]
            only56 = sum(1 for r in rs if r["selected"] and r["compare80"].get("width") is None)
            only80 = sum(1 for r in rs if not r["selected"] and r.get("compare80", {}).get("width") is not None)
            neither = sum(1 for r in rs if not r["selected"] and r.get("compare80", {}).get("width") is None)
            same = sum(r["compare80"]["identical_to_56"] for r in both)
            aris = [r["compare80"]["ari_vs_56"] for r in both]
            s56 = sum(r.get("n_stable", 0) for r in rs)
            s80 = sum(r.get("compare80", {}).get("n_stable", 0) for r in rs)
            sh = sum(r.get("compare80", {}).get("stable_shared", 0) for r in rs)
            w(f"| {d} | {len(both)} | {only56} | {only80} | {neither} | {same} | "
              f"{statistics.median(aris):.3f} | {min(aris):.3f} | {s56} / {s80} | {sh} |")
        w("")
        widths = [(r["selected"]["width"], r["compare80"]["width"]) for doc in c80.values() for r in doc["records"]
                  if r["selected"] and r["compare80"].get("width") is not None]
        diff = [a - b for a, b in widths]
        w(f"- Selected domain width, 56 minus 80, over {len(widths)} pairs with both: median {statistics.median(diff):+.3f}, "
          f"p10 {quantiles(diff)[1]:+.3f}, p90 {quantiles(diff)[5]:+.3f}.")
        same_c80 = all(
            {k: v for k, v in r.items() if k not in ("seconds", "scan_seconds", "compare80")}
            == {k: v for k, v in p.items() if k not in ("seconds", "scan_seconds")}
            for d in c80 for r, p in zip(c80[d]["records"], par[d]["records"]))
        w(f"- The 56-value results inside this arm equal the main run's: {'yes' if same_c80 else 'NO'}.\n")

    (HERE / "results.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print("wrote", HERE / "results.md")


if __name__ == "__main__":
    main()

"""PROTOTYPE (throwaway) for ticket 06: "What does the Cluster Comparison mode look like?"

Dumps the real data the UI prototype needs into data.js beside this file: for each Top-N Dataset of the
full Build, every Parameter Grid cell that has a Selected Partition (nodes, edged Tags, Cluster labels,
γ, Seed-Noise Floor, Workbench flag, Neighbour Agreement), the run's pick under the default Pair
Constraints, and the dataset's games (rank, name, Tag ids). All matching runs in the browser so the
minimum similarity and the cell can be changed live.

Run:  uv run python .scratch/cluster-comparison/prototypes/06-look-of-the-mode/export.py
Then: open index.html (double-click; no server needed).
"""

from __future__ import annotations

import json
from pathlib import Path

from steamstudy.app import ps_cache, ps_view
from steamstudy.app.loader import load_build
from steamstudy.network import selection as SEL

HERE = Path(__file__).parent
ROOT = HERE.parents[3]
BUILD = ROOT / "builds" / "20261005T062558Z-full" / "20261008T221504Z-7a23ae9f"
ps_cache.NAME_LENGTH = 64  # this Build's cache predates the 16-digit folder names (in memory only)


def main():
    ctx = load_build(BUILD)
    settings, constraints = ps_view.defaults_of(ctx)
    names: dict[int, str] = {}
    out = {"build": ctx.build_id, "datasets": []}
    for ds in ctx.datasets:
        view = ps_view.dataset_view(ctx, settings, ds.key, constraints, constraints)
        games = ctx.games(ds.key)
        for g in games:
            names.update(zip(g.tag_ids, g.tags))
        cells = {}
        for pair in view.pairs:
            r = view.result(pair)
            if r is None or r.selected is None:
                continue
            labels = {}
            for c in SEL.clusters_of(r.nodes, r.selected):
                for t in c.members:
                    labels[t] = c.label
            na = view.na.get(pair)
            cells[f"{pair[0]},{pair[1]}"] = dict(
                g=pair[0], s=pair[1], gamma=r.selected_resolution, nodes=r.nodes, edged=r.edged,
                label=[labels[t] for t in r.nodes],
                floor=(r.seed_noise or {}).get("floor"), wb=(r.workbench or {}).get("flag"),
                wb_gamma=(r.workbench or {}).get("gamma"), wb_seed=(r.workbench or {}).get("seed"),
                na=None if na is None else na.value,
            )
        out["datasets"].append(dict(
            key=ds.key, label=ds.label, star=None if view.star is None else f"{view.star[0]},{view.star[1]}",
            status=view.status, cells=cells, defining=ctx.context(ds.key).defining_tag_id,
            games=[dict(a=g.appid, r=g.rank, n=g.name, t=list(g.tag_ids)) for g in games],
        ))
    out["names"] = {str(k): v for k, v in names.items()}
    (HERE / "data.js").write_text("window.DATA = " + json.dumps(out, ensure_ascii=False, default=float) + ";\n",
                                  encoding="utf-8")
    print({d["key"]: (d["star"], len(d["cells"]), len(d["games"])) for d in out["datasets"]})


if __name__ == "__main__":
    main()

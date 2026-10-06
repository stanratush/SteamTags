"""PROTOTYPE, throwaway: dump the default Overall and Puzzle Network States of the latest Build to data.js
for the styling-directions prototype, and inline it into the HTML. Run: uv run python .scratch/app-readability/prototypes/01-styling-directions/dump_state.py
"""
import json
import sys
from pathlib import Path

from steamstudy.app.loader import load_build
from steamstudy.build.writer import resolve_build
from steamstudy.network.graph import filter_games
from steamstudy.network.model import resolution_text
from steamstudy.network.state import compute_state
from steamstudy.network.tables import state_tables

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
c = load_build(resolve_build(root))
out = {"build_id": c.build_id, "datasets": {}}
for key in ("overall", "puzzle"):
    s = c.default_settings(key)
    state = compute_state(c.games(key), s, c.context(key))
    t = state_tables(state)
    games = filter_games(c.games(key), s.min_months)
    names = state.network.tag_names
    out["datasets"][key] = {
        "label": c.dataset(key).label, "state_id": state.state_id, "key": s.key(), "gamma": resolution_text(s.resolution),
        "n_games": state.network.n_games, "n_rows": len(c.rows(key)),
        "hidden": [names.get(x, str(x)) for x in s.hidden_tag_ids],
        "quality": t["cluster_quality.csv"][0], "nodes": t["nodes.csv"], "clusters": t["clusters.csv"],
        "edges": [{k: v for k, v in r.items() if k != "appids"} for r in t["edges.csv"]],
        "nin": t["not_in_network.csv"],
        "games": [{"appid": g.appid, "name": g.name, "rank": g.rank, "tags": sorted(g.tag_ids)} for g in games],
        "positions": {str(k): v for k, v in state.positions.items()},
    }
dest = Path(__file__).with_name("data.js")
dest.write_text("window.DATA = " + json.dumps(out, default=str, allow_nan=False) + ";\n", encoding="utf-8")
print(dest, dest.stat().st_size)
# Inline the data too, so the page works when opened as a single file (e.g. a data: snapshot).
import re
html = Path(__file__).with_name("PROTOTYPE-styling-directions.html")
text = html.read_text(encoding="utf-8")
inline = "<!--DATA--><script>" + dest.read_text(encoding="utf-8").replace("</", r"<\/") + "</script><!--/DATA-->"
html.write_text(re.sub(r"<!--DATA-->.*?<!--/DATA-->", lambda m: inline, text, flags=re.S), encoding="utf-8", newline="\n")

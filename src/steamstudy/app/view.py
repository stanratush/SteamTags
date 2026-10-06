"""Text and table views of a Network State: the quality and noise lines, grid columns, the inspector."""

from __future__ import annotations

import math
from typing import Any

from dash import html

from steamstudy.export import schema as S
from steamstudy.network.metrics import within_z_cap

SILHOUETTE_LABEL = "silhouette (Jaccard game-set distance), descriptive diagnostic, not a selection criterion"
SCREENING = "screening flag, not a significance test"


def num(value: Any, digits: int = 2) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, int):
        return str(value)
    return f"{value:.{digits}f}"


def z_text(z: float | None) -> str:
    if z is None:
        return "n/a"
    return f"{z:.0f}" if abs(z) >= 10 else f"{z:.1f}"


def quality_line(q: dict[str, Any], gamma: str) -> str:
    if q["modularity"] is None:
        qtext = f"Q (γ = {gamma}) n/a: no edges"
    else:
        null_edges = "n/a" if q["null_n_edges_mean"] is None else f"{q['null_n_edges_mean']:.0f}"
        qtext = (f"Q (γ = {gamma}) {num(q['modularity'])} vs null {num(q['q_null_mean'])} ± {num(q['q_null_sd'])} "
                 f"(excess {num(q['q_excess'])}, z {z_text(q['modularity_z'])}; null networks average {null_edges} "
                 f"edges vs {q['n_edges']})")
    sil = num(q["mean_silhouette"]) if q["mean_silhouette"] is not None else f"n/a ({q['silhouette_status']})"
    parts = [qtext, f"coverage {num(q['coverage'])}",
             f"{q['n_multi_tag_clusters']} multi-tag + {q['n_one_tag_clusters']} one-tag",
             f"{SILHOUETTE_LABEL} {sil}"]
    if q["n_disconnected_clusters"]:
        parts.append(f"{q['n_disconnected_clusters']} disconnected cluster(s): try Leiden")
    return " · ".join(parts)


def noise_line(q: dict[str, Any], k: int) -> str:
    sil_sd = num(q["seed_silhouette_sd"]) if q["seed_silhouette_sd"] is not None else "n/a"
    return (f"Seed-noise floor (K = {k}): ARI vs. main min {num(q['seed_ari_min'])}, mean {num(q['seed_ari_mean'])} · "
            f"multi-tag clusters {q['seed_k_min']}–{q['seed_k_max']} · SD Q {num(q['seed_modularity_sd'], 3)} · "
            f"SD silhouette {sil_sd}")


def chance_footer(flagged: int, n: int, k: int) -> str:
    return (f"{flagged} of {n} tags flagged; if removals acted only like another seed, at most about "
            f"{n / (k + 1):.0f} would be (n / (K + 1)). {SCREENING.capitalize()}.")


# ----------------------------------------------------------------------------- grids


def column_defs(schema_key: str, columns: list[str] | None = None, *, extra: list[dict[str, Any]] | None = None) -> list[dict]:
    """ag-grid columns for a declared file; every header shows the schema description as its tooltip."""
    schema = S.file(schema_key)
    names = columns or list(schema.column_names)
    defs = []
    for name in names:
        col = schema.column(name)
        d: dict[str, Any] = {"field": name, "headerName": name, "headerTooltip": col.description,
                             "sortable": True, "filter": True, "resizable": True}
        if col.type in ("float", "float6"):
            d["valueFormatter"] = {"function": "params.value == null ? '' : d3.format('.3~f')(params.value)"}
            d.update(filter="agNumberColumnFilter", type="rightAligned")
        elif col.type == "int":
            d.update(filter="agNumberColumnFilter", type="rightAligned")
        elif col.type.endswith("_list"):
            d["valueFormatter"] = {"function": "params.value == null ? '' : params.value.join('; ')"}
        defs.append(d)
    return defs + list(extra or [])


def grid_rows(rows: list[dict[str, Any]], drop: tuple[str, ...] = ()) -> list[dict[str, Any]]:
    return [{k: (None if isinstance(v, float) and not math.isfinite(v) else v) for k, v in r.items() if k not in drop}
            for r in rows]


# ----------------------------------------------------------------------------- inspector

NODES, EDGES, CLUSTERS, RS = ("app_export/nodes.csv", "app_export/edges.csv", "app_export/clusters.csv",
                              "app_export/removal_sensitivity.csv")

# The Inspector's plain names. Grids, exports and the Column Index keep the column names; each label's tooltip
# gives the column's description and name, and its guide entry says "Shown in the app as" this label.
INSPECTOR_LABELS: dict[str, tuple[tuple[str, str], ...]] = {
    "Cluster": ((NODES, "cluster"),),
    "Games": ((NODES, "n_games"),),
    "Total shared games": ((NODES, "strength_shared"),),
    "Total lift": ((NODES, "strength_lift"),),
    "Shared games in own cluster": ((NODES, "strength_shared_intra"),),
    "Lift in own cluster": ((NODES, "strength_lift_intra"),),
    "Links · in own cluster": ((NODES, "degree"), (NODES, "degree_intra")),
    "Membership Stability": ((NODES, "membership_stability"),),
    "Prominence in own cluster (z)": ((NODES, "within_z"),),
    "Spread across clusters": ((NODES, "participation"),),
    "Fit to own cluster (silhouette)": ((NODES, "silhouette"),),
    "Mean game-set distance to members": ((NODES, "medoid_score"),),
    "Cluster Center": ((NODES, "is_center"), (CLUSTERS, "center")),
    "Shared games": ((EDGES, "shared_games"),),
    "Lift": ((EDGES, "lift"),),
    "Center's game-set distance": ((CLUSTERS, "center_medoid_score"),),
    "Most-linked member": ((CLUSTERS, "top_strength_tag"),),
    "Center is the most-linked member": ((CLUSTERS, "center_is_top_strength"),),
    "Mean Membership Stability": ((CLUSTERS, "mean_membership_stability"),),
    "Boundary crossing (conductance)": ((CLUSTERS, "conductance"),),
    "Agreement after removal (ARI, reclustered)": ((RS, "rc_ari"),),
    "Beyond seed noise": ((RS, "rc_ari_beyond_noise"),),
    "Change in Q (reclustered)": ((RS, "rc_delta_modularity"),),
    "Silhouette after removal (reclustered)": ((RS, "rc_delta_silhouette"), (RS, "rc_silhouette_after")),
    "Change in multi-tag · one-tag clusters": ((RS, "rc_delta_k"), (RS, "rc_delta_s")),
    "Cluster Centers lost": ((RS, "rc_centers_lost"),),
    "Change in Q (clusters kept)": ((RS, "fp_delta_modularity"),),
    "Silhouette after removal (clusters kept)": ((RS, "fp_delta_silhouette"), (RS, "fp_silhouette_after")),
}
GAMES_SHOWN = 10


def label_tip(label: str) -> str:
    """A plain name's tooltip: each column's description and name."""
    return "  ".join(f"{S.file(f).column(c).description} Column: {c} ({f.split('/')[-1]})."
                     for f, c in INSPECTOR_LABELS[label])


def _kv(rows: list[tuple[str, Any]]) -> html.Dl:
    """Metrics as a two-column list: muted plain names (tooltip: description and column), values."""
    items: list[Any] = []
    for label, value in rows:
        items += [html.Dt(label, title=label_tip(label)), html.Dd(value)]
    return html.Dl(items, className="kv")


def _note(value: str, note: str) -> list[Any]:
    return [value, " ", html.Small(note)]


def _swatch(color: str) -> html.Span:
    return html.Span(className="sw", style={"background": color})


def tag_games(games: list[Any], min_months: int, tag: int) -> list[dict[str, Any]]:
    """The games in the network (after the Minimum Months Filter) that have the tag, in rank order."""
    from steamstudy.network.graph import filter_games

    return [{"appid": g.appid, "name": g.name, "rank": g.rank} for g in filter_games(games, min_months)
            if tag in g.tag_ids]


def connected_tags(tables: dict[str, Any], tag: int) -> list[dict[str, Any]]:
    """The tags linked to `tag`: by shared games (most first), then by name."""
    from steamstudy.app.renderer import cluster_color

    kinds = {r["cluster"]: r["kind"] for r in tables["clusters"]}
    out = []
    for e in tables["edges"]:
        if tag not in (e["source_tag_id"], e["target_tag_id"]):
            continue
        mine = e["source_tag_id"] == tag
        cluster = e["target_cluster"] if mine else e["source_cluster"]
        out.append({"edge": f"{e['source_tag_id']}-{e['target_tag_id']}",
                    "tag": e["target_tag"] if mine else e["source_tag"], "cluster": cluster,
                    "color": cluster_color(cluster, kinds.get(cluster, "multi_tag")), "shared": e["shared_games"],
                    "lift": e["lift"]})
    return sorted(out, key=lambda c: (-c["shared"], str(c["tag"]).lower()))


def _games_table(games: list[dict[str, Any]], with_appid: bool = False) -> html.Table:
    head = [html.Th("Rank", className="r")] + ([html.Th("AppID")] if with_appid else []) + [html.Th("Name")]
    body = [html.Tr([html.Td(g["rank"], className="r mute")] + ([html.Td(g["appid"], className="mono mute")]
                                                               if with_appid else []) +
                    [html.Td(g["name"], className="name")]) for g in games]
    return html.Table([html.Thead(html.Tr(head)), html.Tbody(body)], className="tl")


def node_inspector(node: dict[str, Any], weight: str, rs_row: dict[str, Any] | None, cluster_size: int,
                   stale: bool, games: list[dict[str, Any]] | None = None,
                   connected: list[dict[str, Any]] | None = None, color: str = "#999") -> list[Any]:
    """The tag view: its games, its connected tags, then its metrics (and its Removal Sensitivity, if run)."""
    games, connected = games or [], connected or []
    active = "strength_shared" if weight == "shared_games" else "strength_lift"
    used = lambda column, value: _note(value, "used for clustering") if column.startswith(active) else value  # noqa: E731
    within = node["within_z"]
    cap = within_z_cap(cluster_size) if cluster_size >= 2 else None
    within_text: Any = "n/a" if within is None else _note(
        num(within, 1), f"max {num(cap, 1)} in a {cluster_size}-tag cluster; not comparable across cluster sizes")
    silhouette: Any = _note(num(node["silhouette"]), "descriptive") if node["silhouette"] is not None \
        else _note("n/a", str(node["silhouette_status"]))
    n = len(games)
    out: list[Any] = [
        html.H4([_swatch(color), node["tag"]] + ([html.Span("◆ Cluster Center", className="badge")]
                                                 if node["is_center"] else []), className="i-title"),
        html.P(f"Tag {node['tag_id']} · {node['cluster']} ({cluster_size} tags)", className="i-sub"),
        html.P([html.B(str(n)), f" game{'' if n == 1 else 's'} in the network {'has' if n == 1 else 'have'} this tag"],
               className="lead"),
        _games_table(games[:GAMES_SHOWN]),
    ]
    if n > GAMES_SHOWN:
        out.append(html.Details([html.Summary(f"Show all {n}", className="more"), _games_table(games[GAMES_SHOWN:])]))
    out.append(html.Div(["Connected tags ", html.Span(f"{len(connected)}, by shared games", className="cnt")],
                        className="i-h"))
    out.append(html.Table([
        html.Thead(html.Tr([html.Th("Tag"), html.Th("Shared games", className="r"), html.Th("Lift", className="r")])),
        html.Tbody([html.Tr([html.Td([_swatch(c["color"]), c["tag"]]), html.Td(c["shared"], className="r"),
                             html.Td(num(c["lift"]), className="r")],
                            id={"type": "conn", "edge": c["edge"]}, className="click", title="Select this link")
                    for c in connected])], className="tl"))
    out.append(html.Div("Metrics", className="i-h"))
    out.append(_kv([
        ("Cluster", node["cluster"]),
        ("Games", str(node["n_games"])),
        ("Total shared games", used("strength_shared", num(node["strength_shared"]))),
        ("Total lift", used("strength_lift", num(node["strength_lift"]))),
        ("Shared games in own cluster", used("strength_shared_intra", num(node["strength_shared_intra"]))),
        ("Lift in own cluster", used("strength_lift_intra", num(node["strength_lift_intra"]))),
        ("Links · in own cluster", f"{node['degree']} · {node['degree_intra']}"),
        ("Membership Stability", num(node["membership_stability"])),
        ("Prominence in own cluster (z)", within_text),
        ("Spread across clusters", num(node["participation"])),
        ("Fit to own cluster (silhouette)", silhouette),
        ("Mean game-set distance to members", num(node["medoid_score"], 3)),
        ("Cluster Center", "yes ◆" if node["is_center"] else "no"),
    ]))
    if rs_row is not None:
        out += [html.Div("Removal Sensitivity" + (" (stale: other settings)" if stale else ""), className="i-h"),
                _kv([
                    ("Agreement after removal (ARI, reclustered)", num(rs_row["rc_ari"])),
                    ("Beyond seed noise", _note("yes" if rs_row["rc_ari_beyond_noise"] else "no", SCREENING)),
                    ("Change in Q (reclustered)", num(rs_row["rc_delta_modularity"], 3)),
                    ("Silhouette after removal (reclustered)", _transition(rs_row, "rc")),
                    ("Change in multi-tag · one-tag clusters", f"{rs_row['rc_delta_k']} · {rs_row['rc_delta_s']}"),
                    ("Cluster Centers lost", ", ".join(rs_row["rc_centers_lost"] or []) or "none"),
                    ("Change in Q (clusters kept)", num(rs_row["fp_delta_modularity"], 3)),
                    ("Silhouette after removal (clusters kept)", _transition(rs_row, "fp")),
                ])]
    return out


def _transition(row: dict[str, Any], prefix: str) -> str:
    after, status, delta = row[f"{prefix}_silhouette_after"], row[f"{prefix}_silhouette_after_status"], row[f"{prefix}_delta_silhouette"]
    if delta is not None:
        return f"Δ {num(delta, 3)} (after {num(after)})"
    return f"→ {num(after)}" if after is not None else f"→ n/a ({status})"


def edge_inspector(edge: dict[str, Any], games: list[dict[str, Any]]) -> list[Any]:
    same = edge["source_cluster"] == edge["target_cluster"]
    return [
        html.H4([edge["source_tag"], html.Span(" — ", className="mute"), edge["target_tag"]], className="i-title"),
        html.P(f"Inside {edge['source_cluster']}" if same
               else f"Between {edge['source_cluster']} and {edge['target_cluster']}", className="i-sub"),
        _kv([("Shared games", html.B(str(edge["shared_games"]))), ("Lift", num(edge["lift"]))]),
        html.Div(["Games having both tags ", html.Span(str(len(games)), className="cnt")], className="i-h"),
        _games_table(games, with_appid=True),
    ]


def cluster_inspector(cluster: dict[str, Any], members: list[dict[str, Any]], weight: str, color: str = "#999") -> list[Any]:
    out: list[Any] = [
        html.H4([_swatch(color), f"{cluster['cluster']} · {cluster['size']} tags"], className="i-title"),
        html.P("Multi-Tag Cluster" if cluster["kind"] == "multi_tag" else "One-Tag Cluster", className="i-sub"),
    ]
    if not cluster["connected"]:
        out.append(html.P("This Louvain cluster is not a connected group of tags (never split). The Leiden mode "
                          "avoids such clusters.", className="warning"))
    out.append(_kv([
        ("Cluster Center", ("◆ " + cluster["center"]) if cluster["center"] else f"none ({cluster['center_status']})"),
        ("Center's game-set distance", num(cluster["center_medoid_score"], 3)),
        ("Most-linked member", cluster["top_strength_tag"] or "n/a"),
        ("Center is the most-linked member", num(cluster["center_is_top_strength"])),
        ("Mean Membership Stability", num(cluster["mean_membership_stability"])),
        ("Boundary crossing (conductance)", num(cluster["conductance"]) if cluster["conductance"] is not None
         else f"n/a ({cluster['conductance_status']})"),
    ]))
    out.append(html.Div(["Members ", html.Span("by game-set distance to the others", className="cnt")],
                        className="i-h"))
    head = [("Tag", None), ("Games", "Games"), ("Distance", "Mean game-set distance to members"),
            ("Stability", "Membership Stability")]
    out.append(html.Table([
        html.Thead(html.Tr([html.Th(h, className="r" if tip else None, title=label_tip(tip) if tip else None)
                            for h, tip in head])),
        html.Tbody([html.Tr([html.Td(("◆ " if m["is_center"] else "") + m["tag"]), html.Td(m["n_games"], className="r"),
                             html.Td(num(m["medoid_score"], 3), className="r"),
                             html.Td(num(m["membership_stability"]), className="r")]) for m in members])],
        className="tl"))
    return out


# ----------------------------------------------------------------------------- tag search and missing tags

REASONS = {"removed": "removed", "defining_tag_hidden": "defining tag hidden", "genre_tag_hidden": "Genre Tag hidden"}


def reason_text(reason: str, n_games: int, min_games: int) -> str:
    """A `not_in_network.csv` reason in plain words."""
    if reason == "below_min_games":
        return f"{n_games} game{'' if n_games == 1 else 's'}, below {min_games}"
    return REASONS.get(reason, reason)


def nin_action(reasons: list[str]) -> str | None:
    """The one action that brings a missing tag back, if exactly one does: Restore (removed) or Unhide (hidden)."""
    found = set(reasons)
    if found == {"removed"}:
        return "restore"
    if found and found <= {"genre_tag_hidden", "defining_tag_hidden"}:
        return "unhide"
    return None


def search_options(tables: dict[str, Any], min_games: int) -> list[dict[str, Any]]:
    """The header search: every tag of the network (by name, with cluster and games), then every tag not in the
    network (greyed, by games, with all its reasons). Values are `node:<id>` and `nin:<id>`."""
    from steamstudy.app.renderer import cluster_color

    kinds = {r["cluster"]: r["kind"] for r in tables["clusters"]}
    nodes = sorted(tables["nodes"], key=lambda r: (str(r["tag"]).lower(), r["tag_id"]))
    missing = sorted(tables["nin"], key=lambda r: (-r["n_games"], str(r["tag"]).lower()))
    options: list[dict[str, Any]] = [{"label": html.Span(f"In the network · {len(nodes)}", className="grp"),
                                      "value": "group:in", "disabled": True, "search": ""}]
    for r in nodes:
        options.append({"label": html.Span([
            html.Span(className="sw", style={"background": cluster_color(r["cluster"], kinds[r["cluster"]])}),
            r["tag"], html.Span(f"{r['cluster']} · {r['n_games']} games", className="why")], className="opt"),
            "value": f"node:{r['tag_id']}", "search": str(r["tag"])})
    if missing:
        options.append({"label": html.Span(f"Not in the network · {len(missing)}", className="grp"),
                        "value": "group:nin", "disabled": True, "search": ""})
    for r in missing:
        why = " · ".join(reason_text(x, r["n_games"], min_games) for x in r["reasons"])
        options.append({"label": html.Span([r["tag"], html.Span(why, className="why")], className="opt gone"),
                        "value": f"nin:{r['tag_id']}", "search": str(r["tag"])})
    return options


def nin_inspector(row: dict[str, Any], min_games: int) -> list[Any]:
    """The "Not in the network" card: the tag's reasons and games, and the one action that brings it back."""
    action = nin_action(list(row["reasons"]))
    n = row["n_games"]
    out: list[Any] = [
        html.H4(row["tag"]), html.P(f"Tag {row['tag_id']} · not in the network", className="mute"),
        html.P([html.Span(reason_text(x, n, min_games), className="reason") for x in row["reasons"]]),
        html.P(f"{n} game{'' if n == 1 else 's'} of the dataset {'has' if n == 1 else 'have'} this tag.",
               className="mute"),
    ]
    if action:
        out.append(html.Div([
            html.Button("Restore" if action == "restore" else "Unhide", id={"type": "nin-action", "action": action},
                        className="btn primary"),
            html.Span(" Pressing it changes the Network State.", className="mute small")], className="row-inline"))
    else:
        out.append(html.P("No single control brings this tag back; change the settings listed above.",
                          className="mute small"))
    return out

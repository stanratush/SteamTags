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


def _metric(label: str, value: str, column: tuple[str, str] | None = None) -> html.Tr:
    tip = S.file(column[0]).column(column[1]).description if column else None
    return html.Tr([html.Th(label, title=tip, style={"textAlign": "left", "paddingRight": "1em"}), html.Td(value)])


def node_inspector(node: dict[str, Any], weight: str, rs_row: dict[str, Any] | None, cluster_size: int,
                   stale: bool) -> list[Any]:
    active, other = ("strength_shared", "strength_lift") if weight == "shared_games" else ("strength_lift", "strength_shared")
    within = node["within_z"]
    cap = within_z_cap(cluster_size) if cluster_size >= 2 else None
    within_text = "n/a" if within is None else (
        f"{num(within, 1)} (max {num(cap, 1)} in a {cluster_size}-tag cluster); not comparable across cluster sizes")
    nodes = "app_export/nodes.csv"
    rows = [
        _metric("cluster", node["cluster"], (nodes, "cluster")),
        _metric("games (n_games)", str(node["n_games"]), (nodes, "n_games")),
        _metric(f"{active} (active)", num(node[active]), (nodes, active)),
        _metric(other, num(node[other]), (nodes, other)),
        _metric(f"{active}_intra", num(node[f"{active}_intra"]), (nodes, f"{active}_intra")),
        _metric("degree / intra", f"{node['degree']} / {node['degree_intra']}", (nodes, "degree")),
        _metric("Membership Stability", num(node["membership_stability"]), (nodes, "membership_stability")),
        _metric("within-z", within_text, (nodes, "within_z")),
        _metric("participation", num(node["participation"]), (nodes, "participation")),
        _metric("silhouette", num(node["silhouette"]) if node["silhouette"] is not None
                else f"n/a ({node['silhouette_status']})", (nodes, "silhouette")),
        _metric("medoid_score", num(node["medoid_score"], 3), (nodes, "medoid_score")),
        _metric("Cluster Center", "yes ◆" if node["is_center"] else "no", (nodes, "is_center")),
    ]
    out: list[Any] = [html.H4(f"{node['tag']} (tag {node['tag_id']})"), html.Table(rows)]
    if rs_row is not None:
        rs = "app_export/removal_sensitivity.csv"
        out += [html.H5("Removal Sensitivity" + (" (stale: other settings)" if stale else "")), html.Table([
            _metric("rc ARI", num(rs_row["rc_ari"]), (rs, "rc_ari")),
            _metric("beyond noise", ("yes" if rs_row["rc_ari_beyond_noise"] else "no") + f" ({SCREENING})",
                    (rs, "rc_ari_beyond_noise")),
            _metric("rc ΔQ", num(rs_row["rc_delta_modularity"], 3), (rs, "rc_delta_modularity")),
            _metric("rc silhouette", _transition(rs_row, "rc"), (rs, "rc_delta_silhouette")),
            _metric("rc Δk / Δs", f"{rs_row['rc_delta_k']} / {rs_row['rc_delta_s']}", (rs, "rc_delta_k")),
            _metric("centers lost", ", ".join(rs_row["rc_centers_lost"] or []) or "none", (rs, "rc_centers_lost")),
            _metric("fp ΔQ", num(rs_row["fp_delta_modularity"], 3), (rs, "fp_delta_modularity")),
            _metric("fp silhouette", _transition(rs_row, "fp"), (rs, "fp_delta_silhouette")),
        ])]
    return out


def _transition(row: dict[str, Any], prefix: str) -> str:
    after, status, delta = row[f"{prefix}_silhouette_after"], row[f"{prefix}_silhouette_after_status"], row[f"{prefix}_delta_silhouette"]
    if delta is not None:
        return f"Δ {num(delta, 3)} (after {num(after)})"
    return f"→ {num(after)}" if after is not None else f"→ n/a ({status})"


def edge_inspector(edge: dict[str, Any], games: list[dict[str, Any]]) -> list[Any]:
    edges = "app_export/edges.csv"
    return [
        html.H4(f"{edge['source_tag']} — {edge['target_tag']}"),
        html.Table([_metric("shared_games", str(edge["shared_games"]), (edges, "shared_games")),
                    _metric("lift", num(edge["lift"]), (edges, "lift")),
                    _metric("clusters", f"{edge['source_cluster']} / {edge['target_cluster']}", None)]),
        html.H5(f"Games having both tags ({len(games)})"),
        html.Table([html.Tr([html.Th("rank"), html.Th("AppID"), html.Th("name")])] +
                   [html.Tr([html.Td(g["rank"]), html.Td(g["appid"]), html.Td(g["name"])]) for g in games],
                   style={"fontSize": "0.85em"}),
    ]


def cluster_inspector(cluster: dict[str, Any], members: list[dict[str, Any]], weight: str) -> list[Any]:
    clusters = "app_export/clusters.csv"
    intra = "strength_shared_intra" if weight == "shared_games" else "strength_lift_intra"
    other = "strength_lift_intra" if weight == "shared_games" else "strength_shared_intra"
    header = html.Tr([html.Th("tag"), html.Th("medoid"), html.Th(f"{intra} (active)"), html.Th(other),
                      html.Th("within-z"), html.Th("participation"), html.Th("stability")])
    body = [html.Tr([html.Td(("◆ " if m["is_center"] else "") + m["tag"]), html.Td(num(m["medoid_score"], 3)),
                     html.Td(num(m[intra])), html.Td(num(m[other])), html.Td(num(m["within_z"], 1)),
                     html.Td(num(m["participation"])), html.Td(num(m["membership_stability"]))]) for m in members]
    out: list[Any] = [html.H4(f"{cluster['cluster']} · {cluster['size']} tags ({cluster['kind']})")]
    if not cluster["connected"]:
        out.append(html.P("This Louvain cluster is not a connected group of tags (never split). The Leiden mode "
                          "avoids such clusters.", className="warning"))
    out.append(html.Table([
        _metric("center", cluster["center"] or f"none ({cluster['center_status']})", (clusters, "center")),
        _metric("center_medoid_score", num(cluster["center_medoid_score"], 3), (clusters, "center_medoid_score")),
        _metric("top_strength_tag", cluster["top_strength_tag"] or "n/a", (clusters, "top_strength_tag")),
        _metric("center_is_top_strength", num(cluster["center_is_top_strength"]), (clusters, "center_is_top_strength")),
        _metric("mean Membership Stability", num(cluster["mean_membership_stability"]),
                (clusters, "mean_membership_stability")),
        _metric("conductance", num(cluster["conductance"]) if cluster["conductance"] is not None
                else f"n/a ({cluster['conductance_status']})", (clusters, "conductance")),
    ]))
    out.append(html.Table([header, *body], style={"fontSize": "0.85em", "marginTop": "0.5em"}))
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

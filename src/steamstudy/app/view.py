"""Text and table views of a Network State: the quality and noise lines, grid columns, the inspector."""

from __future__ import annotations

import html as markup
import math
import re
from functools import lru_cache
from typing import Any

from dash import html

from steamstudy.app import help as H
from steamstudy.export import schema as S
from steamstudy.i18n import Text, text
from steamstudy.network.metrics import within_z_cap

SILHOUETTE_LABEL = "silhouette (Jaccard game-set distance), descriptive diagnostic, not a selection criterion"
SCREENING = "screening flag, not a significance test"
WIRE = text("en")  # i18n: wire (issue 13 passes the page's translator instead)


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
    return (f"{flagged} of {n} tags flagged; if removals acted only like another seed, about "
            f"{n / (k + 1):.0f} would be flagged on average (n / (K + 1)). {SCREENING.capitalize()}.")


# ----------------------------------------------------------------------------- grids


def column_defs(schema_key: str, columns: list[str] | None = None, *, tx: Text,
                extra: list[dict[str, Any]] | None = None) -> list[dict]:
    """ag-grid columns for a declared file. A metric column's header shows its guide entry's In short as the tooltip
    and an ⓘ that opens the entry; an identifier column's shows the schema description (translated on screen only:
    the schema and every export keep the English). Column names are never translated; numbers take the language's
    decimal mark."""
    schema = S.file(schema_key)
    names = columns or list(schema.column_names)
    defs = []
    for name in names:
        col = schema.column(name)
        d: dict[str, Any] = {"field": name, "headerName": name, "headerTooltip": tx(col.description),
                             "sortable": True, "filter": True, "resizable": True}
        if H.column_has_help((schema_key, name)):
            d.update(metric_header(schema_key, name, tx=tx))
        if col.type in ("float", "float6"):
            d["valueFormatter"] = {"function": f"params.value == null ? '' : {tx.d3_format('.3~f')}(params.value)"}
            d.update(filter="agNumberColumnFilter", type="rightAligned")
        elif col.type == "int":
            d.update(filter="agNumberColumnFilter", type="rightAligned")
        elif col.type.endswith("_list"):
            d["valueFormatter"] = {"function": "params.value == null ? '' : params.value.join('; ')"}
        defs.append(d)
    return defs + list(extra or [])


def metric_header(schema_key: str, name: str, *, tx: Text) -> dict[str, Any]:
    """A metric column's header help: ag-grid's tooltip shows the In short lines and the Column line on hover, and
    an ⓘ (workbench.js `MetricHeader`) shows them on keyboard focus and opens the entry."""
    lines, target = H.column_help([(schema_key, name)], tx)
    return {"headerTooltip": H.tip_text(lines, tx),
            "headerComponentParams": {"innerHeaderComponent": "MetricHeader",
                                      "innerHeaderComponentParams": {"help": target, "tip": H.tip_json(lines)}}}


def grid_rows(rows: list[dict[str, Any]], drop: tuple[str, ...] = ()) -> list[dict[str, Any]]:
    return [{k: (None if isinstance(v, float) and not math.isfinite(v) else v) for k, v in r.items() if k not in drop}
            for r in rows]


# ----------------------------------------------------------------------------- inspector

NODES, EDGES, CLUSTERS, RS = ("app_export/nodes.csv", "app_export/edges.csv", "app_export/clusters.csv",
                              "app_export/removal_sensitivity.csv")

# The Inspector's plain names. Grids, exports and the Column Index keep the column names; each label's tooltip
# is its guide entry's In short with the column names, and the entry says "Shown in the app as" this label.
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


@lru_cache(maxsize=None)
def label_help(label: str, cls: str = "term", tx: Text = WIRE) -> str:
    """A plain name's two help layers as escaped HTML attributes (see `steamstudy.app.help`)."""
    attrs = {"class": cls, "tabindex": "0", **H.column_attrs(INSPECTOR_LABELS[label], tx)}
    return " ".join(f'{k}="{_e(v)}"' for k, v in attrs.items())


class Markup(str):
    """HTML that is already escaped (a value with its note, a bold number) for `_kv`."""


def _kv(rows: list[tuple[str, Any]]) -> html.Div:
    """Metrics as a two-column list: muted plain names (with both help layers), values. One component (see
    `_html`)."""
    items = "".join(f'<dt {label_help(label)}>{_e(label)}</dt>'
                    f'<dd>{value if isinstance(value, Markup) else _e(value)}</dd>' for label, value in rows)
    return _html(f'<dl class="kv">{items}</dl>')


def _note(value: str, note: str) -> Markup:
    return Markup(f"{_e(value)} <small>{_e(note)}</small>")


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


# Long lists in the Inspector are one element of escaped HTML each: Dash's renderer costs grow faster than the
# number of components it mounts, so a table of a few hundred cells took seconds to swap for the next tag's.
# workbench.js puts the HTML in place (no Markdown parsing, no React element per cell).


def _html(text: str) -> html.Div:
    """Escaped HTML as a single element; workbench.js sets it as the element's content."""
    attrs: dict[str, Any] = {"data-html": text}
    return html.Div(className="html-block", **attrs)


def _e(value: Any) -> str:
    return markup.escape(str(value), quote=True)


def _cell(value: Any, cls: str | None = None, tag: str = "td") -> str:
    attrs = f' class="{_e(cls)}"' if cls else ""
    return f"<{tag}{attrs}>{_e(value)}</{tag}>"


def _label_th(label: str) -> str:
    """A right-aligned table header that is an Inspector label, with its help."""
    return f"<th {label_help(label, 'term r')}>{_e(label)}</th>"


def _table(head: str, rows: list[str]) -> str:
    return f'<table class="tl"><thead><tr>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table>'


def _swatch_html(color: str) -> str:
    safe = color if re.fullmatch(r"#[0-9a-fA-F]{3,8}", color) else "#999"
    return f'<span class="sw" style="background:{safe}"></span>'


def _games_table(games: list[dict[str, Any]], with_appid: bool = False) -> str:
    head = _cell("Rank", "r", "th") + (_cell("AppID", tag="th") if with_appid else "") + _cell("Name", tag="th")
    return _table(head, [f'<tr>{_cell(g["rank"], "r mute")}{_cell(g["appid"], "mono mute") if with_appid else ""}'
                         f'{_cell(g["name"], "name")}</tr>' for g in games])


def _connected_table(connected: list[dict[str, Any]]) -> str:
    """Connected tags; a row selects its link (graph.js listens for clicks on `data-edge`)."""
    head = _cell("Tag", tag="th") + _label_th("Shared games") + _label_th("Lift")
    return _table(head, [f'<tr class="click" data-edge="{_e(c["edge"])}" tabindex="0" title="Select this link">'
                         f'<td>{_swatch_html(c["color"])}{_e(c["tag"])}</td>{_cell(c["shared"], "r")}'
                         f'{_cell(num(c["lift"]), "r")}</tr>' for c in connected])


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
        _html(_games_table(games[:GAMES_SHOWN]) + (
            f'<details><summary class="more">Show all {n}</summary>{_games_table(games[GAMES_SHOWN:])}</details>'
            if n > GAMES_SHOWN else "")),
    ]
    out.append(html.Div(["Connected tags ", html.Span(f"{len(connected)}, by shared games", className="cnt")],
                        className="i-h"))
    out.append(_html(_connected_table(connected)))
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
        _kv([("Shared games", Markup(f"<b>{_e(edge['shared_games'])}</b>")), ("Lift", num(edge["lift"]))]),
        html.Div(["Games having both tags ", html.Span(str(len(games)), className="cnt")], className="i-h"),
        _html(_games_table(games, with_appid=True)),
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
    head = _cell("Tag", tag="th") + "".join(_label_th(label) for label in (
        "Games", "Mean game-set distance to members", "Membership Stability"))
    out.append(_html(_table(
        head,
        [f'<tr>{_cell(("◆ " if m["is_center"] else "") + m["tag"])}{_cell(m["n_games"], "r")}'
         f'{_cell(num(m["medoid_score"], 3), "r")}{_cell(num(m["membership_stability"]), "r")}</tr>'
         for m in members])))
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


# ----------------------------------------------------------------------------- summary row and quality boxes

def _excess(q: dict[str, Any]) -> str:
    return "n/a" if q["q_excess"] is None else f"{q['q_excess']:+.2f}"


def _stat(label: str, value: str, sub: str, key: str, now: str | None) -> html.Div:
    """One summary number: hover or focus shows its In short, a click opens its guide entry."""
    return html.Div([html.B(value, className="num"), html.Span(label, className="term"),
                     html.Small(sub) if sub else None], className="m", tabIndex="0", **H.attrs(key, WIRE, now))


def summary_row(q: dict[str, Any], n_rows: int, gamma: str, r: int) -> list[Any]:
    """The key numbers above the graph, each large with a muted label and the two help layers."""
    q_value = "n/a" if q["modularity"] is None else f"{num(q['modularity'])} · excess {_excess(q)}"
    sil = num(q["mean_silhouette"]) if q["mean_silhouette"] is not None else "n/a"
    q_now = (f"γ = {gamma}; no links, so no Q." if q["modularity"] is None else
             f"γ = {gamma}; null mean {num(q['q_null_mean'])} ± {num(q['q_null_sd'])} from R = {r} shuffled "
             "networks; excess = Q − null mean.")
    items = [
        ("Games", f"{q['n_dataset_games']} of {n_rows}", "", "summary.games",
         f"{q['n_dataset_games']} of the dataset's {n_rows} games pass the Minimum Months Filter."),
        ("Tags", str(q["n_nodes"]), "", "summary.tags", None),
        ("Links", str(q["n_edges"]), "", "summary.links",
         None if q["null_n_edges_mean"] is None else f"shuffled networks average {q['null_n_edges_mean']:.0f} links."),
        ("Clusters", f"{q['n_multi_tag_clusters']} + {q['n_one_tag_clusters']}", "multi-tag + one-tag",
         "summary.clusters", None if q["seed_k_min"] is None else
         f"all other seeds give {q['seed_k_min']} multi-tag clusters." if q["seed_k_min"] == q["seed_k_max"] else
         f"other seeds give {q['seed_k_min']}–{q['seed_k_max']} multi-tag clusters."),
        ("Q", q_value, "", "summary.q", q_now),
        ("Silhouette", f"{sil} · descriptive", "", "summary.silhouette",
         None if q["seed_silhouette_sd"] is None else f"SD across seeds {num(q['seed_silhouette_sd'])}."),
    ]
    return [_stat(*item) for item in items]


def quality_boxes(q: dict[str, Any], gamma: str, k: int, r: int) -> list[Any]:
    """The Cluster quality tab: five boxes with both help layers, then the two full sentences once, small and muted."""
    null = f"null mean {num(q['q_null_mean'])} ± {num(q['q_null_sd'])} from R = {r} shuffled networks"
    if q["modularity"] is None:
        excess_sub, q_now, excess_now = "no edges", f"γ = {gamma}; no links, so no Q.", None
    else:
        excess_sub = (f"z {z_text(q['modularity_z'])} · null {num(q['q_null_mean'])} ± {num(q['q_null_sd'])} "
                      f"· excess over the null mean")
        q_now = f"γ = {gamma}; {null}."
        excess_now = f"Q {num(q['modularity'])} − {null}; z {z_text(q['modularity_z'])}."
    sil = num(q["mean_silhouette"]) if q["mean_silhouette"] is not None else f"n/a ({q['silhouette_status']})"
    boxes = [
        ("Q", num(q["modularity"]), f"γ = {gamma}", "quality.q", q_now),
        ("Null-model excess", _excess(q), excess_sub, "quality.excess", excess_now),
        ("Coverage", num(q["coverage"]), "link weight inside clusters", "quality.coverage", None),
        ("Silhouette", sil, "descriptive", "quality.silhouette",
         None if q["seed_silhouette_sd"] is None else f"SD across the K = {k} seeds {num(q['seed_silhouette_sd'])}."),
        ("Seed noise", num(q["seed_ari_min"]), f"ARI min · mean {num(q['seed_ari_mean'])}", "quality.seed_noise",
         f"each of the K = {k} extra seeds against the clusters shown; min is the seed that differed most."),
    ]
    return [
        html.Div([html.Div([html.Div(html.Span(label, className="term"), className="l"),
                            html.Div(value, className="v"), html.Div(sub, className="s")],
                           className="qbox", tabIndex="0", **H.attrs(key, WIRE, now))
                  for label, value, sub, key, now in boxes], className="qboxes"),
        html.Div([html.P(quality_line(q, gamma), tabIndex="0", **H.attrs("quality.sentence", WIRE)),
                  html.P(noise_line(q, k), tabIndex="0", **H.attrs("quality.noise_sentence", WIRE))], className="sentences"),
    ]


def _copied(tx: Text) -> dict[str, Any]:
    """The word app.css shows after a state_id is copied (`content: attr(data-copied)`)."""
    return {"data-copied": tx("copied")}


def state_sentence(dataset_label: str, n_rows: int, settings: Any, hidden: list[str], defining: str | None,
                   removed: list[str], state_id: str) -> list[Any]:
    """The Network State in one readable sentence, ending with its state_id (click to copy)."""
    genre = [h for h in hidden if h != defining]
    if not genre:
        hidden_text = "no Genre Tag hidden"
    elif len(genre) <= 3:
        hidden_text = f"Genre Tag{'s' if len(genre) > 1 else ''} {', '.join(genre)} hidden"
    else:
        hidden_text = f"{len(genre)} Genre Tags hidden"
    if defining and defining in hidden:
        hidden_text += f", defining tag {defining} hidden"
    removed_text = f"removed: {', '.join(removed)}" if removed else "no tag removed"
    weight = "shared games" if settings.clustering_weight == "shared_games" else "lift"
    text = (f"{dataset_label} Top {n_rows}, games with ≥ {settings.min_months} months observed; "
            f"tags on ≥ {settings.min_games_per_tag} games, links of ≥ {settings.min_shared_games} shared games; "
            f"{hidden_text}; {removed_text}; {settings.algorithm.capitalize()} on {weight}, "
            f"γ {settings.resolution:.2f}, seed {settings.seed} · ")
    return [text, html.Span(state_id, className="mono copy-id", title="Network State id: click to copy",
                            **_copied(WIRE))]


# ----------------------------------------------------------------------------- Analysis Report §1


def key_json(key: dict[str, Any]) -> str:
    """The state key as JSON with one field per line (a list of tag ids stays on its field's line)."""
    import json

    return "{\n" + ",\n".join(f"  {json.dumps(k)}: {json.dumps(v, ensure_ascii=False)}" for k, v in key.items()) + "\n}"


# The Network State fields that show a metric or a choice whose effect needs interpretation -> their help key.
STATE_HELP = {"n_games": "state.n_games", "min_months": "control.min-months", "clustering_weight": "control.weight",
              "algorithm": "control.algorithm", "resolution": "control.gamma", "seed": "control.seed",
              "null_replicates": "state.null_replicates", "noise_seeds": "state.noise_seeds"}


def _state_th(field: str, label: str, key_field: str) -> html.Th:
    """A Network State row's name: with both help layers when it shows a metric or a choice that needs interpretation,
    the key field as the tooltip's last line (workbench.js styles "Field:" like "Column:")."""
    if field not in STATE_HELP:
        return html.Th(label, title=f"State key field: {key_field}")
    last = ("field", field) if field == key_field else None  # n_games is derived, not a key field
    return html.Th(html.Span(label, className="term"), tabIndex="0", **H.attrs(STATE_HELP[field], WIRE, last=last))


def state_table(key: dict[str, Any], state_id: str, dataset_label: str, n_games: int, n_rows: int,
                names: dict[int, str]) -> list[Any]:
    """Analysis Report §1: the state_id (click to copy), then the Network State as a short table a reader can
    cite (tags by name, never by bare id), then the raw state key behind "Show JSON"."""
    def tags(ids: list[int]) -> str:
        return ", ".join(names.get(int(t), f"tag {t}") for t in ids) or "none"

    weight = "Shared games" if key["clustering_weight"] == "shared_games" else "Lift"
    rows = [
        ("dataset", "Dataset and Build", f"{dataset_label} · Build {key['build_id']}"),
        ("n_games", "Games after the Minimum Months Filter", f"{n_games} of {n_rows}"),
        ("min_months", "Minimum Months Filter", f"≥ {key['min_months']} months observed"),
        ("min_games_per_tag", "Minimum games per tag", str(key["min_games_per_tag"])),
        ("min_shared_games", "Minimum shared games", str(key["min_shared_games"])),
        ("hidden_tag_ids", "Hidden tags", tags(key["hidden_tag_ids"])),
        ("removed_tag_ids", "Removed tags", tags(key["removed_tag_ids"])),
        ("clustering_weight", "Clustering Weight", weight),
        ("algorithm", "Algorithm", str(key["algorithm"]).capitalize()),
        ("resolution", "Resolution γ", str(key["resolution"])),
        ("seed", "Seed", str(key["seed"])),
        ("null_replicates", "Null-model replicates R", str(key["null_replicates"])),
        ("noise_seeds", "Noise seeds K", str(key["noise_seeds"])),
        ("key_version", "Method version", str(key["key_version"])),
    ]
    fields = {"dataset": "dataset, build_id", "n_games": "derived from dataset and min_months"}
    return [
        html.Div([html.Span("Network State ", className="mute"),
                  html.Span(state_id, className="mono copy-id state-id", title="Click to copy",
                            **_copied(WIRE)),
                  html.Span(" — quote it with every network number.", className="mute small")], className="state-head"),
        html.Table(html.Tbody([html.Tr([_state_th(field, label, fields.get(field, field)), html.Td(value)],
                                       id=f"state-row-{field}") for field, label, value in rows]),
                   className="tl state-table"),
        html.Details([html.Summary("Show JSON", className="more"), html.Pre(key_json(key), className="key-json")]),
    ]

"""Text and table views of a Network State: the quality and noise lines, grid columns, the inspector.

Every function that renders visible text takes the Interface Language's translator `tx` (`steamstudy.i18n`) and
writes its words and numbers through it. Tag names, game titles, dataset labels and cluster labels `C1…` are never
translated.
"""

from __future__ import annotations

import html as markup
import math
import re
from functools import lru_cache
from typing import Any

from dash import html

from steamstudy.app import help as H
from steamstudy.export import schema as S
from steamstudy.i18n import Text
from steamstudy.network.metrics import within_z_cap


def z_text(z: float | None, tx: Text) -> str:
    if z is None:
        return tx.num(None)
    return tx.fixed(z, ".0f") if abs(z) >= 10 else tx.fixed(z, ".1f")


def _na_status(status: Any, tx: Text) -> str:
    return tx("n/a ({status})", status=status)


def quality_line(q: dict[str, Any], gamma: str, *, tx: Text) -> str:
    gamma = tx.figure(gamma)
    if q["modularity"] is None:
        qtext = tx("Q (γ = {gamma}) n/a: no edges", gamma=gamma)
    else:
        null_edges = tx.num(None) if q["null_n_edges_mean"] is None else tx.fixed(q["null_n_edges_mean"], ".0f")
        qtext = tx("Q (γ = {gamma}) {q} vs null {mean} ± {sd} (excess {excess}, z {z}; null networks average "
                   "{null_edges} edges vs {edges})", gamma=gamma, q=tx.num(q["modularity"]),
                   mean=tx.num(q["q_null_mean"]), sd=tx.num(q["q_null_sd"]), excess=tx.num(q["q_excess"]),
                   z=z_text(q["modularity_z"], tx), null_edges=null_edges, edges=q["n_edges"])
    sil = tx.num(q["mean_silhouette"]) if q["mean_silhouette"] is not None else _na_status(q["silhouette_status"], tx)
    parts = [qtext, tx("coverage {value}", value=tx.num(q["coverage"])),
             tx("{multi} multi-tag + {one} one-tag", multi=q["n_multi_tag_clusters"], one=q["n_one_tag_clusters"]),
             tx("silhouette (Jaccard game-set distance), descriptive diagnostic, not a selection criterion {value}",
                value=sil)]
    if q["n_disconnected_clusters"]:
        parts.append(tx.n(q["n_disconnected_clusters"], one="{n} disconnected cluster: try Leiden",
                          other="{n} disconnected clusters: try Leiden"))
    return " · ".join(parts)


def noise_line(q: dict[str, Any], k: int, *, tx: Text) -> str:
    sil_sd = tx.num(q["seed_silhouette_sd"])
    return tx("Seed-noise floor (K = {k}): ARI vs. main min {min}, mean {mean} · multi-tag clusters {lo}–{hi} · "
              "SD Q {sd_q} · SD silhouette {sd_sil}", k=k, min=tx.num(q["seed_ari_min"]),
              mean=tx.num(q["seed_ari_mean"]), lo=q["seed_k_min"], hi=q["seed_k_max"],
              sd_q=tx.num(q["seed_modularity_sd"], 3), sd_sil=sil_sd)


def chance_footer(flagged: int, n: int, k: int, *, tx: Text) -> str:
    return tx("{flagged} of {n} tags flagged; if removals acted only like another seed, about {expected} would be "
              "flagged on average (n / (K + 1)). Screening flag, not a significance test.",
              flagged=flagged, n=n, expected=tx.fixed(n / (k + 1), ".0f"))


def _screening(tx: Text) -> str:
    return tx("screening flag, not a significance test")


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

# The Inspector's plain names (English; shown through `tx`). Grids, exports and the Column Index keep the column
# names; each label's tooltip is its guide entry's In short with the column names, and the entry says "Shown in the
# app as" this label.
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
def label_help(label: str, tx: Text, cls: str = "term") -> str:
    """A plain name's two help layers as escaped HTML attributes (see `steamstudy.app.help`)."""
    attrs = {"class": cls, "tabindex": "0", **H.column_attrs(INSPECTOR_LABELS[label], tx)}
    return " ".join(f'{k}="{_e(v)}"' for k, v in attrs.items())


class Markup(str):
    """HTML that is already escaped (a value with its note, a bold number) for `_kv`."""


def _kv(rows: list[tuple[str, Any]], tx: Text) -> html.Div:
    """Metrics as a two-column list: muted plain names (with both help layers), values. One component (see
    `_html`)."""
    items = "".join(f'<dt {label_help(label, tx)}>{_e(tx(label))}</dt>'
                    f'<dd>{value if isinstance(value, Markup) else _e(value)}</dd>' for label, value in rows)
    return _html(f'<dl class="kv">{items}</dl>')


def _note(value: str, note: str) -> Markup:
    return Markup(f"{_e(value)} <small>{_e(note)}</small>")


def _swatch(color: str) -> html.Span:
    return html.Span(className="sw", style={"background": color})


def _bold_count(message: str, n: int) -> list[Any]:
    """A counted sentence whose number is bold: `message` holds the count as "\\0" (`tx.n(…, n="\\0")`)."""
    parts = message.split("\0")
    out: list[Any] = []
    for i, part in enumerate(parts):
        if i:
            out.append(html.B(str(n)))
        if part:
            out.append(part)
    return out


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


def _label_th(label: str, tx: Text) -> str:
    """A right-aligned table header that is an Inspector label, with its help."""
    return f"<th {label_help(label, tx, 'term r')}>{_e(tx(label))}</th>"


def _table(head: str, rows: list[str]) -> str:
    return f'<table class="tl"><thead><tr>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table>'


def _swatch_html(color: str) -> str:
    safe = color if re.fullmatch(r"#[0-9a-fA-F]{3,8}", color) else "#999"
    return f'<span class="sw" style="background:{safe}"></span>'


def _games_table(games: list[dict[str, Any]], tx: Text, with_appid: bool = False) -> str:
    head = (_cell(tx("Rank"), "r", "th") + (_cell(tx("AppID"), tag="th") if with_appid else "")
            + _cell(tx("Name"), tag="th"))
    return _table(head, [f'<tr>{_cell(g["rank"], "r mute")}{_cell(g["appid"], "mono mute") if with_appid else ""}'
                         f'{_cell(g["name"], "name")}</tr>' for g in games])


def _show_all(games: list[dict[str, Any]], tx: Text) -> str:
    """The first `GAMES_SHOWN` games, then "Show all N" with the rest."""
    n = len(games)
    return _games_table(games[:GAMES_SHOWN], tx) + (
        f'<details><summary class="more">{_e(tx("Show all {n}", n=n))}</summary>'
        f'{_games_table(games[GAMES_SHOWN:], tx)}</details>' if n > GAMES_SHOWN else "")


def _connected_table(connected: list[dict[str, Any]], tx: Text) -> str:
    """Connected tags; a row selects its link (graph.js listens for clicks on `data-edge`)."""
    head = _cell(tx("Tag"), tag="th") + _label_th("Shared games", tx) + _label_th("Lift", tx)
    title = _e(tx("Select this link"))
    return _table(head, [f'<tr class="click" data-edge="{_e(c["edge"])}" tabindex="0" title="{title}">'
                         f'<td>{_swatch_html(c["color"])}{_e(c["tag"])}</td>{_cell(c["shared"], "r")}'
                         f'{_cell(tx.num(c["lift"]), "r")}</tr>' for c in connected])


def node_inspector(node: dict[str, Any], weight: str, rs_row: dict[str, Any] | None, cluster_size: int,
                   stale: bool, games: list[dict[str, Any]] | None = None,
                   connected: list[dict[str, Any]] | None = None, color: str = "#999", *, tx: Text) -> list[Any]:
    """The tag view: its games, its connected tags, then its metrics (and its Removal Sensitivity, if run)."""
    games, connected = games or [], connected or []
    active = "strength_shared" if weight == "shared_games" else "strength_lift"
    used_note = tx("used for clustering")
    used = lambda column, value: _note(value, used_note) if column.startswith(active) else value  # noqa: E731
    within = node["within_z"]
    cap = within_z_cap(cluster_size) if cluster_size >= 2 else None
    within_text: Any = tx.num(None) if within is None else _note(
        tx.num(within, 1), tx("max {cap} in a {size}-tag cluster; not comparable across cluster sizes",
                              cap=tx.num(cap, 1), size=cluster_size))
    silhouette: Any = _note(tx.num(node["silhouette"]), tx("descriptive")) if node["silhouette"] is not None \
        else _note(tx.num(None), str(node["silhouette_status"]))
    n = len(games)
    out: list[Any] = [
        html.H4([_swatch(color), node["tag"]] + ([html.Span("◆ " + tx("Cluster Center"), className="badge")]
                                                 if node["is_center"] else []), className="i-title"),
        html.P(tx.n(cluster_size, one="Tag {tag_id} · {cluster} ({n} tag)", other="Tag {tag_id} · {cluster} ({n} tags)",
                    tag_id=node["tag_id"], cluster=node["cluster"]), className="i-sub"),
        html.P(_bold_count(tx.n(n, one="{n} game in the network has this tag",
                                other="{n} games in the network have this tag", n="\0"), n), className="lead"),
        _html(_show_all(games, tx)),
    ]
    out.append(html.Div([tx("Connected tags") + " ",
                         html.Span(tx("{n}, by shared games", n=len(connected)), className="cnt")], className="i-h"))
    out.append(_html(_connected_table(connected, tx)))
    out.append(html.Div(tx("Metrics"), className="i-h"))
    out.append(_kv([
        ("Cluster", node["cluster"]),
        ("Games", str(node["n_games"])),
        ("Total shared games", used("strength_shared", tx.num(node["strength_shared"]))),
        ("Total lift", used("strength_lift", tx.num(node["strength_lift"]))),
        ("Shared games in own cluster", used("strength_shared_intra", tx.num(node["strength_shared_intra"]))),
        ("Lift in own cluster", used("strength_lift_intra", tx.num(node["strength_lift_intra"]))),
        ("Links · in own cluster", f"{node['degree']} · {node['degree_intra']}"),
        ("Membership Stability", tx.num(node["membership_stability"])),
        ("Prominence in own cluster (z)", within_text),
        ("Spread across clusters", tx.num(node["participation"])),
        ("Fit to own cluster (silhouette)", silhouette),
        ("Mean game-set distance to members", tx.num(node["medoid_score"], 3)),
        ("Cluster Center", tx.num(True) + " ◆" if node["is_center"] else tx.num(False)),
    ], tx))
    if rs_row is not None:
        out += [html.Div(tx("Removal Sensitivity (stale: other settings)") if stale else tx("Removal Sensitivity"),
                         className="i-h"),
                _kv([
                    ("Agreement after removal (ARI, reclustered)", tx.num(rs_row["rc_ari"])),
                    ("Beyond seed noise", _note(tx.num(bool(rs_row["rc_ari_beyond_noise"])), _screening(tx))),
                    ("Change in Q (reclustered)", tx.num(rs_row["rc_delta_modularity"], 3)),
                    ("Silhouette after removal (reclustered)", _transition(rs_row, "rc", tx)),
                    ("Change in multi-tag · one-tag clusters", f"{rs_row['rc_delta_k']} · {rs_row['rc_delta_s']}"),
                    ("Cluster Centers lost", ", ".join(rs_row["rc_centers_lost"] or []) or tx("none")),
                    ("Change in Q (clusters kept)", tx.num(rs_row["fp_delta_modularity"], 3)),
                    ("Silhouette after removal (clusters kept)", _transition(rs_row, "fp", tx)),
                ], tx)]
    return out


def _transition(row: dict[str, Any], prefix: str, tx: Text) -> str:
    after, status, delta = row[f"{prefix}_silhouette_after"], row[f"{prefix}_silhouette_after_status"], row[f"{prefix}_delta_silhouette"]
    if delta is not None:
        return tx("Δ {delta} (after {after})", delta=tx.num(delta, 3), after=tx.num(after))
    return f"→ {tx.num(after)}" if after is not None else f"→ {_na_status(status, tx)}"


def edge_inspector(edge: dict[str, Any], games: list[dict[str, Any]], *, tx: Text, pair: str | None = None,
                   from_pair: str | None = None) -> list[Any]:
    """The link view. `pair` (a link between two groups) offers "show this pair"; `from_pair` (opened from a pair's
    list of links) offers the way back to it."""
    same = edge["source_cluster"] == edge["target_cluster"]
    nav = ""
    if from_pair:
        a, _, b = from_pair.partition("|")
        nav = (f'<button class="btn small" data-pair="{_e(from_pair)}">'
               f'{_e("← " + _group_name(a, tx) + " ↔ " + _group_name(b, tx))}</button>')
    elif pair:
        nav = f'<button class="btn small" data-pair="{_e(pair)}">{_e(tx("show this pair"))}</button>'
    return [
        *([_html(nav)] if nav else []),
        html.H4([edge["source_tag"], html.Span(" — ", className="mute"), edge["target_tag"]], className="i-title"),
        html.P(tx("Inside {cluster}", cluster=edge["source_cluster"]) if same
               else tx("Between {a} and {b}", a=edge["source_cluster"], b=edge["target_cluster"]), className="i-sub"),
        _kv([("Shared games", Markup(f"<b>{_e(edge['shared_games'])}</b>")), ("Lift", tx.num(edge["lift"]))], tx),
        html.Div([tx("Games having both tags") + " ", html.Span(str(len(games)), className="cnt")], className="i-h"),
        _html(_games_table(games, tx, with_appid=True)),
    ]


def _cluster_games_table(games: list[dict[str, Any]], names: dict[int, str], one_tag: bool, tx: Text) -> str:
    """Games within a Cluster: Rank · Name · Matched · of its tags · Tags (a One-Tag Cluster drops the two constant
    columns). Rows are inert."""
    head = _cell(tx("Rank"), "r", "th") + _cell(tx("Name"), tag="th")
    if not one_tag:
        head += _cell(tx("Matched"), "r", "th")
    head += _cell(tx("of its tags"), "r", "th") + ("" if one_tag else _cell(tx("Tags"), tag="th"))
    rows = []
    for g in games:
        row = _cell(g["rank"], "r mute") + _cell(g["name"], "name")
        if not one_tag:
            row += _cell(tx("{matched} / {size}", matched=g["matched"], size=g["cluster_size"]), "r")
        row += _cell(tx.pct(g["share_of_game"], 0), "r")
        if not one_tag:
            row += _cell(", ".join(names.get(t, str(t)) for t in g["matched_tag_ids"]), "tags")
        rows.append(f"<tr>{row}</tr>")
    return _table(head, rows)


def cluster_games_section(cluster: dict[str, Any], games: list[dict[str, Any]], n_games: int,
                          names: dict[int, str], *, tx: Text) -> list[Any]:
    """The Cluster Inspector's Games section: every game of the network with at least one of its tags, most matched
    first, then by rank; the first `GAMES_SHOWN`, then "Show all N"."""
    one_tag = cluster["kind"] != "multi_tag"
    n = len(games)
    if one_tag:
        lead = tx.n(n, one="{n} game has its tag", other="{n} games have its tag", n="\0")
    else:
        lead = tx.n(n, one="{n} of {total} games has at least one of its {size} tags",
                    other="{n} of {total} games have at least one of its {size} tags", n="\0", total=n_games,
                    size=cluster["size"])
    table = _cluster_games_table(games[:GAMES_SHOWN], names, one_tag, tx)
    if n > GAMES_SHOWN:
        table += (f'<details><summary class="more">{_e(tx("Show all {n}", n=n))}</summary>'
                  f'{_cluster_games_table(games[GAMES_SHOWN:], names, one_tag, tx)}</details>')
    return [html.Div(tx("Games"), className="i-h"), html.P(_bold_count(lead, n), className="lead"), _html(table)]


def cluster_inspector(cluster: dict[str, Any], members: list[dict[str, Any]], weight: str, color: str = "#999", *,
                      tx: Text, games: list[Any] | None = None, connections: list[Any] | None = None) -> list[Any]:
    """The Cluster view: its metrics, its Members, then its Games (`cluster_games_section`) and its Connections
    (`connections_section`), both built by the caller."""
    out: list[Any] = [
        html.H4([_swatch(color), tx.n(cluster["size"], one="{cluster} · {n} tag", other="{cluster} · {n} tags",
                                      cluster=cluster["cluster"])], className="i-title"),
        html.P(tx("Multi-Tag Cluster") if cluster["kind"] == "multi_tag" else tx("One-Tag Cluster"), className="i-sub"),
    ]
    if not cluster["connected"]:
        out.append(html.P(tx("This Louvain cluster is not a connected group of tags (never split). The Leiden mode "
                             "avoids such clusters."), className="warning"))
    out.append(_kv([
        ("Cluster Center", ("◆ " + cluster["center"]) if cluster["center"]
         else tx("none ({status})", status=cluster["center_status"])),
        ("Center's game-set distance", tx.num(cluster["center_medoid_score"], 3)),
        ("Most-linked member", cluster["top_strength_tag"] or tx.num(None)),
        ("Center is the most-linked member", tx.num(cluster["center_is_top_strength"])),
        ("Mean Membership Stability", tx.num(cluster["mean_membership_stability"])),
        ("Boundary crossing (conductance)", tx.num(cluster["conductance"]) if cluster["conductance"] is not None
         else _na_status(cluster["conductance_status"], tx)),
    ], tx))
    out.append(html.Div([tx("Members") + " ", html.Span(tx("by game-set distance to the others"), className="cnt")],
                        className="i-h"))
    head = _cell(tx("Tag"), tag="th") + "".join(_label_th(label, tx) for label in (
        "Games", "Mean game-set distance to members", "Membership Stability"))
    out.append(_html(_table(
        head,
        [f'<tr>{_cell(("◆ " if m["is_center"] else "") + m["tag"])}{_cell(m["n_games"], "r")}'
         f'{_cell(tx.num(m["medoid_score"], 3), "r")}{_cell(tx.num(m["membership_stability"]), "r")}</tr>'
         for m in members])))
    return out + list(games or []) + list(connections or [])


# ----------------------------------------------------------------------------- Cluster connections (issue 18)

POOL = "one_tag_pool"


def pair_id(a: str, b: str) -> str:
    """A pair selection's id: the two groups in the connections table's order."""
    return f"{a}|{b}"


def _group_name(label: str, tx: Text) -> str:
    return tx("pool of one-tag clusters") if label == POOL else label


def _share(value: float | None, tx: Text) -> str:
    """A Connection Share: a whole percent, one decimal below 1 %."""
    if value is None:
        return tx.num(None)
    return tx.pct(value, 0 if value >= 0.01 or value == 0 else 1)


def _total(value: float, weight: str, tx: Text) -> str:
    """A total in its weight's format: shared games whole, Lift to one decimal."""
    return tx.fixed(value, ".0f") if weight == "shared_games" else tx.fixed(value, ".1f")


def _ratio_bar(ratio: float | None, gamma: float, tx: Text) -> str:
    """The ratio with a 0…γ bar marking 1 (a value a hair above γ fills the bar and keeps its number)."""
    if ratio is None:
        return _e(tx.num(None))
    top = gamma if gamma > 0 else 1.0
    fill_ = min(ratio / top, 1.0) * 100
    one = min(1.0 / top, 1.0) * 100
    return (f'<span class="rbar"><span class="rbar-fill" style="width:{fill_:.1f}%"></span>'
            f'<span class="rbar-one" style="left:{one:.1f}%"></span></span> {_e(tx.num(ratio))}')


def ranked_partners(cluster: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """A group's partners from `cluster_connections.csv` rows, with its own share, ordered by Connection Ratio high
    to low (ties by weight), zero-edge partners at 0, then the rows whose ratio is empty."""
    out = []
    for r in rows:
        if r["cluster_a"] == r["cluster_b"]:
            if r["cluster_a"] != cluster:
                continue
            partner, share = r["cluster_a"], r["share_of_a"]
        elif cluster == r["cluster_a"]:
            partner, share = r["cluster_b"], r["share_of_a"]
        elif cluster == r["cluster_b"]:
            partner, share = r["cluster_a"], r["share_of_b"]
        else:
            continue
        out.append({**r, "partner": partner, "share": share})
    return sorted(out, key=lambda r: (r["ratio"] is None, -(r["ratio"] or 0.0), -r["weight"]))


def _reference(gamma: float, tx: Text) -> html.P:
    return html.P(tx("Ratio: 1 = as their total link weight predicts; γ = {gamma} is the most it can reach.",
                     gamma=tx.fixed(gamma, ".2f")), className="mute small")


def connections_section(cluster: str, rows: list[dict[str, Any]], weight: str, gamma: float, *,
                        tx: Text) -> list[Any]:
    """The Cluster Inspector's Connections section: one row per partner (`ranked_partners`); a row selects the pair."""
    partners = ranked_partners(cluster, rows)
    lift = weight == "lift"
    head = (_cell(tx("Partner"), tag="th") + _help_th(tx("Ratio"), "connections.ratio", tx)
            + _help_th(tx("Share"), "connections.share", tx) + _cell(tx("Total"), "r", "th") + _cell(tx("Links"), "r", "th"))
    if lift:
        head += _help_th(tx("Shared games · ratio"), "connections.ratio", tx)
    body = []
    title = _e(tx("Select this pair"))
    for p in partners:
        a, b = p["cluster_a"], p["cluster_b"]
        cells = (f'<td>{_e(_group_name(p["partner"], tx))}</td><td class="r">{_ratio_bar(p["ratio"], gamma, tx)}</td>'
                 f'{_cell(_share(p["share"], tx), "r")}{_cell(_total(p["weight"], weight, tx), "r")}'
                 f'{_cell(p["edge_count"], "r")}')
        if lift:
            cells += _cell(f'{_total(p["shared_weight"], "shared_games", tx)} · {tx.num(p["shared_ratio"])}', "r")
        body.append(f'<tr class="click" data-pair="{_e(pair_id(a, b))}" tabindex="0" title="{title}">{cells}</tr>')
    out: list[Any] = [html.Div([tx("Connections") + " ", html.Span(tx("by Connection Ratio"), className="cnt")],
                               className="i-h"), _reference(gamma, tx)]
    if lift:
        out.append(html.P(tx("Shared games · ratio: not tied to the clustering; can exceed γ."), className="mute small"))
    out.append(_html(_table(head, body)))
    return out


def _help_th(label: str, key: str, tx: Text) -> str:
    """A right-aligned header with both help layers of a help key (`steamstudy.app.help`)."""
    attrs = {"class": "term r", "tabindex": "0", **H.attrs(key, tx)}
    return "<th " + " ".join(f'{k}="{_e(v)}"' for k, v in attrs.items()) + f">{_e(label)}</th>"


def empty_ratio_case(row: dict[str, Any], nodes: list[dict[str, Any]], clusters: list[dict[str, Any]],
                     tx: Text) -> str | None:
    """Why a pair's ratio is empty: a pool of isolated tags only, a pool-pool row with fewer than two linked pool
    tags, or (not expected in practice) no links in the network at all."""
    if row["ratio"] is not None:
        return None
    one_tag = {c["cluster"] for c in clusters if c["kind"] != "multi_tag"}
    linked = sum(1 for n in nodes if n["cluster"] in one_tag and n["degree"] > 0)
    if POOL in (row["cluster_a"], row["cluster_b"]) and linked == 0:
        return tx("Empty: the pool holds isolated tags only, so no link weight is expected.")
    if row["cluster_a"] == row["cluster_b"] == POOL:
        return tx("Empty: fewer than two pool tags have links, so no link weight is expected between them.")
    return tx("Empty: no link weight is expected.")


def pair_links(a: str, b: str, edges: list[dict[str, Any]], one_tag: set[str]) -> list[dict[str, Any]]:
    """The links between two groups (the pool: every One-Tag Cluster), by shared games, the tag in `a` first."""
    group = lambda c: POOL if c in one_tag else c  # noqa: E731
    out = []
    for e in edges:
        ga, gb = group(e["source_cluster"]), group(e["target_cluster"])
        if {ga, gb} != {a, b} or (a == b and (ga != a or e["source_cluster"] == e["target_cluster"])):
            continue
        first = ga == a
        out.append({"edge": f"{e['source_tag_id']}-{e['target_tag_id']}",
                    "tag_a": e["source_tag"] if first else e["target_tag"],
                    "tag_b": e["target_tag"] if first else e["source_tag"],
                    "shared": e["shared_games"], "lift": e["lift"]})
    return sorted(out, key=lambda x: (-x["shared"], str(x["tag_a"]).lower(), str(x["tag_b"]).lower()))


def pair_inspector(row: dict[str, Any], links: list[dict[str, Any]], colors: tuple[str, str], weight: str,
                   gamma: float, empty_case: str | None, *, tx: Text) -> list[Any]:
    """The pair view: both groups, the Connection Ratio with γ, both Connection Shares, the totals and the links
    between them; a link's row selects it."""
    a, b = row["cluster_a"], row["cluster_b"]
    lift = weight == "lift"
    rows = [(tx("Connection Ratio"), Markup(_ratio_bar(row["ratio"], gamma, tx) + " " + _e(tx("of γ = {gamma}",
                                                                                              gamma=tx.fixed(gamma, ".2f"))))),
            (tx("Connection Share of {group}", group=_group_name(a, tx)), _share(row["share_of_a"], tx)),
            (tx("Connection Share of {group}", group=_group_name(b, tx)), _share(row["share_of_b"], tx)),
            (tx("Total"), _total(row["weight"], weight, tx)), (tx("Links"), str(row["edge_count"]))]
    if lift:
        rows += [(tx("Shared-game total"), _total(row["shared_weight"], "shared_games", tx)),
                 (tx("Shared-game ratio (not tied to the clustering; can exceed γ)"), tx.num(row["shared_ratio"]))]
    kv = "".join(f"<dt>{_e(k)}</dt><dd>{v if isinstance(v, Markup) else _e(v)}</dd>" for k, v in rows)
    head = (_cell(tx("Tag in {group}", group=_group_name(a, tx)), tag="th")
            + _cell(tx("Tag in {group}", group=_group_name(b, tx)), tag="th")
            + _label_th("Shared games", tx) + _label_th("Lift", tx))
    title = _e(tx("Select this link"))
    body = [f'<tr class="click" data-edge="{_e(x["edge"])}" data-from-pair="{_e(pair_id(a, b))}" tabindex="0" '
            f'title="{title}"><td>{_e(x["tag_a"])}</td><td>{_e(x["tag_b"])}</td>{_cell(x["shared"], "r")}'
            f'{_cell(tx.num(x["lift"]), "r")}</tr>' for x in links]
    out: list[Any] = [
        html.H4([_swatch(colors[0]), _group_name(a, tx), html.Span(" ↔ ", className="mute"), _swatch(colors[1]),
                 _group_name(b, tx)], className="i-title"),
        html.P(tx("Cluster pair"), className="i-sub"),
        _html(f'<dl class="kv">{kv}</dl>'),
        _reference(gamma, tx),
    ]
    if empty_case:
        out.append(html.P(empty_case, className="mute small"))
    out += [html.Div([tx("Links between them") + " ", html.Span(str(len(links)), className="cnt")], className="i-h"),
            _html(_table(head, body))]
    return out


# ----------------------------------------------------------------------------- tag search and missing tags


def reason_text(reason: str, n_games: int, min_games: int, *, tx: Text) -> str:
    """A `not_in_network.csv` reason in plain words."""
    if reason == "below_min_games":
        return tx.n(n_games, one="{n} game, below {min}", other="{n} games, below {min}", min=min_games)
    words = {"removed": tx("removed"), "defining_tag_hidden": tx("defining tag hidden"),
             "genre_tag_hidden": tx("Genre Tag hidden")}
    return words.get(reason, reason)


def nin_action(reasons: list[str]) -> str | None:
    """The one action that brings a missing tag back, if exactly one does: Restore (removed) or Unhide (hidden)."""
    found = set(reasons)
    if found == {"removed"}:
        return "restore"
    if found and found <= {"genre_tag_hidden", "defining_tag_hidden"}:
        return "unhide"
    return None


def search_options(tables: dict[str, Any], min_games: int, *, tx: Text) -> list[dict[str, Any]]:
    """The header search: every tag of the network (by name, with cluster and games), then every tag not in the
    network (greyed, by games, with all its reasons). Values are `node:<id>` and `nin:<id>`."""
    from steamstudy.app.renderer import cluster_color

    kinds = {r["cluster"]: r["kind"] for r in tables["clusters"]}
    nodes = sorted(tables["nodes"], key=lambda r: (str(r["tag"]).lower(), r["tag_id"]))
    missing = sorted(tables["nin"], key=lambda r: (-r["n_games"], str(r["tag"]).lower()))
    options: list[dict[str, Any]] = [{"label": html.Span(tx("In the network · {n}", n=len(nodes)), className="grp"),
                                      "value": "group:in", "disabled": True, "search": ""}]
    for r in nodes:
        options.append({"label": html.Span([
            html.Span(className="sw", style={"background": cluster_color(r["cluster"], kinds[r["cluster"]])}),
            r["tag"], html.Span(tx.n(r["n_games"], one="{cluster} · {n} game", other="{cluster} · {n} games",
                                     cluster=r["cluster"]), className="why")], className="opt"),
            "value": f"node:{r['tag_id']}", "search": str(r["tag"])})
    if missing:
        options.append({"label": html.Span(tx("Not in the network · {n}", n=len(missing)), className="grp"),
                        "value": "group:nin", "disabled": True, "search": ""})
    for r in missing:
        why = " · ".join(reason_text(x, r["n_games"], min_games, tx=tx) for x in r["reasons"])
        options.append({"label": html.Span([r["tag"], html.Span(why, className="why")], className="opt gone"),
                        "value": f"nin:{r['tag_id']}", "search": str(r["tag"])})
    return options


def nin_inspector(row: dict[str, Any], min_games: int, *, tx: Text) -> list[Any]:
    """The "Not in the network" card: the tag's reasons and games, and the one action that brings it back."""
    action = nin_action(list(row["reasons"]))
    n = row["n_games"]
    out: list[Any] = [
        html.H4(row["tag"]), html.P(tx("Tag {tag_id} · not in the network", tag_id=row["tag_id"]), className="mute"),
        html.P([html.Span(reason_text(x, n, min_games, tx=tx), className="reason") for x in row["reasons"]]),
        html.P(tx.n(n, one="{n} game of the dataset has this tag.", other="{n} games of the dataset have this tag."),
               className="mute"),
    ]
    if action:
        out.append(html.Div([
            html.Button(tx("Restore") if action == "restore" else tx("Unhide"),
                        id={"type": "nin-action", "action": action}, className="btn primary"),
            html.Span(" " + tx("Pressing it changes the Network State."), className="mute small")],
            className="row-inline"))
    else:
        out.append(html.P(tx("No single control brings this tag back; change the settings listed above."),
                          className="mute small"))
    return out


# ----------------------------------------------------------------------------- summary row and quality boxes

def _excess(q: dict[str, Any], tx: Text) -> str:
    return tx.num(None) if q["q_excess"] is None else tx.fixed(q["q_excess"], "+.2f")


def _stat(label: str, value: str, sub: str, key: str, now: str | None, tx: Text) -> html.Div:
    """One summary number: hover or focus shows its In short, a click opens its guide entry."""
    return html.Div([html.B(value, className="num"), html.Span(label, className="term"),
                     html.Small(sub) if sub else None], className="m", tabIndex="0", **H.attrs(key, tx, now))


def summary_row(q: dict[str, Any], n_rows: int, gamma: str, r: int, *, tx: Text) -> list[Any]:
    """The key numbers above the graph, each large with a muted label and the two help layers."""
    gamma = tx.figure(gamma)
    q_value = tx.num(None) if q["modularity"] is None else tx("{q} · excess {excess}", q=tx.num(q["modularity"]),
                                                              excess=_excess(q, tx))
    sil = tx.num(q["mean_silhouette"])
    q_now = (tx("γ = {gamma}; no links, so no Q.", gamma=gamma) if q["modularity"] is None else
             tx("γ = {gamma}; null mean {mean} ± {sd} from R = {r} shuffled networks; excess = Q − null mean.",
                gamma=gamma, mean=tx.num(q["q_null_mean"]), sd=tx.num(q["q_null_sd"]), r=r))
    if q["seed_k_min"] is None:
        clusters_now = None
    elif q["seed_k_min"] == q["seed_k_max"]:
        clusters_now = tx.n(q["seed_k_min"], one="all other seeds give {n} multi-tag cluster.",
                            other="all other seeds give {n} multi-tag clusters.")
    else:
        clusters_now = tx("other seeds give {lo}–{hi} multi-tag clusters.", lo=q["seed_k_min"], hi=q["seed_k_max"])
    items = [
        (tx("Games"), tx("{n} of {total}", n=q["n_dataset_games"], total=n_rows), "", "summary.games",
         tx("{n} of the dataset's {total} games pass the Minimum Months Filter.", n=q["n_dataset_games"],
            total=n_rows)),
        (tx("Tags"), str(q["n_nodes"]), "", "summary.tags", None),
        (tx("Links"), str(q["n_edges"]), "", "summary.links",
         None if q["null_n_edges_mean"] is None else
         tx("shuffled networks average {n} links.", n=tx.fixed(q["null_n_edges_mean"], ".0f"))),
        (tx("Clusters"), f"{q['n_multi_tag_clusters']} + {q['n_one_tag_clusters']}", tx("multi-tag + one-tag"),
         "summary.clusters", clusters_now),
        ("Q", q_value, "", "summary.q", q_now),
        (tx("Silhouette"), tx("{value} · descriptive", value=sil), "", "summary.silhouette",
         None if q["seed_silhouette_sd"] is None else
         tx("SD across seeds {sd}.", sd=tx.num(q["seed_silhouette_sd"]))),
    ]
    return [_stat(*item, tx) for item in items]


def quality_boxes(q: dict[str, Any], gamma: str, k: int, r: int, *, tx: Text) -> list[Any]:
    """The Cluster quality tab: five boxes with both help layers, then the two full sentences once, small and muted."""
    gamma_shown = tx.figure(gamma)
    null = tx("null mean {mean} ± {sd} from R = {r} shuffled networks", mean=tx.num(q["q_null_mean"]),
              sd=tx.num(q["q_null_sd"]), r=r)
    if q["modularity"] is None:
        excess_sub, q_now, excess_now = tx("no edges"), tx("γ = {gamma}; no links, so no Q.", gamma=gamma_shown), None
    else:
        excess_sub = tx("z {z} · null {mean} ± {sd} · excess over the null mean", z=z_text(q["modularity_z"], tx),
                        mean=tx.num(q["q_null_mean"]), sd=tx.num(q["q_null_sd"]))
        q_now = tx("γ = {gamma}; {null}.", gamma=gamma_shown, null=null)
        excess_now = tx("Q {q} − {null}; z {z}.", q=tx.num(q["modularity"]), null=null,
                        z=z_text(q["modularity_z"], tx))
    sil = tx.num(q["mean_silhouette"]) if q["mean_silhouette"] is not None else _na_status(q["silhouette_status"], tx)
    boxes = [
        ("Q", tx.num(q["modularity"]), f"γ = {gamma_shown}", "quality.q", q_now),
        (tx("Null-model excess"), _excess(q, tx), excess_sub, "quality.excess", excess_now),
        (tx("Coverage"), tx.num(q["coverage"]), tx("link weight inside clusters"), "quality.coverage", None),
        (tx("Silhouette"), sil, tx("descriptive"), "quality.silhouette",
         None if q["seed_silhouette_sd"] is None else
         tx("SD across the K = {k} seeds {sd}.", k=k, sd=tx.num(q["seed_silhouette_sd"]))),
        (tx("Seed noise"), tx.num(q["seed_ari_min"]), tx("ARI min · mean {mean}", mean=tx.num(q["seed_ari_mean"])),
         "quality.seed_noise",
         tx("each of the K = {k} extra seeds against the clusters shown; min is the seed that differed most.", k=k)),
    ]
    return [
        html.Div([html.Div([html.Div(html.Span(label, className="term"), className="l"),
                            html.Div(value, className="v"), html.Div(sub, className="s")],
                           className="qbox", tabIndex="0", **H.attrs(key, tx, now))
                  for label, value, sub, key, now in boxes], className="qboxes"),
        html.Div([html.P(quality_line(q, gamma, tx=tx), tabIndex="0", **H.attrs("quality.sentence", tx)),
                  html.P(noise_line(q, k, tx=tx), tabIndex="0", **H.attrs("quality.noise_sentence", tx))],
                 className="sentences"),
    ]


def _copied(tx: Text) -> dict[str, Any]:
    """The word app.css shows after a state_id is copied (`content: attr(data-copied)`)."""
    return {"data-copied": tx("copied")}


def state_sentence(dataset_label: str, n_rows: int, settings: Any, hidden: list[str], defining: str | None,
                   removed: list[str], state_id: str, *, tx: Text) -> list[Any]:
    """The Network State in one readable sentence, ending with its state_id (click to copy)."""
    genre = [h for h in hidden if h != defining]
    if not genre:
        hidden_text = tx("no Genre Tag hidden")
    elif len(genre) <= 3:
        hidden_text = tx.n(len(genre), one="Genre Tag {tags} hidden", other="Genre Tags {tags} hidden",
                           tags=", ".join(genre))
    else:
        hidden_text = tx.n(len(genre), one="{n} Genre Tag hidden", other="{n} Genre Tags hidden")
    if defining and defining in hidden:
        hidden_text = tx("{hidden}, defining tag {tag} hidden", hidden=hidden_text, tag=defining)
    removed_text = tx("removed: {tags}", tags=", ".join(removed)) if removed else tx("no tag removed")
    weight = tx("shared games") if settings.clustering_weight == "shared_games" else tx("lift")
    sentence = tx("{dataset} Top {rows}, games with ≥ {months} months observed; tags on ≥ {g} games, links of ≥ {s} "
                  "shared games; {hidden}; {removed}; {algorithm} on {weight}, γ {gamma}, seed {seed} · ",
                  dataset=dataset_label, rows=n_rows, months=settings.min_months, g=settings.min_games_per_tag,
                  s=settings.min_shared_games, hidden=hidden_text, removed=removed_text,
                  algorithm=settings.algorithm.capitalize(), weight=weight,
                  gamma=tx.fixed(settings.resolution, ".2f"), seed=settings.seed)
    return [sentence, html.Span(state_id, className="mono copy-id", title=tx("Network State id: click to copy"),
                                **_copied(tx))]


# ----------------------------------------------------------------------------- Analysis Report §1


def key_json(key: dict[str, Any]) -> str:
    """The state key as JSON with one field per line (a list of tag ids stays on its field's line)."""
    import json

    return "{\n" + ",\n".join(f"  {json.dumps(k)}: {json.dumps(v, ensure_ascii=False)}" for k, v in key.items()) + "\n}"


# The Network State fields that show a metric or a choice whose effect needs interpretation -> their help key.
STATE_HELP = {"n_games": "state.n_games", "min_months": "control.min-months", "clustering_weight": "control.weight",
              "algorithm": "control.algorithm", "resolution": "control.gamma", "seed": "control.seed",
              "null_replicates": "state.null_replicates", "noise_seeds": "state.noise_seeds"}


def _state_th(field: str, label: str, key_field: str, tx: Text) -> html.Th:
    """A Network State row's name: with both help layers when it shows a metric or a choice that needs interpretation,
    the key field as the tooltip's last line (workbench.js styles the field line like the column line)."""
    if field not in STATE_HELP:
        return html.Th(label, title=tx("State key field: {field}", field=key_field))
    last = ("field", field) if field == key_field else None  # n_games is derived, not a key field
    return html.Th(html.Span(label, className="term"), tabIndex="0", **H.attrs(STATE_HELP[field], tx, last=last))


def state_table(key: dict[str, Any], state_id: str, dataset_label: str, n_games: int, n_rows: int,
                names: dict[int, str], *, tx: Text) -> list[Any]:
    """Analysis Report §1: the state_id (click to copy), then the Network State as a short table a reader can
    cite (tags by name, never by bare id), then the raw state key behind "Show JSON"."""
    def tags(ids: list[int]) -> str:
        return ", ".join(names.get(int(t), tx("tag {tag_id}", tag_id=t)) for t in ids) or tx("none")

    weight = tx("Shared games") if key["clustering_weight"] == "shared_games" else tx("Lift")
    rows = [
        ("dataset", tx("Dataset and Build"), tx("{dataset} · Build {build_id}", dataset=dataset_label,
                                                build_id=key["build_id"])),
        ("n_games", tx("Games after the Minimum Months Filter"), tx("{n} of {total}", n=n_games, total=n_rows)),
        ("min_months", tx("Minimum Months Filter"), tx("≥ {n} months observed", n=key["min_months"])),
        ("min_games_per_tag", tx("Minimum games per tag"), str(key["min_games_per_tag"])),
        ("min_shared_games", tx("Minimum shared games"), str(key["min_shared_games"])),
        ("hidden_tag_ids", tx("Hidden tags"), tags(key["hidden_tag_ids"])),
        ("removed_tag_ids", tx("Removed tags"), tags(key["removed_tag_ids"])),
        ("clustering_weight", tx("Clustering Weight"), weight),
        ("algorithm", tx("Algorithm"), str(key["algorithm"]).capitalize()),
        ("resolution", tx("Resolution γ"), tx.figure(str(key["resolution"]))),
        ("seed", tx("Seed"), str(key["seed"])),
        ("null_replicates", tx("Null-model replicates R"), str(key["null_replicates"])),
        ("noise_seeds", tx("Noise seeds K"), str(key["noise_seeds"])),
        ("key_version", tx("Method version"), str(key["key_version"])),
    ]
    fields = {"dataset": "dataset, build_id", "n_games": tx("derived from dataset and min_months")}
    return [
        html.Div([html.Span(tx("Network State") + " ", className="mute"),
                  html.Span(state_id, className="mono copy-id state-id", title=tx("Click to copy"), **_copied(tx)),
                  html.Span(" " + tx("— quote it with every network number."), className="mute small")],
                 className="state-head"),
        html.Table(html.Tbody([html.Tr([_state_th(field, label, fields.get(field, field), tx), html.Td(value)],
                                       id=f"state-row-{field}") for field, label, value in rows]),
                   className="tl state-table"),
        html.Details([html.Summary(tx("Show JSON"), className="more"), html.Pre(key_json(key), className="key-json")]),
    ]

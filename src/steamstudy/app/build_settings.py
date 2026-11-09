"""A Build's settings, read-only: the Build menu's Settings… on each Build row, in the repository and in App Bundles.

A Build never changes, so this is the only way to read its settings in the app (to change them, Duplicate it into a
draft). They are shown by the draft dialog's steps, with the same help: the Top-N settings as a summary (datasets,
tags per game, the exclusion limit and each rule's tags), every settings file as the text a draft edits.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from dash import html

from steamstudy import build_admin as BA
from steamstudy import toml_text
from steamstudy.app import draft_dialog as DD
from steamstudy.i18n import Text


def view(root: Path, ref: str, tx: Text) -> list[Any]:
    """The Settings… dialog's body for a Build (`<source_id>/<build_id>`)."""
    files, info, bj = BA.build_settings(root, ref)
    imported = bj.get("source") == "import"
    out: list[Any] = [
        html.Button("?", id={"type": "help", "panel": "build-settings"}, className="help dd-help",
                    title=tx("Open the User Guide section")),
        html.P([html.B(info.name), " ", html.Span(info.ref, className="mono mute")]),
    ]
    if info.description:
        out.append(html.P(info.description, className="mute"))
    source = (tx("Import {id}", id=info.source_id) if imported else
              tx("Snapshot {id} ({form} form)", id=info.source_id, form=tx(bj.get("snapshot_form") or "raw")))
    out.append(html.P([html.B(tx("Built from")), " ", source]))
    out.append(html.P(tx("A Build never changes: to try other settings, Duplicate it into a draft."),
                      className="mute small"))
    out += _top_n(files, bj, tx, imported)
    for step in ("curation", "reports", "network"):
        boxes = [f for f in DD.TOML_FILES[step] if not (imported and f in DD.STEAM_ONLY_FILES)]
        out.append(html.Details([html.Summary(html.B(tx(DD.STEP_TITLES[step]))),
                                 *[_text_box(files, f, imported) for f in boxes]], className="bs-step"))
    return out


def _top_n(files: dict[str, Any], bj: dict[str, Any], tx: Text, imported: bool) -> list[Any]:
    ds = files.get("datasets", {})
    ex = files.get("exclusions", {})
    sizes = bj.get("dataset_sizes", {})
    depth = ds.get("tag_depth", "all")
    limit = ex.get("global_rank_limit")
    rows = [html.Tr([html.Td(d.get("key"), className="mono"), html.Td(d.get("label", "")),
                     html.Td((d.get("defining_tag") or {}).get("name", "—")), html.Td(d.get("list_size", 100)),
                     html.Td(sizes.get(d.get("key"), {}).get("eligible_pool", ""))])
            for d in ds.get("dataset", [])]
    head = html.Tr([html.Th(tx("Dataset key")), html.Th(tx("Label")),
                    html.Th(DD.term(tx("Defining tag"), "draft.defining_tag", tx)),
                    html.Th(DD.term(tx("List Size"), "draft.list_size", tx)),
                    html.Th(DD.term(tx("Eligible Pool"), "draft.eligible_pool", tx))])
    facts = [html.Li([DD.term(tx("Tags per game (Tag Depth)"), "draft.tag_depth", tx), ": ",
                      html.B(tx("all") if depth == "all" else str(depth))]),
             html.Li([DD.term(tx("Global rank limit"), "draft.exclusions", tx), ": ",
                      html.B(tx("none") if limit is None else str(limit)), " ",
                      html.Span(tx("(an exclusion rule's tag counts only within this many of a game's first tags)"),
                                className="mute small")])]
    if not imported:
        facts.append(html.Li([tx("App types"), ": ", html.B(", ".join(ex.get("allowed_app_types", ["game"])))]))
    rules = [html.Li([html.Span(r.get("name", ""), className="mono"), " · ", r.get("label", r.get("name", "")),
                      ": ", _signals(r, limit, tx)]) for r in ex.get("rule", [])]
    return [html.H4(tx(DD.STEP_TITLES["top_n"])), html.Table([head, *rows], className="dd-table"),
            html.Ul(facts),
            html.H4(DD.term(tx("Exclusion rules"), "draft.exclusions", tx)),
            html.P(tx("The fixed rules run first ({before}), then these, then {after}.",
                      before=", ".join(tx(t) for t in DD.FIXED_BEFORE), after=", ".join(tx(t) for t in DD.FIXED_AFTER)),
                   className="mute small"),
            html.Ol(rules) if rules else html.P(tx("No named rules."), className="mute")]


def _signals(rule: dict[str, Any], limit: Any, tx: Text) -> str:
    """A rule's signals in a line: its tags with the position each counts within, then the other signals."""
    shared, parts = [], []
    for tag in rule.get("tags", []):
        name = str(tag.get("name", "")) if isinstance(tag, dict) else str(tag)
        own = tag.get("rank_limit") if isinstance(tag, dict) else None
        if own is not None:  # a tag with its own rank limit
            parts.append(tx("{tag} (within the first {n} tags)", tag=name, n=own))
        else:
            shared.append(name)
    if shared:  # the tags that count within the exclusion limit: named once, together
        joined = ", ".join(shared)
        parts.insert(0, tx("{tag} (within the first {n} tags)", tag=joined, n=limit) if limit is not None else joined)
    if rule.get("name_only"):
        parts.append(tx("name: {names}", names=", ".join(rule["name_only"])))
    if rule.get("content_descriptor_ids"):
        parts.append(tx("content descriptors {ids}", ids=", ".join(map(str, rule["content_descriptor_ids"]))))
    if rule.get("adult_only_notice"):
        parts.append(tx("the adults-only notice"))
    return "; ".join(parts)


def _text_box(files: dict[str, Any], file: str, imported: bool) -> html.Div:
    label = "exclusions.toml [[content_flag]]" if file == "content_flags" else f"{file}.toml"
    data = DD.box_data(files, file, imported)
    return html.Div([html.Div(label, className="mono small mute"),
                     html.Pre(toml_text.dumps(data) if data else "", className="bs-text")])


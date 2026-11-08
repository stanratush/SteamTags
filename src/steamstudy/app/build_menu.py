"""The Build menu: the header's Build name opens a lineage tree per Snapshot or Import (issue 28).

In the repository the tree switches Builds, starts and opens drafts (`draft_dialog`), duplicates and deletes Builds,
discards drafts, imports data (issue 33) and shows Manage Builds… with sizes. In an App Bundle it only switches, and it
is hidden when the Bundle ships one Build. The tree is read from disk each time it is shown (`build_tree`).

Build runs (`build_runs`) are shown in every tab by the strip under the header.
"""

from __future__ import annotations

import base64
import io
import shutil
import tempfile
import urllib.parse
from pathlib import Path
from typing import Any

import dash
from dash import ALL, Input, Output, State, ctx, dcc, html, no_update, set_props
from dash.exceptions import PreventUpdate

from steamstudy import build_admin as BA
from steamstudy.app import build_runs
from steamstudy.app.loader import build_folder, builds_root, ref_of
from steamstudy.app.relabel import Labels, msg
from steamstudy.build_tree import BuildNode, SourceTree, build_tree, is_bundle, walk
from steamstudy.i18n import Text, lang_of, text

HIDDEN = {"display": "none"}


def repo_root() -> Path | None:
    root = builds_root()
    return root.parent if root else None


def editable() -> bool:
    """Whether the menu can make Builds: the app runs from the repository, not from an App Bundle."""
    root = repo_root()
    return root is not None and not is_bundle(root)


def build_url(ref: str, mode: str | None = None, dataset: str | None = None) -> str:
    query = {k: v for k, v in (("mode", mode), ("dataset", dataset)) if v}
    return f"/build/{ref}" + (f"?{urllib.parse.urlencode(query)}" if query else "")


# ----------------------------------------------------------------------------- layout


def header_button(L: Labels, brand: Any) -> html.Button:
    """The header's Build name as the menu's button (`brand` is the `brand-build` span)."""
    return html.Button([brand, html.Span(" ▾", className="mute")], id="build-menu-btn", className="btn quiet bm-btn",
                       title=L.prop("build-menu-btn", "title", msg("Builds: switch, make and manage")))


def layout(L: Labels) -> list[Any]:
    """The menu panel, its dialog, the Build run strip and their stores (placed once in the page)."""
    return [
        html.Div([html.Div(id="bm-tree", className="bm-tree"),
                  html.Div(id="bm-footer", className="bm-footer")],
                 id="build-menu", className="build-menu", style=HIDDEN),
        html.Div([html.Div([html.B(id="bm-dialog-title"),
                            html.Button("×", id="bm-dialog-close", className="x",
                                        title=L.prop("bm-dialog-close", "title", msg("Close")))],
                           className="help-head"),
                  html.Div(id="bm-dialog-body", className="bm-dialog-body")],
                 id="bm-dialog", className="help-modal bm-dialog", style=HIDDEN),
        html.Div(id="build-strip", className="build-strip", style=HIDDEN),
        dcc.Interval(id="build-strip-tick", interval=1500),
        dcc.Store(id="bm-pending"),  # {"action": "delete" | "duplicate", "ref": …} awaiting its dialog's button
        dcc.Store(id="draft-open"),  # {"source": …, "slug": …}: the draft whose dialog is open
    ]


# ----------------------------------------------------------------------------- the tree


def _size(n: int, tx: Text) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{tx.num(n, 0) if unit == 'B' else tx.num(n, 1)} {unit}"
        n /= 1024  # type: ignore[assignment]
    return str(n)


def _chips(node: BuildNode, open_ref: str, tx: Text) -> list[Any]:
    chips = []
    if node.ref == open_ref:
        chips.append(html.Span(tx("✓ open in this tab"), className="bm-chip open"))
    if node.latest:
        chips.append(html.Span(tx("latest"), className="bm-chip"))
    if node.test:
        chips.append(html.Span(tx("test"), className="bm-chip warn"))
    return chips


def _build_row(depth: int, node: BuildNode, open_ref: str, tx: Text, *, edit: bool, sizes: bool) -> html.Div:
    origin = []
    if node.orphan == "deleted":
        origin = [html.Span(tx("from a deleted Build"), className="mute small")]
    elif node.orphan:
        origin = [html.Span(tx("from {name} (not in this Bundle)", name=node.parent_name or node.info.parent_build_id),
                            className="mute small")]
    actions = []
    if edit:
        actions = [html.Button(tx("Duplicate"), id={"type": "bm-dup", "ref": node.ref}, className="btn quiet small"),
                   html.Button(tx("Delete"), id={"type": "bm-del", "ref": node.ref}, className="btn quiet small")]
    size = ([html.Span(tx("{size} (app cache {cache})", size=_size(node.size_bytes, tx),
                          cache=_size(node.app_cache_bytes, tx)), className="mute small")] if sizes else [])
    return html.Div([
        html.Button([html.B(node.info.name), *_chips(node, open_ref, tx),
                     html.Span(node.date, className="mute small"), html.Span(node.top_n, className="mute small"),
                     *origin, *size],
                    id={"type": "bm-build", "ref": node.ref}, className="bm-row-main",
                    title=node.info.description or node.ref),
        html.Span(actions, className="bm-actions"),
    ], className="bm-row build", style={"paddingLeft": f"{12 + depth * 18}px"})


def _draft_row(depth: int, draft: BA.Draft, tx: Text) -> html.Div:
    run = build_runs.running_draft(draft.source_id, draft.stored_slug or "")
    if run:
        status = (tx("running {pct}%", pct=min(99, round(100 * run["elapsed_s"] / max(run["estimate_s"], 1))))
                  if run["status"] == "running" else tx("waiting"))
    elif draft.last_failure:
        status = tx("failed")
    else:
        status = tx("draft")
    saved = (draft.saved_at or "").replace("T", " ").rstrip("Z")
    return html.Div([
        html.Button([html.I(draft.name), html.Span(status, className="bm-chip draft"),
                     html.Span(tx("last saved {when}", when=saved), className="mute small")],
                    id={"type": "bm-draft", "source": draft.source_id, "slug": draft.stored_slug or ""},
                    className="bm-row-main"),
        html.Span([html.Button(tx("Discard"), id={"type": "bm-discard", "source": draft.source_id,
                                                  "slug": draft.stored_slug or ""}, className="btn quiet small")],
                  className="bm-actions"),
    ], className="bm-row draft", style={"paddingLeft": f"{12 + depth * 18}px"})


def _source_block(tree: SourceTree, open_ref: str, tx: Text, *, edit: bool, sizes: bool) -> html.Div:
    kind = tx("Import") if tree.kind == "import" else tx("Snapshot")
    forms = {"raw": tx("raw"), "lightweight": tx("lightweight"), "import": ""}
    form_text = ", ".join(forms[f] for f in tree.forms if forms[f])
    rows: list[Any] = [html.Div([html.B(f"{kind} {tree.source_id}"),
                                 html.Span(f" ({form_text})" if form_text else "", className="mute small")],
                                className="bm-source")]
    if edit:
        root_label = tx("Import defaults") if tree.kind == "import" else "config/"
        rows.append(html.Div(html.Button([html.Span(root_label, className="mono"),
                                          html.Span(tx("start a draft from the defaults"), className="mute small")],
                                         id={"type": "bm-root", "source": tree.source_id}, className="bm-row-main"),
                             className="bm-row root"))
        rows += [_draft_row(1, d, tx) for d in tree.drafts]
    base = 1 if edit else 0
    for depth, node in walk(tree.builds):
        rows.append(_build_row(base + depth, node, open_ref, tx, edit=edit, sizes=sizes))
        if edit:
            rows += [_draft_row(base + depth + 1, d, tx) for d in node.drafts]
    return html.Div(rows, className="bm-block")


def tree_view(open_ref: str, tx: Text, *, sizes: bool = False) -> list[Any]:
    root = repo_root()
    if root is None:
        return []
    edit = not is_bundle(root)
    trees = build_tree(root, sizes=sizes)
    return [_source_block(t, open_ref, tx, edit=edit, sizes=sizes) for t in trees]


def footer_view(tx: Text) -> list[Any]:
    if not editable():
        return []
    return [html.Button(tx("Duplicate the open Build"), id="bm-dup-open", className="btn small"),
            html.Button(tx("Import data…"), id="bm-import", className="btn small"),
            html.Button(tx("Manage Builds…"), id="bm-manage", className="btn small")]


def menu_visible() -> bool:
    """The menu is hidden in a Bundle that ships one Build (nothing to switch to)."""
    root = repo_root()
    if root is None:
        return False
    if not is_bundle(root):
        return True
    return sum(len(walk(t.builds)) for t in build_tree(root, bundle=True)) > 1


# ----------------------------------------------------------------------------- callbacks


def toggle_menu(n, build_path, lang, style):
    if not n:
        raise PreventUpdate
    if style and style.get("display") != "none":
        return HIDDEN, no_update, no_update
    if not menu_visible():
        raise PreventUpdate
    tx = text(lang_of(lang))
    open_ref = ref_of(build_folder(build_path))
    return {"display": "block"}, tree_view(open_ref, tx), footer_view(tx)


def _clicked() -> Any:
    """The id of the clicked pattern-matching button (None when the trigger is a re-render, not a click)."""
    trig = ctx.triggered[0] if ctx.triggered else None
    if not trig or not trig.get("value"):
        return None
    return ctx.triggered_id


def _dialog(title: str, body: list[Any]) -> None:
    set_props("bm-dialog", {"style": {"display": "flex", "width": "640px"}})
    set_props("bm-dialog-title", {"children": title})
    set_props("bm-dialog-body", {"children": body})


def _close_dialog() -> None:
    set_props("bm-dialog", {"style": HIDDEN})


def _refresh(build_path: str, tx: Text) -> None:
    set_props("bm-tree", {"children": tree_view(ref_of(build_folder(build_path)), tx)})


def tree_click(_b, _r, _d, _dup, _del, _dis, build_path, lang, mode, dataset):
    """A click in the tree: switch, start or open a draft, or ask for a Duplicate, Delete or Discard."""
    target = _clicked()
    if target is None:
        raise PreventUpdate
    tx = text(lang_of(lang))
    root = repo_root()
    kind = target["type"]
    if kind == "bm-build":
        ref = target["ref"]
        if ref == ref_of(build_folder(build_path)):
            set_props("build-menu", {"style": HIDDEN})
            raise PreventUpdate
        set_props("switch-to", {"data": build_url(ref, mode, dataset)})
        return no_update
    if root is None or not editable():
        raise PreventUpdate
    if kind == "bm-root":
        draft = BA.start_draft(root, target["source"], config_dir=root / "config")
        set_props("build-menu", {"style": HIDDEN})
        return {"source": draft.source_id, "slug": draft.stored_slug}
    if kind == "bm-draft":
        set_props("build-menu", {"style": HIDDEN})
        return {"source": target["source"], "slug": target["slug"]}
    if kind == "bm-discard":
        draft = _draft(root, target["source"], target["slug"])
        if draft is not None:
            BA.discard_draft(root, draft)
        _refresh(build_path, tx)
        return no_update
    if kind == "bm-dup":
        _ask_duplicate(root, target["ref"], tx)
        return no_update
    if kind == "bm-del":
        _ask_delete(root, target["ref"], build_path, tx)
        return no_update
    raise PreventUpdate


def _draft(root: Path, source_id: str, slug: str) -> BA.Draft | None:
    return next((d for d in BA.list_drafts(root, source_id) if d.stored_slug == slug), None)


def _sources_for(root: Path, ref: str) -> list[str]:
    """Where a Build may be duplicated: an Import Build within its Import, a Steam Build onto any Snapshot."""
    from steamstudy.build.import_build import is_import

    source = ref.split("/", 1)[0]
    if is_import(root, source):
        return [source]
    return [t.source_id for t in build_tree(root) if t.kind == "snapshot" and t.forms]


def _ask_duplicate(root: Path, ref: str, tx: Text) -> None:
    sources = _sources_for(root, ref)
    source = ref.split("/", 1)[0]
    _dialog(tx("Duplicate {name}", name=BA.parent_name(root, ref) or ref), [
        html.P(tx("The new draft starts from this Build's settings, with this Build as its parent.")),
        html.Label(tx("Snapshot or Import to build from"), htmlFor="bm-dup-source", className="l"),
        dcc.Dropdown(id="bm-dup-source", options=[{"label": s, "value": s} for s in sources],
                     value=source if source in sources else (sources[0] if sources else None), clearable=False),
        html.Div(html.Button(tx("Duplicate"), id="bm-dup-go", className="btn primary"), className="row-inline"),
    ])
    set_props("bm-pending", {"data": {"action": "duplicate", "ref": ref}})


def _ask_delete(root: Path, ref: str, build_path: str, tx: Text) -> None:
    open_ref = ref_of(build_folder(build_path))
    try:
        plan = BA.deletion_plan(root, ref, open_ref)
    except BA.DeleteRefused:
        _dialog(tx("Delete"), [html.P(tx("This tab shows this Build: switch to another Build first."),
                                      className="warning")])
        return
    moves = [html.Li(tx("the {where} latest pointer moves to {to}", where=k if k != "root" else tx("root"),
                        to=v or tx("nothing (it is removed)"))) for k, v in sorted(plan.latest_moves.items())]
    orphans = [html.Li(tx("{n} Builds and {m} drafts lose their parent and move to the root",
                          n=len(plan.orphaned_builds), m=len(plan.orphaned_drafts)))] if (
        plan.orphaned_builds or plan.orphaned_drafts) else []
    bundles = [html.Li(tx("Bundles naming it: {names}", names=", ".join(plan.bundles)))] if plan.bundles else []
    _dialog(tx("Delete {name}?", name=plan.name), [
        html.P(tx("This deletes the Build folder {ref} ({size}, of which app cache {cache}). It cannot be undone.",
                  ref=plan.ref, size=_size(plan.size_bytes, tx), cache=_size(plan.app_cache_bytes, tx))),
        html.Ul([*moves, *orphans, *bundles]),
        html.P(tx("Exports made from it will no longer open with Open Network State…"), className="mute small"),
        html.P(tx("Other tabs on this Build will show that it no longer exists."), className="mute small"),
        html.Div(html.Button(tx("Delete the Build"), id="bm-del-go", className="btn primary danger"),
                 className="row-inline"),
    ])
    set_props("bm-pending", {"data": {"action": "delete", "ref": ref}})


def dialog_go(_dup, _del, _dup_open, pending, source, build_path, lang):
    """The dialog's button: make the duplicate (and open its draft) or delete the Build; or Duplicate the open
    Build from the footer."""
    trig = ctx.triggered_id
    if not ctx.triggered or not ctx.triggered[0].get("value"):
        raise PreventUpdate
    root = repo_root()
    if root is None or not editable():
        raise PreventUpdate
    tx = text(lang_of(lang))
    if trig == "bm-dup-open":
        _ask_duplicate(root, ref_of(build_folder(build_path)), tx)
        raise PreventUpdate
    if not pending:
        raise PreventUpdate
    if trig == "bm-dup-go" and pending.get("action") == "duplicate":
        try:
            draft = BA.duplicate(root, pending["ref"], source)
        except (BA.WrongSource, FileNotFoundError) as exc:
            set_props("bm-dialog-body", {"children": html.P(str(exc), className="warning")})
            raise PreventUpdate from exc
        _close_dialog()
        set_props("build-menu", {"style": HIDDEN})
        return {"source": draft.source_id, "slug": draft.stored_slug}
    if trig == "bm-del-go" and pending.get("action") == "delete":
        try:
            BA.delete_build(root, pending["ref"], ref_of(build_folder(build_path)))
        except BA.DeleteRefused:
            set_props("bm-dialog-body", {"children": html.P(
                tx("This tab shows this Build: switch to another Build first."), className="warning")})
            raise PreventUpdate from None
        _close_dialog()
        _refresh(build_path, tx)
    raise PreventUpdate


def close_dialog(_n):
    if not _n:
        raise PreventUpdate
    return HIDDEN


def manage(_n, build_path, lang):
    if not _n or not editable():
        raise PreventUpdate
    tx = text(lang_of(lang))
    _dialog(tx("Manage Builds"), [html.P(tx("Every Build with its folder size and app-cache size."),
                                         className="mute small"),
                                  *tree_view(ref_of(build_folder(build_path)), tx, sizes=True)])
    raise PreventUpdate


# ----------------------------------------------------------------------------- Import data… (issue 33)


def import_dialog(_n, lang):
    if not _n or not editable():
        raise PreventUpdate
    tx = text(lang_of(lang))
    _dialog(tx("Import data"), [
        html.P(tx("One wide UTF-8 CSV: id, name, attributes (separated by ;), optional score, any numeric "
                  "columns. Making an Import is separate from making its first Build.")),
        dcc.Upload(html.Div(tx("Choose the CSV file…"), id="bm-imp-file-label"), id="bm-imp-file",
                   className="bm-upload", multiple=False),
        dcc.Upload(html.Div(tx("Optional: attributes.csv (id, name)…"), id="bm-imp-attrs-label"),
                   id="bm-imp-attrs", className="bm-upload", multiple=False),
        html.Label(tx("Filter column"), htmlFor="bm-imp-filter", className="l"),
        dcc.Dropdown(id="bm-imp-filter", options=[{"label": tx("none"), "value": ""}], value="", clearable=False),
        html.Div(html.Button(tx("Import"), id="bm-imp-go", className="btn primary"), className="row-inline"),
        html.Div(id="bm-imp-result"),
    ])
    raise PreventUpdate


def _decode(contents: str) -> bytes:
    return base64.b64decode(contents.split(",", 1)[1])


def import_columns(contents, filename, lang):
    """The filter dropdown: the uploaded file's non-reserved columns, plus "none"."""
    import csv

    from steamstudy.imports import RESERVED

    if not contents:
        raise PreventUpdate
    tx = text(lang_of(lang))
    try:
        head = next(csv.reader(io.StringIO(_decode(contents).decode("utf-8-sig"))), [])
    except (UnicodeDecodeError, ValueError):
        head = []
    columns = [h.strip() for h in head if h.strip() and h.strip() not in RESERVED]
    return ([{"label": tx("none"), "value": ""}, *[{"label": c, "value": c} for c in columns]], "",
            filename or tx("Choose the CSV file…"))


def import_go(_n, contents, filename, attrs, attrs_name, filter_field, build_path, lang):
    from steamstudy.imports import ERROR_CODES, WARNING_CODES, ImportRefused, make_import

    if not _n or not contents or not editable():
        raise PreventUpdate
    root = repo_root()
    assert root is not None
    tx = text(lang_of(lang))
    work = Path(tempfile.mkdtemp(prefix="steamstudy-import-"))
    try:
        path = work / Path(filename or "import.csv").name
        path.write_bytes(_decode(contents))
        attributes = None
        if attrs:
            attributes = work / "attrs" / Path(attrs_name or "attributes.csv").name
            attributes.parent.mkdir()
            attributes.write_bytes(_decode(attrs))
        try:
            folder = make_import(root, path, attributes_file=attributes, filter_field=filter_field or None)
        except ImportRefused as exc:
            if exc.existing is not None:
                return html.P(tx("Refused: the same file is already Import {import_id}.",
                                 import_id=Path(exc.existing).name), className="warning")
            rows = [html.Tr([html.Td(p.file), html.Td("" if p.row is None else p.row), html.Td(p.column),
                             html.Td(p.code, className="mono"), html.Td(p.value),
                             html.Td(tx(ERROR_CODES[p.code]) if p.code in ERROR_CODES else p.message)])
                    for p in exc.errors[:200]]
            head = html.Tr([html.Th(h) for h in (tx("File"), tx("Row"), tx("Column"), tx("Code"), tx("Value"),
                                                 tx("Message"))])
            where = (Path(exc.failed_folder).relative_to(root).as_posix() if exc.failed_folder else "")
            return [html.P(tx("Refused: {n} problems. Every one is listed in {path}.", n=len(exc.errors),
                              path=f"{where}/errors.csv"), className="warning"),
                    html.Table([head, *rows], className="bm-errors")]
    finally:
        shutil.rmtree(work, ignore_errors=True)
    import json

    meta = json.loads((folder / "import.json").read_text(encoding="utf-8"))
    warnings = [html.Li(f"{w.get('code')}: {tx(WARNING_CODES[w['code']]) if w.get('code') in WARNING_CODES else ''}")
                for w in meta.get("warnings", [])]
    _refresh(build_path, tx)
    return [html.P(tx("Made Import {import_id}. Its Import defaults row in the tree starts a draft.",
                      import_id=folder.name)), html.Ul(warnings) if warnings else None]


# ----------------------------------------------------------------------------- the Build run strip


def strip(_tick, lang):
    views = build_runs.runs()
    if not views:
        return HIDDEN, []
    tx = text(lang_of(lang))
    rows = []
    for v in views:
        if v["status"] in ("waiting", "running"):
            pct = min(99, round(100 * v["elapsed_s"] / max(v["estimate_s"], 1)))
            label = (tx("Building {name}: {stage}, {s} s of about {est} s", name=v["name"],
                        stage=v["stage"] or tx("starting"), s=v["elapsed_s"], est=v["estimate_s"])
                     if v["status"] == "running" else tx("{name} waits for the Build before it", name=v["name"]))
            rows.append(html.Div([html.Span(label), html.Progress(value=str(pct), max="100"),
                                  html.Button(tx("Cancel"), id={"type": "strip-cancel", "run": v["run_id"]},
                                              className="btn small")], className="strip-row"))
        elif v["status"] == "done":
            rows.append(html.Div([html.Span(tx("Built {name}.", name=v["name"])),
                                  html.Button(tx("Open it in this tab"), id={"type": "strip-open", "ref": v["ref"]},
                                              className="btn small primary"),
                                  html.Button("×", id={"type": "strip-dismiss", "run": v["run_id"]}, className="x")],
                                 className="strip-row"))
        else:
            text_ = (tx("The Build of {name} failed: {error}", name=v["name"], error=v["error"] or "")
                     if v["status"] == "failed" else tx("The Build of {name} was cancelled.", name=v["name"]))
            rows.append(html.Div([html.Span(text_, className="error" if v["status"] == "failed" else ""),
                                  html.Button(tx("Open the draft"), id={"type": "strip-draft", "source": v["source_id"],
                                                                        "slug": v["slug"]}, className="btn small"),
                                  html.Button("×", id={"type": "strip-dismiss", "run": v["run_id"]}, className="x")],
                                 className="strip-row"))
    return {"display": "block"}, rows


def strip_click(_o, _d, _c, _x, mode, dataset):
    target = _clicked()
    if target is None:
        raise PreventUpdate
    kind = target["type"]
    if kind == "strip-open":
        set_props("switch-to", {"data": build_url(target["ref"], mode, dataset)})
        for v in build_runs.runs():
            if v["ref"] == target["ref"]:
                build_runs.dismiss(v["run_id"])
    elif kind == "strip-draft":
        return {"source": target["source"], "slug": target["slug"]}
    elif kind == "strip-cancel":
        build_runs.cancel(int(target["run"]))
    elif kind == "strip-dismiss":
        build_runs.dismiss(int(target["run"]))
    return no_update


def register(app: dash.Dash) -> None:
    cb = app.callback
    cb(Output("build-menu", "style"), Output("bm-tree", "children"), Output("bm-footer", "children"),
       Input("build-menu-btn", "n_clicks"), State("build-path", "data"), State("lang", "data"),
       State("build-menu", "style"), prevent_initial_call=True)(toggle_menu)
    cb(Output("draft-open", "data", allow_duplicate=True),
       Input({"type": "bm-build", "ref": ALL}, "n_clicks"), Input({"type": "bm-root", "source": ALL}, "n_clicks"),
       Input({"type": "bm-draft", "source": ALL, "slug": ALL}, "n_clicks"),
       Input({"type": "bm-dup", "ref": ALL}, "n_clicks"), Input({"type": "bm-del", "ref": ALL}, "n_clicks"),
       Input({"type": "bm-discard", "source": ALL, "slug": ALL}, "n_clicks"),
       State("build-path", "data"), State("lang", "data"), State("mode", "value"), State("dataset", "value"),
       prevent_initial_call=True)(tree_click)
    cb(Output("draft-open", "data", allow_duplicate=True), Input("bm-dup-go", "n_clicks"),
       Input("bm-del-go", "n_clicks"), Input("bm-dup-open", "n_clicks"), State("bm-pending", "data"),
       State("bm-dup-source", "value"), State("build-path", "data"), State("lang", "data"),
       prevent_initial_call=True)(dialog_go)
    cb(Output("bm-dialog", "style", allow_duplicate=True), Input("bm-dialog-close", "n_clicks"),
       prevent_initial_call=True)(close_dialog)
    cb(Output("bm-dialog-title", "children", allow_duplicate=True), Input("bm-manage", "n_clicks"),
       State("build-path", "data"), State("lang", "data"), prevent_initial_call=True)(manage)
    cb(Output("bm-dialog-title", "children", allow_duplicate=True), Input("bm-import", "n_clicks"),
       State("lang", "data"), prevent_initial_call=True)(import_dialog)
    cb(Output("bm-imp-filter", "options"), Output("bm-imp-filter", "value"), Output("bm-imp-file-label", "children"),
       Input("bm-imp-file", "contents"), State("bm-imp-file", "filename"), State("lang", "data"),
       prevent_initial_call=True)(import_columns)
    cb(Output("bm-imp-result", "children"), Input("bm-imp-go", "n_clicks"), State("bm-imp-file", "contents"),
       State("bm-imp-file", "filename"), State("bm-imp-attrs", "contents"), State("bm-imp-attrs", "filename"),
       State("bm-imp-filter", "value"), State("build-path", "data"), State("lang", "data"),
       prevent_initial_call=True)(import_go)
    cb(Output("build-strip", "style"), Output("build-strip", "children"), Input("build-strip-tick", "n_intervals"),
       Input("lang", "data"))(strip)
    cb(Output("draft-open", "data", allow_duplicate=True),
       Input({"type": "strip-open", "ref": ALL}, "n_clicks"),
       Input({"type": "strip-draft", "source": ALL, "slug": ALL}, "n_clicks"),
       Input({"type": "strip-cancel", "run": ALL}, "n_clicks"), Input({"type": "strip-dismiss", "run": ALL}, "n_clicks"),
       State("mode", "value"), State("dataset", "value"), prevent_initial_call=True)(strip_click)

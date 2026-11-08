"""The draft dialog: a Build Draft's settings in six steps, saved on every edit (issues 29-31).

Start (name, description, where it started, its source, its last failure, Make lightweight Snapshot), Changes the
Top-N (datasets, Tag Depth, global rank limit, app types, the named rules), Curation (Manual Exclusions, Exclusion
Overrides, Manual Metadata Entries), Reports and analysis (Content Flags, Genre Tags, `analysis.toml`), Network
defaults (`network.toml`, with the grid-scaling warnings) and Review. A step's marker is green when it has changes
and red when it needs a fix. Build is only on Review.

The datasets, Tag Depth, the global rank limit and app types are form fields. The rule list, the curation lists, the
report settings and the network defaults are edited as the TOML text of their settings file (`toml_text`), which the
Build validates as it validates `config/` (a text that does not parse marks its step red and is not saved).

Every field is one component `{"type": "dd-field", "name": …}`; one callback reads them all, rebuilds the draft's
settings and saves the draft (`build_admin.save_draft`).
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import dash
from dash import ALL, Input, Output, State, ctx, dcc, html, no_update, set_props
from dash.exceptions import PreventUpdate

from steamstudy import build_admin as BA
from steamstudy import toml_text
from steamstudy.app import build_runs, preview
from steamstudy.app import help as H
from steamstudy.app.build_menu import HIDDEN, editable, repo_root
from steamstudy.app.relabel import msg
from steamstudy.i18n import Text, lang_of, text

STEP_TITLES = {"start": msg("Start"), "top_n": msg("Changes the Top-N"), "curation": msg("Curation"),
               "reports": msg("Reports and analysis"), "network": msg("Network defaults"), "review": msg("Review")}
# The files edited as TOML text, by step (Steam-only files are left out of an Import's draft).
TOML_FILES = {"top_n": ("exclusions",), "curation": ("manual_exclusions", "exclusion_overrides", "manual_metadata"),
              "reports": ("genres", "analysis"), "network": ("network",)}
STEAM_ONLY_FILES = ("manual_metadata",)
APP_TYPES = ("game", "dlc", "demo", "application", "tool", "music", "video", "series", "episode", "hardware", "mod")
# Fixed problem sentences of `build_admin.draft_problems`, shown in the Interface Language.
KNOWN_PROBLEMS = (msg("The draft needs a name"),
                  msg("The draft needs a description (it becomes its changelog entry)"),
                  msg("The Parameter Grid has no pairs: s starts above the largest g"))
# The Build's fixed rules, around the named ones (shown, not editable).
FIXED_BEFORE = (msg("Manual Exclusions"), msg("App types"), msg("No tags"))
FIXED_AFTER = (msg("Exclusion Overrides"),)


def _field(name: str) -> dict[str, str]:
    return {"type": "dd-field", "name": name}


def load(root: Path, ref: dict[str, str] | None) -> BA.Draft | None:
    if not ref:
        return None
    return next((d for d in BA.list_drafts(root, ref["source"]) if d.stored_slug == ref["slug"]), None)


def _is_import(root: Path, draft: BA.Draft) -> bool:
    from steamstudy.build.import_build import is_import

    return is_import(root, draft.source_id)


# ----------------------------------------------------------------------------- layout of one draft


def layout() -> html.Div:
    """The dialog's frame (placed once in the page); its body is rendered when a draft opens."""
    return html.Div([html.Div(id="dd-body", className="dd-frame")], id="draft-dialog", className="draft-dialog",
                    style=HIDDEN)


def _start(draft: BA.Draft, root: Path, tx: Text) -> list[Any]:
    from steamstudy.lightweight import light_path

    parent = BA.parent_name(root, draft.parent_build_id) if draft.parent_build_id else None
    started = (tx("the defaults") if not draft.parent_build_id
               else parent or tx("a deleted Build ({ref})", ref=draft.parent_build_id))
    imported = _is_import(root, draft)
    source = (tx("Import {id}", id=draft.source_id) if imported else tx("Snapshot {id}", id=draft.source_id))
    out: list[Any] = [
        html.Label(tx("Name"), htmlFor="dd-name", className="l"),
        dcc.Input(id=_field("name"), value=draft.name, debounce=0.6, className="wide"),
        html.Label(tx("Description (required: it becomes the Build's changelog entry)"), className="l"),
        dcc.Textarea(id=_field("description"), value=draft.description, className="wide dd-text short"),
        html.P([html.B(tx("Started from")), " ", started]),
        html.P([html.B(tx("Builds from")), " ", source]),
    ]
    if not imported and not light_path(root / "snapshots", draft.source_id).is_file():
        out.append(html.Div([
            html.P(tx("This Snapshot has only its raw form: the Eligible Pool is not previewed and a Build takes "
                      "about 99 s. A lightweight form makes both fast."), className="mute small"),
            html.Button(tx("Make lightweight Snapshot"), id="dd-lighten", className="btn")]))
    failure = draft.last_failure
    if failure:
        if failure.get("kind") == "parse_errors":
            text_ = tx("The last Build run failed: {n} pages did not parse; they are listed in {path}.",
                       n=failure.get("count"), path=failure.get("path"))
        else:
            text_ = tx("The last Build run failed: {error}", error=failure.get("message", ""))
        out.append(html.P(text_, className="warning"))
    return out


def _datasets(draft: BA.Draft, tx: Text, imported: bool) -> list[Any]:
    ds = draft.config.get("datasets", {})
    rows = []
    for i, d in enumerate(ds.get("dataset", [])):
        defining = d.get("defining_tag") or {}
        overall = d.get("key") == "overall"
        rows.append(html.Tr([
            html.Td(dcc.Input(id=_field(f"ds:{i}:key"), value=d.get("key", ""), debounce=0.6, disabled=overall,
                              className="mono")),
            html.Td(dcc.Input(id=_field(f"ds:{i}:label"), value=d.get("label", ""), debounce=0.6)),
            html.Td(dcc.Input(id=_field(f"ds:{i}:defining"), value=defining.get("name", ""), debounce=0.6,
                              disabled=overall, placeholder=tx("(none)") if overall else
                              (tx("an attribute") if imported else tx("a Steam tag")))),
            html.Td(dcc.Input(id=_field(f"ds:{i}:list_size"), value=d.get("list_size", 100), type="number", min=1,
                              debounce=0.6)),
            html.Td(html.Span(id={"type": "dd-pool", "key": d.get("key", "")}, className="dd-pool mute")),
            html.Td(html.Button("×", id={"type": "dd-ds-del", "i": i}, className="x", disabled=overall,
                                title=tx("Remove this dataset"))),
        ]))
    head = html.Tr([html.Th(h) for h in (tx("Dataset key"), tx("Label"), _term(tx("Defining tag"), "draft.defining_tag", tx),
                                         _term(tx("List Size"), "draft.list_size", tx),
                                         _term(tx("Eligible Pool"), "draft.eligible_pool", tx), "")])
    depth = ds.get("tag_depth", "all" if imported else 20)
    ex = draft.config.get("exclusions", {})
    out: list[Any] = [
        html.H4(tx("Datasets")),
        html.Table([head, *rows], className="dd-table"),
        html.Button(tx("Add a dataset"), id="dd-ds-add", className="btn small"),
        html.H4(_term(tx("Tags per game (Tag Depth)"), "draft.tag_depth", tx)),
        html.Div([dcc.Input(id=_field("tag_depth"), value=None if depth == "all" else depth, type="number", min=2,
                            debounce=0.6),
                  dcc.Checklist(id=_field("tag_depth_all"), options=[{"label": tx("all"), "value": "all"}],
                                value=["all"] if depth == "all" else [], inline=True)], className="row-inline"),
        html.H4(_term(tx("Global rank limit"), "draft.exclusions", tx)),
        dcc.Input(id=_field("global_rank_limit"), value=ex.get("global_rank_limit"), type="number", min=1, max=20,
                  debounce=0.6, placeholder=tx("none") if imported else ""),
    ]
    if not imported:
        out += [html.H4(tx("App types")),
                dcc.Checklist(id=_field("app_types"), options=[{"label": t, "value": t} for t in APP_TYPES],
                              value=list(ex.get("allowed_app_types", ["game"])), inline=True, className="chips")]
    out += [html.H4(_term(tx("Exclusion rules"), "draft.exclusions", tx)),
            html.P(tx("The fixed rules run first ({before}), then the named rules below in order, then {after}. "
                      "Edit the named rules ([[rule]]) and Content Flags ([[content_flag]]) here.",
                      before=", ".join(tx(t) for t in FIXED_BEFORE), after=", ".join(tx(t) for t in FIXED_AFTER)),
                   className="mute small")]
    return out


def _toml_box(draft: BA.Draft, file: str, tx: Text, bad: dict[str, str]) -> list[Any]:
    data = {k: v for k, v in draft.config.get(file, {}).items()
            if not (file == "exclusions" and k in ("global_rank_limit", "allowed_app_types"))}
    value = bad.get(file, toml_text.dumps(data))
    return [html.Label(html.Span(f"{file}.toml", className="mono"), className="l"),
            dcc.Textarea(id=_field(f"toml:{file}"), value=value, className="wide dd-text mono",
                         spellCheck=False)]


def _term(label: str, key: str, tx: Text) -> html.Span:
    """A setting's label with both help layers: hover shows its chapter-3 In short, a click opens the entry."""
    return html.Span(label, className="term", tabIndex="0", **H.attrs(key, tx))


def _help(step: str, tx: Text) -> html.Button:
    """The step's `?`: opens its section of chapter 7 (guide.PANEL_SECTIONS)."""
    return html.Button("?", id={"type": "help", "panel": f"draft-{step}"}, className="help dd-help",
                       title=tx("Open the User Guide section"))


def _step_body(step: str, draft: BA.Draft, root: Path, tx: Text, bad: dict[str, str]) -> list[Any]:
    return [_help(step, tx), *_step_content(step, draft, root, tx, bad)]


def _step_content(step: str, draft: BA.Draft, root: Path, tx: Text, bad: dict[str, str]) -> list[Any]:
    imported = _is_import(root, draft)
    if step == "start":
        return _start(draft, root, tx)
    out: list[Any] = []
    if step == "top_n":
        out += _datasets(draft, tx, imported)
    if step == "curation":
        out.append(html.P(tx("Each entry needs a reason and evidence, as in config/. The would-be Overall ranks of "
                             "excluded games are on Review."), className="mute small"))
    if step == "network":
        out.append(html.Div(id="dd-grid-warnings"))
    if step == "review":
        return [html.Div(id="dd-review")]
    for file in TOML_FILES.get(step, ()):
        if imported and file in STEAM_ONLY_FILES:
            continue
        out += _toml_box(draft, file, tx, bad)
    return out


def body(draft: BA.Draft, root: Path, step: str, tx: Text, bad: dict[str, str] | None = None) -> list[Any]:
    bad = bad or {}
    nav = [html.Button([html.Span(className="dd-mark", id={"type": "dd-mark", "step": s}), tx(STEP_TITLES[s])],
                       id={"type": "dd-step", "step": s}, className="dd-step" + (" on" if s == step else ""))
           for s in BA.STEPS]
    steps = [html.Div(_step_body(s, draft, root, tx, bad), id={"type": "dd-pane", "step": s},
                      className="dd-pane", style=None if s == step else HIDDEN) for s in BA.STEPS]
    return [
        html.Div([html.B(tx("Build Draft: {name}", name=draft.name), id="dd-title"),
                  html.Span(tx("Saved automatically; Close keeps the draft."), className="mute small"),
                  html.Span(tx("Previewing…"), id="dd-busy", className="mute small dd-busy", hidden=True),
                  html.Button(tx("Close"), id="dd-close", className="btn")], className="dd-head"),
        html.Div([html.Nav(nav, className="dd-nav"), html.Div(steps, className="dd-steps")], className="dd-main"),
        dcc.Store(id="dd-step-now", data=step), dcc.Store(id="dd-bad", data=bad), dcc.Store(id="dd-preview-key"),
    ]


# ----------------------------------------------------------------------------- reading the fields back


def _number(value: Any) -> int | None:
    try:
        return None if value in (None, "") else int(value)
    except (TypeError, ValueError):
        return None


def apply_fields(config: dict[str, Any], fields: dict[str, Any], imported: bool) -> tuple[dict[str, Any],
                                                                                         dict[str, str]]:
    """The draft's settings with the dialog's field values in, and the TOML texts that do not parse
    (file -> text; that file keeps its last saved value)."""
    out = copy.deepcopy(config)
    bad: dict[str, str] = {}
    ds = out.setdefault("datasets", {})
    rows = ds.setdefault("dataset", [])
    for name, value in fields.items():
        if not name.startswith("ds:"):
            continue
        _, i, key = name.split(":", 2)
        if int(i) >= len(rows):
            continue
        row = rows[int(i)]
        if key == "list_size":
            size = _number(value)
            if size is not None and size != row.get("list_size", 100):  # absent means 100
                row["list_size"] = size
        elif key == "defining":
            if row.get("key") == "overall":
                continue
            name_ = str(value or "").strip()
            if name_:
                row["defining_tag"] = {"name": name_} if imported else _steam_tag(name_, row.get("defining_tag"))
            else:
                row.pop("defining_tag", None)
        elif key in ("key", "label") and not (key == "key" and row.get("key") == "overall"):
            row[key] = str(value or "")
    if "tag_depth_all" in fields or "tag_depth" in fields:
        current = ds.get("tag_depth", "all" if imported else 20)  # absent means 20 (Steam) or all (an Import)
        wanted = "all" if fields.get("tag_depth_all") else _number(fields.get("tag_depth"))
        if wanted is not None and wanted != current:
            ds["tag_depth"] = wanted
    ex = out.setdefault("exclusions", {})
    if "global_rank_limit" in fields:
        limit = _number(fields["global_rank_limit"])
        if limit is None:
            ex.pop("global_rank_limit", None) if imported else None
        else:
            ex["global_rank_limit"] = limit
    if "app_types" in fields and not imported:
        types = list(fields["app_types"] or [])
        if sorted(types) != sorted(ex.get("allowed_app_types", ["game"])):
            ex["allowed_app_types"] = types
    # The rule list last, so that a rule renamed there renames the overrides read from their own text.
    tomls = sorted((n, v) for n, v in fields.items() if n.startswith("toml:"))
    for name, value in sorted(tomls, key=lambda nv: nv[0] == "toml:exclusions"):
        file = name.split(":", 1)[1]
        try:
            data = toml_text.loads(value or "")
        except ValueError:
            bad[file] = value
            continue
        if file == "exclusions":
            data = {**{k: ex[k] for k in ("global_rank_limit", "allowed_app_types") if k in ex}, **data}
            renamed = rule_renames(config.get("exclusions", {}), data)
            if renamed:
                rename_overrides(out, renamed)
        out[file] = data
    return out, bad


def rule_renames(before: dict[str, Any], after: dict[str, Any]) -> dict[str, str]:
    """Named rules renamed in place (old name -> new name): the same number of rules, and a rule whose name changed
    at the same position. A deleted rule is not a rename: its overrides stay and Review lists them as a problem."""
    old = [r.get("name") for r in before.get("rule", [])]
    new = [r.get("name") for r in after.get("rule", [])]
    if len(old) != len(new):
        return {}
    return {o: n for o, n in zip(old, new) if o != n and o and n and n not in old}


def rename_overrides(config: dict[str, Any], renamed: dict[str, str]) -> None:
    """Every Exclusion Override on a renamed rule names its new name."""
    for entry in config.get("exclusion_overrides", {}).get("override", []):
        if entry.get("rule") in renamed:
            entry["rule"] = renamed[entry["rule"]]


def _steam_tag(name: str, current: dict[str, Any] | None) -> dict[str, Any]:
    """A Steam defining tag by name: its id from the shipped vocabulary when the name is known there."""
    if current and current.get("name") == name and "id" in current:
        return current
    tag_id = _vocabulary().get(name.casefold())
    return {"id": tag_id, "name": name} if tag_id is not None else {"name": name}


def _vocabulary() -> dict[str, int]:
    """Steam tag names (case-folded) -> ids, from the shipped config's tags (all a defining tag may name here)."""
    from steamstudy.config import load_config

    root = repo_root()
    if root is None:
        return {}
    config = load_config(root / "config")
    found: dict[str, int] = {}

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            if isinstance(value.get("id"), int) and isinstance(value.get("name"), str):
                found[value["name"].casefold()] = value["id"]
            for v in value.values():
                walk(v)
        elif isinstance(value, list):
            for v in value:
                walk(v)
    walk(config.files)
    return found


# ----------------------------------------------------------------------------- Review and the markers


def _short(value: Any) -> str:
    text_ = json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value
    return text_ if len(text_) <= 80 else text_[:77] + "…"


def review(root: Path, draft: BA.Draft, tx: Text, bad: dict[str, str]) -> tuple[list[Any], dict[str, str], bool]:
    """Review's content, each step's marker ("green", "red" or ""), and whether Build may run. Also fills the
    Top-N step's pool cells and the preview key the Build button checks."""
    from steamstudy.config import BUILD_FILES

    base = BA.draft_base(root, draft, root / "config")
    changes = BA.changed_settings(base, draft.config)
    problems = BA.draft_problems(root, draft)
    problems += [BA.Problem(BA.STEP_OF_FILE.get(f, "top_n"), tx("{file}.toml does not parse; its last saved value "
                                                                 "is kept", file=f)) for f in bad]
    marks = {s: "" for s in BA.STEPS}
    for c in changes:
        marks[c.step] = "green"
    if draft.description.strip():
        marks["start"] = "green"
    for p in problems:
        marks[p.step] = "red"
    pv = preview.for_review(root, draft)
    if pv.error and pv.error_step:
        marks[pv.error_step] = "red"
    if pv.problems:
        marks["top_n"] = "red"
    marks["review"] = "red" if problems or pv.problems or pv.error else ""
    for d in draft.config.get("datasets", {}).get("dataset", []):
        set_props({"type": "dd-pool", "key": d.get("key", "")}, {"children": preview.pool_text(pv, d.get("key", ""), tx)})
    set_props("dd-preview-key", {"data": pv.key})
    rows = [html.Tr([html.Td(f"{c.file}.toml", className="mono"), html.Td(c.key, className="mono"),
                     html.Td(html.S(_short(c.before)) if c.before is not None else ""),
                     html.Td(_short(c.after) if c.after is not None else tx("(removed)")),
                     html.Td(html.Span(tx("Top-N"), className="bm-chip warn") if c.top_n else "")])
                for c in changes if c.file in BUILD_FILES]
    out: list[Any] = [html.H4(tx("Changed settings")),
                      html.Table(rows, className="dd-table") if rows else html.P(tx("No setting changed."),
                                                                                className="mute")]
    same = BA.identical_builds(root, draft.source_id, BA.draft_config_hash(draft))
    for b in same:
        note = tx(" (made with other software versions)") if b.versions_differ else ""
        out.append(html.P(tx("Identical settings to the Build {name}{note}. Building again is allowed.",
                             name=b.name, note=note), className="warning"))
    out += preview.review_block(pv, tx)
    if problems:
        out.append(html.H4(tx("Problems to fix")))
        out.append(html.Ul([html.Li([tx(p.message) if p.message in KNOWN_PROBLEMS else p.message, " ",
                                     html.Button(tx("Go to {step}", step=tx(STEP_TITLES[p.step])),
                                                 id={"type": "dd-step", "step": p.step, "from": "review"},
                                                 className="btn quiet small")]) for p in problems]))
    can_build = not problems and not bad and pv.buildable
    run = build_runs.running_draft(draft.source_id, draft.stored_slug or "")
    out.append(html.Div([html.Button(tx("Build"), id="dd-build", className="btn primary",
                                     disabled=not can_build or run is not None),
                         html.Span(tx("Building…") if run else "", className="mute small")], className="row-inline"))
    return out, marks, can_build


# ----------------------------------------------------------------------------- callbacks


def open_draft(ref, lang):
    """A draft opened (or closed): render its dialog on Start."""
    root = repo_root()
    if not ref or root is None or not editable():
        return HIDDEN, []
    draft = load(root, ref)
    if draft is None:
        return HIDDEN, []
    tx = text(lang_of(lang))
    preview.warm(root, draft.source_id)
    return {"display": "flex"}, body(draft, root, "start", tx)


def go_step(_clicks, ref, lang):
    target = ctx.triggered_id
    if not target or not ctx.triggered or not ctx.triggered[0].get("value"):
        raise PreventUpdate
    step = target["step"]
    set_props("dd-step-now", {"data": step})
    styles = [None if s == step else HIDDEN for s in BA.STEPS]
    classes = ["dd-step" + (" on" if s == step else "") for s in BA.STEPS]
    if step == "review":
        root = repo_root()
        draft = load(root, ref) if root else None
        if draft is not None:
            tx = text(lang_of(lang))
            content, marks, _ = review(root, draft, tx, {})
            set_props("dd-review", {"children": content})
    return styles, classes


def save_fields(values, ids, ref, lang):
    """Every edit: rebuild the draft's settings from the fields and save it; refresh the markers and Review."""
    root = repo_root()
    draft = load(root, ref) if root else None
    if draft is None:
        raise PreventUpdate
    tx = text(lang_of(lang))
    fields = {i["name"]: v for i, v in zip(ids, values)}
    imported = _is_import(root, draft)
    config, bad = apply_fields(draft.config, {k: v for k, v in fields.items() if k not in ("name", "description")},
                               imported)
    draft.config = config
    name_problem = None
    if "description" in fields:
        draft.description = str(fields["description"] or "")
    new_name = str(fields.get("name", draft.name) or "").strip()
    if new_name and new_name != draft.name:
        try:
            BA.check_name(root, draft.source_id, new_name, ignore_slug=draft.stored_slug)
            draft.name = new_name
        except BA.NameClash as exc:
            name_problem = str(exc)
    old_slug = draft.stored_slug
    BA.save_draft(root, draft)
    if draft.stored_slug != old_slug:  # renamed: the dialog follows its new file
        set_props("draft-open", {"data": {"source": draft.source_id, "slug": draft.stored_slug}})
    content, marks, _ = review(root, draft, tx, bad)
    if name_problem:
        marks["start"] = "red"
        content.insert(0, html.P(name_problem, className="warning"))
    set_props("dd-review", {"children": content})
    set_props("dd-grid-warnings", {"children": preview.grid_warnings(root, draft, tx)})
    set_props("dd-title", {"children": tx("Build Draft: {name}", name=draft.name)})
    overrides_text = fields.get("toml:exclusion_overrides")
    if overrides_text is not None and "exclusion_overrides" not in bad:
        current = toml_text.dumps(draft.config.get("exclusion_overrides", {}))
        if toml_text.loads(overrides_text) != draft.config.get("exclusion_overrides", {}):
            set_props(_field("toml:exclusion_overrides"), {"value": current})  # a renamed rule's overrides
    return [marks[s] and f"dd-mark {marks[s]}" or "dd-mark" for s in BA.STEPS], bad


def edit_datasets(_add, _del, ref, step, lang):
    """Add a dataset (a new key) or remove one (never `overall`); the dialog is drawn again on the same step."""
    root = repo_root()
    draft = load(root, ref) if root else None
    if draft is None or not ctx.triggered or not ctx.triggered[0].get("value"):
        raise PreventUpdate
    rows = draft.config.setdefault("datasets", {}).setdefault("dataset", [])
    if ctx.triggered_id == "dd-ds-add":
        keys = {d.get("key") for d in rows}
        n = 1
        while f"dataset_{n}" in keys:
            n += 1
        rows.append({"key": f"dataset_{n}", "label": f"Dataset {n}", "list_size": 100})
    else:
        i = int(ctx.triggered_id["i"])
        if 0 <= i < len(rows) and rows[i].get("key") != "overall":
            rows.pop(i)
    BA.save_draft(root, draft)
    return body(draft, root, step or "top_n", text(lang_of(lang)))


def build_now(_n, ref, shown_key):
    """Build, from Review only: the preview on screen must be the current settings' (never a stale one)."""
    root = repo_root()
    draft = load(root, ref) if root else None
    if not _n or draft is None:
        raise PreventUpdate
    pv = preview.for_review(root, draft)
    if not pv.not_previewed and pv.key != shown_key:
        raise PreventUpdate
    if BA.draft_problems(root, draft) or not pv.buildable:
        raise PreventUpdate
    build_runs.start(root, draft.source_id, draft.stored_slug or "", draft.name)
    return HIDDEN


def lighten_now(_n, ref):
    root = repo_root()
    draft = load(root, ref) if root else None
    if not _n or draft is None:
        raise PreventUpdate
    build_runs.start_lighten(root, draft.source_id)
    return True


def close(_n):
    if not _n:
        raise PreventUpdate
    return None


def register(app: dash.Dash) -> None:
    cb = app.callback
    cb(Output("draft-dialog", "style"), Output("dd-body", "children"), Input("draft-open", "data"),
       State("lang", "data"))(open_draft)
    cb(Output({"type": "dd-pane", "step": ALL}, "style"), Output({"type": "dd-step", "step": ALL}, "className"),
       Input({"type": "dd-step", "step": ALL}, "n_clicks"),
       Input({"type": "dd-step", "step": ALL, "from": ALL}, "n_clicks"),
       State("draft-open", "data"), State("lang", "data"), prevent_initial_call=True)(
        lambda a, b, ref, lang: go_step(a, ref, lang))
    cb(Output({"type": "dd-mark", "step": ALL}, "className"), Output("dd-bad", "data"),
       Input({"type": "dd-field", "name": ALL}, "value"), State({"type": "dd-field", "name": ALL}, "id"),
       State("draft-open", "data"), State("lang", "data"), prevent_initial_call=False,
       running=[(Output("dd-busy", "hidden"), False, True)])(save_fields)
    cb(Output("dd-body", "children", allow_duplicate=True), Input("dd-ds-add", "n_clicks"),
       Input({"type": "dd-ds-del", "i": ALL}, "n_clicks"), State("draft-open", "data"),
       State("dd-step-now", "data"), State("lang", "data"), prevent_initial_call=True)(edit_datasets)
    cb(Output("draft-dialog", "style", allow_duplicate=True), Input("dd-build", "n_clicks"),
       State("draft-open", "data"), State("dd-preview-key", "data"), prevent_initial_call=True)(build_now)
    cb(Output("dd-lighten", "disabled"), Input("dd-lighten", "n_clicks"), State("draft-open", "data"),
       prevent_initial_call=True)(lighten_now)
    cb(Output("draft-open", "data", allow_duplicate=True), Input("dd-close", "n_clicks"),
       prevent_initial_call=True)(close)
    _ = no_update

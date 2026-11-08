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
from steamstudy import pool_preview as PP
from steamstudy import toml_text
from steamstudy.app import build_runs, preview
from steamstudy.app import help as H
from steamstudy.app.build_menu import HIDDEN, editable, repo_root
from steamstudy.app.relabel import msg
from steamstudy.i18n import Text, lang_of, text

STEP_TITLES = {"start": msg("Start"), "top_n": msg("Changes the Top-N"), "curation": msg("Curation"),
               "reports": msg("Reports and analysis"), "network": msg("Network defaults"), "review": msg("Review")}
# The files edited as TOML text, by step (Steam-only files are left out of an Import's draft). The named rules
# are edited one card per rule on Top-N; `content_flags` is the `content_flag` part of `exclusions.toml`, edited on
# Reports and analysis; `exclusions` shows only what is left of that file (nothing, in today's shape).
TOML_FILES = {"top_n": ("exclusions",), "curation": ("manual_exclusions", "exclusion_overrides", "manual_metadata"),
              "reports": ("content_flags", "genres", "analysis"), "network": ("network",)}
STEAM_ONLY_FILES = ("manual_metadata",)
# Keys a TOML box leaves out: edited elsewhere in the dialog, or (an Import) Steam-only.
EDITED_ELSEWHERE = {"exclusions": ("global_rank_limit", "allowed_app_types", "rule", "content_flag")}
STEAM_ONLY_KEYS = {"analysis": ("release_month_check",)}
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
    from steamstudy.imports import is_import

    return is_import(root, draft.source_id)


# ----------------------------------------------------------------------------- layout of one draft


def layout() -> html.Div:
    """The dialog's frame (placed once in the page); its body is rendered when a draft opens."""
    return html.Div([html.Div(id="dd-body", className="dd-frame")], id="draft-dialog", className="draft-dialog",
                    style=HIDDEN)


def _start(draft: BA.Draft, root: Path, tx: Text) -> list[Any]:
    from steamstudy.builds import light_path

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


def _tag_picker(i: int, current: str | None, names: list[str], overall: bool, imported: bool,
                tx: Text) -> dcc.Dropdown:
    """A dataset's defining tag, chosen from the source's vocabulary (GetTagList, or the Import's attributes). A name
    from an older config that is not in it stays shown, so that the Build's own check reports it."""
    options = [{"label": n, "value": n} for n in names]
    if current and current not in names:
        options.insert(0, {"label": tx("{name} (not in this source)", name=current), "value": current})
    return dcc.Dropdown(id=_field(f"ds:{i}:defining"), options=options, value=current or None, disabled=overall,
                        clearable=True, searchable=True, className="dd-tag",
                        placeholder=tx("(none)") if overall else (tx("an attribute") if imported else tx("a Steam tag")))


def _datasets(draft: BA.Draft, root: Path, tx: Text, imported: bool, bad: dict[str, str]) -> list[Any]:
    ds = draft.config.get("datasets", {})
    names = sorted(preview.vocabulary(root, draft.source_id).ids, key=str.casefold)
    rows = []
    for i, d in enumerate(ds.get("dataset", [])):
        defining = d.get("defining_tag") or {}
        overall = d.get("key") == "overall"
        rows.append(html.Tr([
            html.Td(dcc.Input(id=_field(f"ds:{i}:key"), value=d.get("key", ""), debounce=0.6, disabled=overall,
                              className="mono")),
            html.Td(dcc.Input(id=_field(f"ds:{i}:label"), value=d.get("label", ""), debounce=0.6)),
            html.Td(_tag_picker(i, defining.get("name"), names, overall, imported, tx)),
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
        html.Div(id="dd-pool-note"),
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
    out += [html.H4(_term(tx("Exclusion rules"), "draft.exclusions", tx)), *_rules(draft, tx, bad)]
    return out


def _rules(draft: BA.Draft, tx: Text, bad: dict[str, str]) -> list[Any]:
    """The named rules in order, one card each (name, up, down, delete, and the rule's signals as TOML), between
    the fixed rules, which are shown but not editable."""
    rules = draft.config.get("exclusions", {}).get("rule", [])
    cards = []
    for i, rule in enumerate(rules):
        body = {k: v for k, v in rule.items() if k != "name"}
        cards.append(html.Div([
            html.Div([html.Span(f"{i + 1}.", className="mute"),
                      dcc.Input(id=_field(f"rule:{i}:name"), value=rule.get("name", ""), debounce=0.6,
                                className="mono", placeholder=tx("rule name")),
                      html.Button("↑", id={"type": "dd-rule-move", "i": i, "d": -1}, className="btn quiet small",
                                  disabled=i == 0, title=tx("Run this rule earlier")),
                      html.Button("↓", id={"type": "dd-rule-move", "i": i, "d": 1}, className="btn quiet small",
                                  disabled=i == len(rules) - 1, title=tx("Run this rule later")),
                      html.Button("×", id={"type": "dd-rule-del", "i": i}, className="x",
                                  title=tx("Delete this rule"))], className="row-inline"),
            dcc.Textarea(id=_field(f"rule:{i}:body"), value=bad.get(f"rule:{i}", toml_text.dumps(body)),
                         className="wide dd-text short mono", spellCheck=False),
        ], className="dd-rule"))
    return [html.P(tx("The fixed rules run first, then the named rules in this order, then the Exclusion Overrides. "
                      "Order decides each excluded game's primary reason. Renaming a rule renames its overrides."),
                   className="mute small"),
            _fixed_rules(FIXED_BEFORE, tx), *cards, _fixed_rules(FIXED_AFTER, tx),
            html.Div(id="dd-rule-confirm"),
            html.Button(tx("Add a rule"), id="dd-rule-add", className="btn small")]


def _fixed_rules(names: tuple[str, ...], tx: Text) -> html.Div:
    return html.Div([html.Span(tx("fixed"), className="bm-chip"), " ", ", ".join(tx(t) for t in names)],
                    className="dd-rule fixed mute small")


def _box_data(config: dict[str, Any], file: str, imported: bool) -> dict[str, Any]:
    """What a TOML box shows of a settings file."""
    if file == "content_flags":
        return {"content_flag": config.get("exclusions", {}).get("content_flag", [])}
    hidden = (*EDITED_ELSEWHERE.get(file, ()), *(STEAM_ONLY_KEYS.get(file, ()) if imported else ()))
    return {k: v for k, v in config.get(file, {}).items() if k not in hidden}


def _toml_box(draft: BA.Draft, file: str, tx: Text, bad: dict[str, str], imported: bool) -> list[Any]:
    data = _box_data(draft.config, file, imported)
    if file == "exclusions" and not data and file not in bad:
        return []  # today's shape: every key has its own editor
    label = "exclusions.toml [[content_flag]]" if file == "content_flags" else f"{file}.toml"
    out: list[Any] = [html.Label(html.Span(label, className="mono"), className="l")]
    if file == "content_flags":
        out.append(html.P(tx("Content Flags mark games for the reports; they never exclude one."),
                          className="mute small"))
    return out + [dcc.Textarea(id=_field(f"toml:{file}"), value=bad.get(file, toml_text.dumps(data)),
                               className="wide dd-text mono", spellCheck=False)]


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
        out += _datasets(draft, root, tx, imported, bad)
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
        out += _toml_box(draft, file, tx, bad, imported)
    return out


def body(draft: BA.Draft, root: Path, step: str, tx: Text, bad: dict[str, str] | None = None,
         busy: str | None = None) -> list[Any]:
    """The dialog of one draft on `step`. `busy` is the label shown while the preview computes ("Loading
    Snapshot…" the first time the source is read; "Previewing…" after)."""
    bad = bad or {}
    nav = [html.Button([html.Span(className="dd-mark", id={"type": "dd-mark", "step": s}), tx(STEP_TITLES[s])],
                       id={"type": "dd-step", "step": s}, className="dd-step" + (" on" if s == step else ""))
           for s in BA.STEPS]
    steps = [html.Div(_step_body(s, draft, root, tx, bad), id={"type": "dd-pane", "step": s},
                      className="dd-pane", style=None if s == step else HIDDEN) for s in BA.STEPS]
    return [
        html.Div([html.B(tx("Build Draft: {name}", name=draft.name), id="dd-title"),
                  html.Span(tx("Saved automatically; Close keeps the draft."), className="mute small"),
                  html.Span([html.Span(className="dd-spinner"), busy or tx("Previewing…")], id="dd-busy",
                            className="mute small dd-busy", hidden=True),
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


def apply_fields(config: dict[str, Any], fields: dict[str, Any], imported: bool,
                 vocabulary: PP.Vocabulary | None = None) -> tuple[dict[str, Any], dict[str, str]]:
    """The draft's settings with the dialog's field values in, and the TOML texts that do not parse
    (box -> text; that box keeps its last saved value). `vocabulary` resolves a defining tag's id."""
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
            if row.get("key") != "overall":
                _set_defining(row, str(value or "").strip(), vocabulary)
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
    for name, value in sorted(fields.items()):
        if not name.startswith("toml:"):
            continue
        file = name.split(":", 1)[1]
        try:
            data = toml_text.loads(value or "")
        except ValueError:
            bad[file] = value
            continue
        if file == "content_flags":
            ex["content_flag"] = data.get("content_flag", [])
            continue
        kept = (*EDITED_ELSEWHERE.get(file, ()), *(STEAM_ONLY_KEYS.get(file, ()) if imported else ()))
        out[file] = {**{k: v for k, v in out.get(file, {}).items() if k in kept}, **data}
    # The rule cards last, so that a renamed rule renames the overrides just read from their own box.
    renamed = _apply_rules(out.setdefault("exclusions", {}), fields, bad)
    if renamed:
        rename_overrides(out, renamed)
    return out, bad


def _apply_rules(ex: dict[str, Any], fields: dict[str, Any], bad: dict[str, str]) -> dict[str, str]:
    """The rule cards' names and bodies into `ex["rule"]`; returns the renames (old name -> new name)."""
    rules = ex.get("rule", [])
    renamed: dict[str, str] = {}
    old_names = [r.get("name") for r in rules]
    for i, rule in enumerate(rules):
        body_text = fields.get(f"rule:{i}:body")
        if body_text is not None:
            try:
                body = toml_text.loads(body_text or "")
            except ValueError:
                bad[f"rule:{i}"] = body_text
            else:
                rules[i] = rule = {"name": rule.get("name", ""), **{k: v for k, v in body.items() if k != "name"}}
        new = str(fields.get(f"rule:{i}:name", rule.get("name", "")) or "").strip()
        old = rule.get("name", "")
        if new != old:
            rule["name"] = new
            if old and new and new not in old_names:
                renamed[old] = new
    return renamed


def _set_defining(row: dict[str, Any], name: str, vocabulary: PP.Vocabulary | None) -> None:
    """A dataset's defining tag by name: `{ id, name }` from the source's vocabulary (an Import with numbered
    attributes: `{ name }`). A name the vocabulary lacks is kept as it was, for the Build's check to report."""
    if not name:
        row.pop("defining_tag", None)
        return
    current = row.get("defining_tag")
    ref = vocabulary.ref(name) if vocabulary is not None else None
    if ref is not None:
        row["defining_tag"] = ref
    elif not (current and current.get("name") == name):
        row["defining_tag"] = {"name": name}


def rename_overrides(config: dict[str, Any], renamed: dict[str, str]) -> None:
    """Every Exclusion Override on a renamed rule names its new name."""
    for entry in config.get("exclusion_overrides", {}).get("override", []):
        if entry.get("rule") in renamed:
            entry["rule"] = renamed[entry["rule"]]


def overrides_of(config: dict[str, Any], rule: str) -> list[dict[str, Any]]:
    return [e for e in config.get("exclusion_overrides", {}).get("override", []) if e.get("rule") == rule]


def move_rule(config: dict[str, Any], i: int, step: int) -> None:
    rules = config.setdefault("exclusions", {}).setdefault("rule", [])
    j = i + step
    if 0 <= i < len(rules) and 0 <= j < len(rules):
        rules[i], rules[j] = rules[j], rules[i]


def delete_rule(config: dict[str, Any], i: int, *, drop_overrides: bool) -> None:
    """Remove the i-th named rule; with `drop_overrides`, its Exclusion Overrides too (else they stay, and fail the
    Build's check on Curation)."""
    rules = config.setdefault("exclusions", {}).setdefault("rule", [])
    if not 0 <= i < len(rules):
        return
    name = rules.pop(i).get("name")
    if drop_overrides:
        table = config.setdefault("exclusion_overrides", {})
        table["override"] = [e for e in table.get("override", []) if e.get("rule") != name]


def add_rule(config: dict[str, Any]) -> None:
    rules = config.setdefault("exclusions", {}).setdefault("rule", [])
    names = {r.get("name") for r in rules}
    n = 1
    while f"rule_{n}" in names:
        n += 1
    rules.append({"name": f"rule_{n}", "label": f"Rule {n}", "tags": []})


def add_overrides(config: dict[str, Any], appid: int, name: str, rules: list[str], today: str) -> int:
    """The Override shortcut: an Exclusion Override of each rule that excludes the game (and has none yet), with
    an empty reason and evidence for the researcher to fill in on Curation. Returns how many were added."""
    table = config.setdefault("exclusion_overrides", {})
    entries = table.setdefault("override", [])
    have = {(e.get("appid"), e.get("rule")) for e in entries}
    added = 0
    for rule in rules:
        if (appid, rule) not in have:
            entries.append({"appid": appid, "name": name, "rule": rule, "reason": "", "evidence": [], "added": today})
            added += 1
    return added


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
    problems += [BA.Problem(*_bad_problem(f, tx)) for f in bad]
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
    set_props("dd-pool-note", {"children": _cannot_compute(pv, tx)})
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
    out += _cannot_compute(pv, tx)
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


def _go_to(step: str, tx: Text) -> html.Button:
    return html.Button(tx("Go to {step}", step=tx(STEP_TITLES[step])), id={"type": "dd-step", "step": step,
                                                                           "from": "review"},
                       className="btn quiet small")


def _cannot_compute(pv: PP.PoolPreview, tx: Text) -> list[Any]:
    """Why the preview's numbers read "—", with a link to the step marked red."""
    if not pv.error:
        return []
    out: list[Any] = [tx("— Cannot preview: {reason}", reason=pv.error)]
    if pv.error_step:
        out += [" ", _go_to(pv.error_step, tx)]
    return [html.P(out, className="warning small")]


def _bad_problem(box: str, tx: Text) -> tuple[str, str]:
    """(step, message) for a TOML box that does not parse."""
    if box.startswith("rule:"):
        return "top_n", tx("Rule {n} does not parse; its last saved value is kept", n=int(box.split(":")[1]) + 1)
    label = "exclusions.toml [[content_flag]]" if box == "content_flags" else f"{box}.toml"
    return BA.step_of_box(box), tx("{file} does not parse; its last saved value is kept", file=label)


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
    busy = None
    if not preview.is_loaded(root, draft.source_id) and preview.previewable(root, draft.source_id):
        busy = tx("Loading Import…") if _is_import(root, draft) else tx("Loading Snapshot…")
    preview.warm(root, draft.source_id)
    return {"display": "flex"}, body(draft, root, "start", tx, busy=busy)


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
                               imported, preview.vocabulary(root, draft.source_id))
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
    set_props("dd-busy", {"children": [html.Span(className="dd-spinner"), tx("Previewing…")]})
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


def edit_rules(_move, _del, _drop, _add, _cancel, ref, step, lang):
    """The rule cards' buttons: move a rule up or down, add one, delete one (asking first when it has Exclusion
    Overrides: they go with it, or the delete is cancelled). The dialog is drawn again on the same step."""
    root = repo_root()
    draft = load(root, ref) if root else None
    if draft is None or not ctx.triggered or not ctx.triggered[0].get("value"):
        raise PreventUpdate
    tx = text(lang_of(lang))
    trig = ctx.triggered_id
    if isinstance(trig, dict) and trig["type"] == "dd-rule-cancel":
        set_props("dd-rule-confirm", {"children": []})
        raise PreventUpdate
    if trig == "dd-rule-add":
        add_rule(draft.config)
    elif trig["type"] == "dd-rule-move":
        move_rule(draft.config, int(trig["i"]), int(trig["d"]))
    elif trig["type"] == "dd-rule-del":
        i = int(trig["i"])
        rules = draft.config.get("exclusions", {}).get("rule", [])
        name = rules[i].get("name", "") if 0 <= i < len(rules) else ""
        n = len(overrides_of(draft.config, name)) if name else 0
        if n:
            set_props("dd-rule-confirm", {"children": html.Div([
                html.P(tx.n(n, one="The rule {name} has {n} Exclusion Override. Delete it too?",
                            other="The rule {name} has {n} Exclusion Overrides. Delete them too?", name=name),
                       className="warning"),
                html.Button(tx("Delete the rule and its overrides"), id={"type": "dd-rule-drop", "i": i},
                            className="btn small danger"),
                html.Button(tx("Cancel"), id={"type": "dd-rule-cancel", "i": i}, className="btn small")],
                className="row-inline")})
            raise PreventUpdate
        delete_rule(draft.config, i, drop_overrides=False)
    elif trig["type"] == "dd-rule-drop":
        delete_rule(draft.config, int(trig["i"]), drop_overrides=True)
    BA.save_draft(root, draft)
    return body(draft, root, step or "top_n", tx)


def keep_game(_clicks, ref, lang):
    """The Override shortcut on Review: an Exclusion Override for each rule that excludes the game, then Curation,
    where its reason and evidence are filled in."""
    import datetime as dt

    root = repo_root()
    draft = load(root, ref) if root else None
    if draft is None or not ctx.triggered or not ctx.triggered[0].get("value"):
        raise PreventUpdate
    trig = ctx.triggered_id
    add_overrides(draft.config, int(trig["appid"]), str(trig["name"]), str(trig["rules"]).split(","),
                  dt.date.today().isoformat())
    BA.save_draft(root, draft)
    set_props("dd-step-now", {"data": "curation"})
    return body(draft, root, "curation", text(lang_of(lang)))


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
       running=[(Output("dd-busy", "hidden"), False, True),
                (Output("dd-body", "className"), "dd-frame computing", "dd-frame")])(save_fields)
    cb(Output("dd-body", "children", allow_duplicate=True), Input("dd-ds-add", "n_clicks"),
       Input({"type": "dd-ds-del", "i": ALL}, "n_clicks"), State("draft-open", "data"),
       State("dd-step-now", "data"), State("lang", "data"), prevent_initial_call=True)(edit_datasets)
    cb(Output("dd-body", "children", allow_duplicate=True), Input({"type": "dd-rule-move", "i": ALL, "d": ALL}, "n_clicks"),
       Input({"type": "dd-rule-del", "i": ALL}, "n_clicks"), Input({"type": "dd-rule-drop", "i": ALL}, "n_clicks"),
       Input("dd-rule-add", "n_clicks"), Input({"type": "dd-rule-cancel", "i": ALL}, "n_clicks"),
       State("draft-open", "data"),
       State("dd-step-now", "data"), State("lang", "data"), prevent_initial_call=True)(edit_rules)
    cb(Output("dd-body", "children", allow_duplicate=True),
       Input({"type": "dd-keep", "appid": ALL, "name": ALL, "rules": ALL}, "n_clicks"), State("draft-open", "data"),
       State("lang", "data"), prevent_initial_call=True)(keep_game)
    cb(Output("draft-dialog", "style", allow_duplicate=True), Input("dd-build", "n_clicks"),
       State("draft-open", "data"), State("dd-preview-key", "data"), prevent_initial_call=True)(build_now)
    cb(Output("dd-lighten", "disabled"), Input("dd-lighten", "n_clicks"), State("draft-open", "data"),
       prevent_initial_call=True)(lighten_now)
    cb(Output("draft-open", "data", allow_duplicate=True), Input("dd-close", "n_clicks"),
       prevent_initial_call=True)(close)
    _ = no_update

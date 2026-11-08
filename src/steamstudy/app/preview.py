"""The draft dialog's Eligible Pool preview and grid warnings (issues 31-32), over `pool_preview`.

At most one source's records are loaded per app process: loaded the first time a draft dialog opens for that source
("Loading Snapshot…", about 2.8 s), swapped when a dialog for another source opens, and dropped when the source
changes (its lightweight file or the Import's sha256). The preview runs in the app process, never as a server job.
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

from dash import html

from steamstudy import pool_preview as PP
from steamstudy.build_admin import Draft
from steamstudy.i18n import Text

_LOCK = threading.Lock()
_LOADED: tuple[Path, str, str, PP.Records] | None = None  # (root, source_id, version, records)


def records(root: Path, source_id: str) -> PP.Records | None:
    """The source's records, loading (or swapping in) them when the cached ones are not this source's current form."""
    global _LOADED
    found = PP.source_version(root, source_id)
    if found is None:
        return None
    with _LOCK:
        if _LOADED and (_LOADED[0], _LOADED[1], _LOADED[2]) == (root, source_id, found[1]):
            return _LOADED[3]
        loaded = PP.load_records(root, source_id)
        _LOADED = (root, source_id, found[1], loaded) if loaded is not None else None
        return loaded


def warm(root: Path, source_id: str) -> None:
    """Load the source in the background when a draft dialog opens, so the first preview does not wait for it."""
    threading.Thread(target=records, args=(root, source_id), daemon=True).start()


def _comparison(root: Path, draft: Draft) -> tuple[list[int] | None, str | None]:
    """The Overall list entering and leaving compare with: the draft's source Build, else the source's latest."""
    from steamstudy.app.loader import load_build
    from steamstudy.builds import builds_dir

    candidates = []
    if draft.parent_build_id:
        candidates.append(builds_dir(root) / draft.parent_build_id)
    pointer = builds_dir(root) / draft.source_id / "latest"
    if pointer.is_file():
        candidates.append(builds_dir(root) / draft.source_id / pointer.read_text(encoding="utf-8").strip())
    for path in candidates:
        if (path / "datasets" / "build.json").is_file():
            try:
                ctx = load_build(path)
                games = sorted(ctx.read(ctx.datasets[0].key).games(), key=lambda g: g.rank)
                return [g.appid for g in games], ctx.build_json.get("name") or ctx.build_id
            except (OSError, ValueError, KeyError):
                continue
    return None, None


def for_review(root: Path, draft: Draft) -> PP.PoolPreview:
    loaded = records(root, draft.source_id)
    if loaded is None:
        from steamstudy.build.import_build import is_import

        missing = not is_import(root, draft.source_id) and not (root / "snapshots" / draft.source_id).is_dir()
        return PP.PoolPreview("", not_previewed=not missing,
                              error="the Snapshot is missing" if missing else None,
                              error_step="start" if missing else None)
    compare, name = _comparison(root, draft)
    return PP.preview(loaded, draft.config, compare=compare, compared_with=name)


def pool_text(pv: PP.PoolPreview, key: str, tx: Text) -> str:
    if pv.not_previewed:
        return tx("Not previewed")
    if pv.error:
        return "—"
    if key not in pv.pools:
        return ""
    eligible, size = pv.pools[key]
    return tx("{n} eligible", n=eligible) + (" ⚠" if eligible < size else "")


def review_block(pv: PP.PoolPreview, tx: Text) -> list[Any]:
    out: list[Any] = [html.H4(tx("Eligible Pools"))]
    if pv.not_previewed:
        return out + [html.P(tx("Not previewed: this Snapshot has no lightweight form. The Build checks each List "
                                "Size itself (about 99 s from raw)."), className="mute")]
    if pv.error:
        return out + [html.P(tx("— Cannot preview: {reason}", reason=pv.error), className="warning")]
    out.append(html.Ul([html.Li(tx("{key}: {n} eligible, List Size {size}", key=k, n=n, size=size))
                        for k, (n, size) in pv.pools.items()]))
    for line in pv.short:
        out.append(html.P(line, className="warning" if pv.test else "error"))
    if pv.compared_with is not None:
        out.append(html.P(tx("Compared with {name}: {a} games enter Overall and {b} leave it.", name=pv.compared_with,
                             a=len(pv.entering), b=len(pv.leaving))))
        if pv.entering:
            out.append(html.P([html.B(tx("Enter: ")), ", ".join(n for _, n in pv.entering[:30])], className="small"))
        if pv.leaving:
            out.append(html.P([html.B(tx("Leave: ")), ", ".join(n for _, n in pv.leaving[:30])], className="small"))
    if pv.would_be:
        out.append(html.H4(tx("Excluded games that would rank in Overall")))
        out.append(html.Table([html.Tr([html.Th(tx("Rank")), html.Th(tx("Name")), html.Th(tx("Rule")),
                                        html.Th(tx("ID"))])] +
                              [html.Tr([html.Td(rank), html.Td(name), html.Td(", ".join(rules), className="mono"),
                                        html.Td(appid, className="mono")]) for appid, name, rank, rules in
                               pv.would_be[:50]], className="dd-table"))
        out.append(html.P(tx("To keep one, add an Exclusion Override for its rule on Curation."),
                          className="mute small"))
    return out


def grid_warnings(root: Path, draft: Draft, tx: Text) -> list[Any]:
    """The grid-scaling warnings per dataset (never a refusal), and the no-pairs grid (a red problem)."""
    lines: list[Any] = []
    network = draft.config.get("network", {})
    ps = network.get("parameter_selection", {})
    analysis = draft.config.get("analysis", {})
    g_range, s_range = ps.get("g_range", [3, 20]), ps.get("s_range", [2, 12])
    for d in draft.config.get("datasets", {}).get("dataset", []):
        n, label = int(d.get("list_size", 100)), d.get("label", d.get("key"))
        if g_range and g_range[-1] > n:
            lines.append(tx("{dataset} (N = {n}): the Parameter Grid's largest g ({g}) is above N.", dataset=label,
                            n=n, g=g_range[-1]))
        for key, short in (("min_games_per_tag", "g"), ("min_shared_games", "s")):
            if int(network.get(key, 0)) > n:
                lines.append(tx("{dataset} (N = {n}): the default {name} ({value}) is above N.", dataset=label, n=n,
                                name=short, value=network.get(key)))
        if int(analysis.get("min_support", 0)) > n:
            lines.append(tx("{dataset} (N = {n}): min_support ({value}) is above N.", dataset=label, n=n,
                            value=analysis.get("min_support")))
    out: list[Any] = [html.P(line, className="warning") for line in lines]
    if s_range and g_range and s_range[0] > g_range[-1]:
        out.append(html.P(tx("The Parameter Grid has no pairs: s starts above the largest g"), className="error"))
    return out


def no_pairs(draft: Draft) -> bool:
    ps = draft.config.get("network", {}).get("parameter_selection", {})
    g_range, s_range = ps.get("g_range", [3, 20]), ps.get("s_range", [2, 12])
    return bool(s_range and g_range and s_range[0] > g_range[-1])

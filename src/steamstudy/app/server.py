"""Create and run the Tag Network app: offline, `127.0.0.1` only, `debug=False`.

Each tab names its Build in the URL, `/build/<source_id>/<build_id>` (Dash Pages, ADR 0006): the page is built from
that Build when the tab loads it, and `/` redirects to the startup Build. The ids are resolved under the builds root
of the startup Build; a URL whose Build is gone gets the missing-Build page. The background job store is one
temporary folder per app process, removed at exit, never inside a Build (an open `cache.db` would block deleting it
on Windows).
"""

from __future__ import annotations

import atexit
import shutil
import tempfile
import threading
import webbrowser
from pathlib import Path
from typing import Any

import dash
import diskcache
import flask
from dash import DiskcacheManager, dcc, html

from steamstudy.app import build_menu, callbacks, draft_dialog, pending
from steamstudy.app.layout import build_layout
from steamstudy.app.loader import builds_root, is_ref, load_build, resolve_ref, set_builds_root
from steamstudy.app.relabel import msg
from steamstudy.i18n import COOKIE, DEFAULT, lang_of, text

HOST = "127.0.0.1"
PAGE_PATH = "/build/<source_id>/<build_id>"


def served_lang() -> str:
    """The Interface Language of the page being served: the browser's cookie, English without one."""
    return lang_of(flask.request.cookies.get(COOKIE)) if flask.has_request_context() else DEFAULT


def build_url(ref: str) -> str:
    return f"/build/{ref}"


def latest_ref(root: Path) -> str | None:
    """The root `latest` pointer's Build (`<source_id>/<build_id>`), when it names one that exists."""
    pointer = root / "latest"
    if not pointer.is_file():
        return None
    ref = pointer.read_text(encoding="utf-8").strip().replace("\\", "/")  # written on Windows with a backslash
    try:
        resolve_ref(ref, root)
    except FileNotFoundError:
        return None
    return ref


def missing_layout(lang: str, startup: str) -> html.Div:
    """"This Build no longer exists", with a link to the latest Build (else the startup one)."""
    tx = text(lang)
    root = builds_root()
    target = (latest_ref(root) if root else None) or startup
    return html.Div([html.H2(tx(msg("This Build no longer exists"))),
                     html.P(dcc.Link(tx(msg("Open the latest Build")), href=build_url(target)))],
                    className="missing-build", id="missing-build")


def page_layout(startup: str) -> Any:
    def layout(source_id: str | None = None, build_id: str | None = None, mode: str | None = None,
               dataset: str | None = None, open: str | None = None, **_query: Any) -> Any:  # noqa: A002
        lang = served_lang()
        ref = f"{source_id}/{build_id}"
        if not is_ref(ref):
            return missing_layout(lang, startup)
        try:
            ctx = load_build(resolve_ref(ref))
        except (FileNotFoundError, ValueError):
            return missing_layout(lang, startup)
        return build_layout(ctx, lang, mode=mode or "workbench", dataset=dataset, open_token=open)
    return layout


def job_store() -> Path:
    """One temporary folder per app process for the background job store, removed at exit."""
    folder = Path(tempfile.mkdtemp(prefix="steamstudy-jobs-"))
    atexit.register(shutil.rmtree, folder, ignore_errors=True)
    return folder


def create_app(build_path: str | Path) -> dash.Dash:
    ctx = load_build(build_path)
    path = ctx.path.resolve()
    set_builds_root(path.parents[1])  # job processes inherit it
    startup = ctx.ref
    jobs = job_store()
    pending.set_store(jobs)
    manager = DiskcacheManager(diskcache.Cache(str(jobs / "jobs")))
    app = dash.Dash(
        __name__, title="Tag Network", background_callback_manager=manager, serve_locally=True,
        assets_folder=str(Path(__file__).parent / "assets"), suppress_callback_exceptions=True,
        use_pages=True, pages_folder="",
    )
    dash.register_page("steamstudy.app.build_page", path_template=PAGE_PATH, layout=page_layout(startup),
                       title="Tag Network", name="Build")
    dash.register_page("not_found_404", layout=lambda **_kw: missing_layout(served_lang(), startup),
                       title="Tag Network")
    app.layout = html.Div(dash.page_container)

    @app.server.before_request
    def _root_redirect() -> Any:  # `/` opens the startup Build
        if flask.request.path == "/":
            return flask.redirect(build_url(startup))
        return None

    build_layout(ctx)  # fills the relabel registry before any page is served
    callbacks.register(app)
    build_menu.register(app)
    draft_dialog.register(app)
    return app


def run(build_path: str | Path, port: int = 8050, open_browser: bool = True) -> None:
    app = create_app(build_path)
    url = f"http://{HOST}:{port}/"  # never "localhost": about 300 ms extra per callback on Windows
    if open_browser:
        threading.Timer(1.5, lambda: webbrowser.open(url)).start()
    app.run(host=HOST, port=port, debug=False, dev_tools_ui=False, dev_tools_props_check=False)

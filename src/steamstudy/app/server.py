"""Create and run the Tag Network app: offline, `127.0.0.1` only, `debug=False`."""

from __future__ import annotations

import threading
import webbrowser
from pathlib import Path

import dash
import diskcache
import flask
from dash import DiskcacheManager

from steamstudy.app import callbacks
from steamstudy.app.layout import build_layout
from steamstudy.app.loader import load_build
from steamstudy.app.rs_cache import JOBS_DIR
from steamstudy.i18n import COOKIE, DEFAULT, lang_of

HOST = "127.0.0.1"


def served_lang() -> str:
    """The Interface Language of the page being served: the browser's cookie, English without one."""
    return lang_of(flask.request.cookies.get(COOKIE)) if flask.has_request_context() else DEFAULT


def create_app(build_path: str | Path) -> dash.Dash:
    ctx = load_build(build_path)
    jobs = ctx.app_cache / JOBS_DIR  # the background job store, separate from cached results
    jobs.mkdir(parents=True, exist_ok=True)
    manager = DiskcacheManager(diskcache.Cache(str(jobs)))
    app = dash.Dash(
        __name__, title="Tag Network", background_callback_manager=manager, serve_locally=True,
        assets_folder=str(Path(__file__).parent / "assets"), suppress_callback_exceptions=True,
    )
    build_layout(ctx)  # fills the relabel registry before any page is served
    app.layout = lambda: build_layout(ctx, served_lang())  # the first paint is already in the chosen language
    callbacks.register(app)
    return app


def run(build_path: str | Path, port: int = 8050, open_browser: bool = True) -> None:
    app = create_app(build_path)
    url = f"http://{HOST}:{port}/"  # never "localhost": about 300 ms extra per callback on Windows
    if open_browser:
        threading.Timer(1.5, lambda: webbrowser.open(url)).start()
    app.run(host=HOST, port=port, debug=False, dev_tools_ui=False, dev_tools_props_check=False)

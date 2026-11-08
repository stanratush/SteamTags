"""Fire a Dash callback over HTTP, as the browser does (for the App Bundle acceptance test).

The app is a Dash Pages app (ADR 0006): `/_dash-layout` is the page shell, and a tab's page comes from the router
callback for its URL (`page`), as the browser fetches it.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from collections.abc import Callable
from typing import Any

Get = Callable[[str], Any]
Post = Callable[[str, dict[str, Any]], Any]


def layout_props(layout: Any) -> dict[str, dict[str, Any]]:
    """Component id -> props, for every component with a string id in a `/_dash-layout` tree."""
    found: dict[str, dict[str, Any]] = {}

    def walk(node: Any) -> None:
        if isinstance(node, list):
            for child in node:
                walk(child)
        elif isinstance(node, dict) and "props" in node:
            props = node["props"]
            if isinstance(props.get("id"), str):
                found[props["id"]] = props
            walk(props.get("children"))
    walk(layout)
    return found


def page_request(pathname: str, search: str = "") -> dict[str, Any]:
    """The router callback's request for a URL (what the browser posts once `_pages_location` mounts)."""
    return {"output": ".._pages_content.children..._pages_store.data..",
            "outputs": [{"id": "_pages_content", "property": "children"}, {"id": "_pages_store", "property": "data"}],
            "inputs": [{"id": "_pages_location", "property": "pathname", "value": pathname},
                       {"id": "_pages_location", "property": "search", "value": search}],
            "changedPropIds": ["_pages_location.pathname"]}


def page(post: Post, pathname: str, search: str = "") -> Any:
    """The page tree a tab gets for a URL."""
    return post("/_dash-update-component", page_request(pathname, search))["response"]["_pages_content"]["children"]


def client_page(client: Any, pathname: str, search: str = "", cookie: tuple[str, str] | None = None) -> Any:
    """`page` through a Flask test client (an optional cookie, e.g. the Interface Language)."""
    if cookie:
        client.set_cookie(*cookie)
    client.get("/")  # the first request registers the router callback
    reply = client.post("/_dash-update-component", json=page_request(pathname, search))
    return reply.get_json()["response"]["_pages_content"]["children"]


def start_path(client: Any) -> str:
    """Where `/` sends a tab: the startup Build's URL."""
    return client.get("/").headers["Location"].replace("http://localhost", "")


def fire(get: Get, post: Post, output_contains: str, changed: str, pathname: str | None = None) -> dict[str, Any]:
    """Run the callback whose output includes `output_contains` with the page's current values (the page of
    `pathname`, else the startup Build's); returns the callback's response (`response` maps output ids to their
    new props)."""
    deps = get("/_dash-dependencies")
    props = layout_props(page(post, pathname or start(get)))
    callback = next(c for c in deps if output_contains in c["output"])
    outputs = []
    for part in callback["output"].strip(".").split("..."):
        component, _, prop = part.rpartition(".")
        outputs.append({"id": component, "property": prop})
    value = lambda d: {**d, "value": props.get(d["id"], {}).get(d["property"])}  # noqa: E731
    body = {"output": callback["output"], "outputs": outputs, "inputs": [value(d) for d in callback["inputs"]],
            "state": [value(d) for d in callback["state"]], "changedPropIds": [changed]}
    return post("/_dash-update-component", body)


def start(get: Get) -> str:
    """The startup Build's URL path, from `/`'s redirect (read without following it)."""
    return str(get("__start__"))


def http(base: str) -> tuple[Get, Post]:
    """GET and POST helpers for a running app at `base` (e.g. http://127.0.0.1:8051)."""
    def get(path: str) -> Any:
        if path == "__start__":
            with urllib.request.urlopen(base + "/", timeout=60) as r:
                return urllib.parse.urlparse(r.geturl()).path
        with urllib.request.urlopen(base + path, timeout=60) as r:
            return json.loads(r.read().decode("utf-8"))

    def post(path: str, body: dict[str, Any]) -> Any:
        request = urllib.request.Request(base + path, data=json.dumps(body).encode("utf-8"),
                                         headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(request, timeout=300) as r:
            return json.loads(r.read().decode("utf-8"))
    return get, post

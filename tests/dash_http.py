"""Fire a Dash callback over HTTP, as the browser does (for the App Bundle acceptance test)."""

from __future__ import annotations

import json
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


def fire(get: Get, post: Post, output_contains: str, changed: str) -> dict[str, Any]:
    """Run the callback whose output includes `output_contains` with the layout's current values; returns the
    callback's response (`response` maps output ids to their new props)."""
    deps = get("/_dash-dependencies")
    props = layout_props(get("/_dash-layout"))
    callback = next(c for c in deps if output_contains in c["output"])
    outputs = []
    for part in callback["output"].strip(".").split("..."):
        component, _, prop = part.rpartition(".")
        outputs.append({"id": component, "property": prop})
    value = lambda d: {**d, "value": props.get(d["id"], {}).get(d["property"])}  # noqa: E731
    body = {"output": callback["output"], "outputs": outputs, "inputs": [value(d) for d in callback["inputs"]],
            "state": [value(d) for d in callback["state"]], "changedPropIds": [changed]}
    return post("/_dash-update-component", body)


def http(base: str) -> tuple[Get, Post]:
    """GET and POST helpers for a running app at `base` (e.g. http://127.0.0.1:8051)."""
    def get(path: str) -> Any:
        with urllib.request.urlopen(base + path, timeout=60) as r:
            return json.loads(r.read().decode("utf-8"))

    def post(path: str, body: dict[str, Any]) -> Any:
        request = urllib.request.Request(base + path, data=json.dumps(body).encode("utf-8"),
                                         headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(request, timeout=300) as r:
            return json.loads(r.read().decode("utf-8"))
    return get, post

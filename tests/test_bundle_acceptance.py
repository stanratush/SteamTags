"""App Bundle acceptance: make a bundle from a test-mode Build, install it with no package index on every Python
3.12-3.14 on this machine, start the app and load a dataset through the running server; move the folder and
start again. Slow (each first start installs about 50 wheels). Skipped when wheels cannot be fetched."""

from __future__ import annotations

import json
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.request
import zipfile
from pathlib import Path

import pytest

from conftest import REPO
from dash_http import fire, http
from steamstudy.build.core import build
from steamstudy.build.writer import write_build
from steamstudy.bundle.make import BundleError, current_target, make_bundle
from steamstudy.config import load_config
from steamstudy.snapshot import Snapshot
from test_build_network import tagged_world

pytestmark = pytest.mark.slow


def pythons() -> list[tuple[str, str]]:
    """(version, executable) of one CPython 3.12, 3.13 and 3.14 each found here (never 3.14.1, never free-threaded)."""
    listed = subprocess.run(["uv", "python", "list", "--only-installed", "--output-format", "json"],
                            capture_output=True, text=True, encoding="utf-8")
    found: dict[str, tuple[str, str]] = {}
    for p in json.loads(listed.stdout or "[]"):
        version = p.get("version", "")
        minor = ".".join(version.split(".")[:2])
        if (p.get("implementation") == "cpython" and minor in ("3.12", "3.13", "3.14") and version != "3.14.1"
                and p.get("path") and "+freethreaded" not in p.get("key", "") and minor not in found):
            found[minor] = (version, p["path"])
    return [found[m] for m in sorted(found)]


@pytest.fixture(scope="module")
def bundle(tmp_path_factory):
    root = tmp_path_factory.mktemp("bundle-root")
    config = load_config(__import__("conftest").CONFIG_DIR)
    write_build(build(Snapshot(tagged_world().snapshot(root / "snap")), config, "20261006T140000Z-abcdef12"), root)
    try:
        path = make_bundle(root, out=root / "out", cache=REPO / "bundles" / ".cache" / "wheels")
    except BundleError as exc:
        if "needs internet" in str(exc):
            pytest.skip(f"the bundle's wheels cannot be fetched: {exc}")
        raise
    folder = tmp_path_factory.mktemp("extracted")
    with zipfile.ZipFile(path) as zf:
        zf.extractall(folder)
    return path, next(folder.iterdir())


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _start(python: str, folder: Path, log: Path) -> tuple[subprocess.Popen, str]:
    port = _free_port()
    kw: dict = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
    env = {k: v for k, v in os.environ.items() if not k.startswith(("VIRTUAL_ENV", "PYTHONPATH", "UV_"))}
    with log.open("w", encoding="utf-8") as out:
        proc = subprocess.Popen([python, str(folder / "start_tag_network.py"), "--no-browser", "--port", str(port)],
                                cwd=folder, stdout=out, stderr=subprocess.STDOUT, env=env, **kw)
    base = f"http://127.0.0.1:{port}"
    deadline = time.time() + 600
    while time.time() < deadline:
        if proc.poll() is not None:
            raise AssertionError(f"the launcher stopped:\n{log.read_text(encoding='utf-8', errors='replace')}")
        try:
            with urllib.request.urlopen(base + "/", timeout=5) as r:
                if r.status == 200:
                    return proc, base
        except OSError:
            time.sleep(2)
    raise AssertionError(f"the app never answered:\n{log.read_text(encoding='utf-8', errors='replace')}")


def _stop(proc: subprocess.Popen) -> None:
    if os.name == "nt":
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)], capture_output=True)
    else:
        os.killpg(proc.pid, signal.SIGTERM)
    proc.wait(timeout=30)


def _check_running_app(base: str, folder: Path) -> None:
    with urllib.request.urlopen(base + "/", timeout=30) as r:
        page = r.read().decode("utf-8")
    urls = re.findall(r'(?:src|href)="([^"]+)"', page)
    assert urls and all(not re.match(r"^(https?:)?//", u) or "127.0.0.1" in u for u in urls), urls
    assert "/assets/cytoscape.min.js" in page
    with urllib.request.urlopen(base + "/assets/cytoscape.min.js", timeout=30) as r:
        assert r.read() == (REPO / "src" / "steamstudy" / "app" / "assets" / "cytoscape.min.js").read_bytes()
    get, post = http(base)
    meta = fire(get, post, "state-meta.data", "dataset.value")["response"]["state-meta"]["data"]
    assert meta["dataset"] == "overall" and meta["n_nodes"] > 0 and re.fullmatch(r"[0-9a-f]{12}", meta["state_id"])


def _env_python(folder: Path) -> Path:
    return folder / "environment" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def test_the_bundle_was_made_for_this_computer(bundle):
    path, folder = bundle
    manifest = json.loads((folder / "bundle.json").read_text(encoding="utf-8"))
    assert manifest["targets"] == [current_target()] and manifest["python_versions"] == ["3.12", "3.13", "3.14"]
    assert (folder / "builds" / "latest").read_text(encoding="utf-8").strip().endswith("20261006T140000Z-abcdef12")
    assert not any(p.name == "app_cache" for p in (folder / "builds").rglob("*"))
    with zipfile.ZipFile(path) as zf:
        command = next(i for i in zf.infolist() if i.filename.endswith("Start Tag Network.command"))
        assert (command.external_attr >> 16) & 0o111  # executable on macOS
        assert b"\r\n" not in zf.read(command)


@pytest.mark.parametrize("version, python", pythons() or [pytest.param("none", "", marks=pytest.mark.skip(
    reason="no CPython 3.12-3.14 found by uv"))])
def test_the_bundle_installs_offline_and_runs_on_each_python(bundle, tmp_path, version, python):
    _, extracted = bundle
    folder = tmp_path / "copy"
    shutil.copytree(extracted, folder, ignore=shutil.ignore_patterns("environment"))
    proc, base = _start(python, folder, tmp_path / "first.log")
    try:
        assert "Setting up" in (tmp_path / "first.log").read_text(encoding="utf-8", errors="replace")
        _check_running_app(base, folder)
    finally:
        _stop(proc)
    installed = subprocess.run([str(_env_python(folder)), "-m", "pip", "list", "--format", "json",
                                "--disable-pip-version-check"], capture_output=True, text=True, encoding="utf-8")
    names = {p["name"].lower() for p in json.loads(installed.stdout)}
    assert {"steamstudy", "dash", "networkx"} <= names
    assert names.isdisjoint({"lxml", "pandas", "markdown", "dash-cytoscape"})
    imported = subprocess.run([str(_env_python(folder)), "-c", (
        "import sys; from steamstudy.app.server import create_app; from steamstudy.builds import resolve_build; "
        f"create_app(resolve_build({str(folder)!r})); "
        "print(sorted(m for m in ('requests', 'lxml', 'pandas', 'markdown') if m in sys.modules))")],
        capture_output=True, text=True, encoding="utf-8", cwd=tmp_path)
    assert imported.stdout.strip() == "[]", imported.stderr  # requests is installed (dash declares it), never used
    version_run = subprocess.run([str(_env_python(folder)), "-c", "import platform; print(platform.python_version())"],
                                 capture_output=True, text=True)
    assert version_run.stdout.strip() == version

    moved = tmp_path / "moved elsewhere"
    shutil.move(str(folder), moved)
    proc, base = _start(python, moved, tmp_path / "moved.log")
    try:
        assert "Setting up" in (tmp_path / "moved.log").read_text(encoding="utf-8", errors="replace")  # rebuilt
        _check_running_app(base, moved)
    finally:
        _stop(proc)

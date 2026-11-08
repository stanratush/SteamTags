"""The App Bundle's premise: the Tag Network app runs on the app-only install (no pipeline module or dependency),
and it says when a library differs from the version the Build recorded."""

from __future__ import annotations

import ast
import json
import shutil
import subprocess
import sys
import textwrap
import tomllib

import pytest

from conftest import REPO
from steamstudy.app import callbacks as CB
from steamstudy.app.loader import load_build
from steamstudy.build.core import build
from steamstudy.build.writer import write_build
from steamstudy.config import load_config
from steamstudy.snapshot import Snapshot
from test_build_network import tagged_world

SRC = REPO / "src" / "steamstudy"
PIPELINE_MODULES = ("steamstudy.build", "steamstudy.collect", "steamstudy.analysis")
PIPELINE_LIBRARIES = ("lxml", "requests", "pandas", "markdown")


@pytest.fixture(scope="module")
def build_folder(tmp_path_factory):
    config = load_config(__import__("conftest").CONFIG_DIR)
    root = tmp_path_factory.mktemp("apponly")
    return write_build(build(Snapshot(tagged_world().snapshot(root / "snap")), config, "20261006T130000Z-abcdef12"),
                       root)


def _imports(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            yield from (a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            yield node.module


def test_app_modules_never_import_pipeline_modules():
    files = [*(SRC / "app").glob("*.py"), *(SRC / "network").glob("*.py"), *(SRC / "export").glob("*.py"),
             SRC / "config.py", SRC / "versions.py", SRC / "builds.py"]
    bad = sorted((f.relative_to(SRC).as_posix(), m) for f in files for m in _imports(f)
                 if any(m == p or m.startswith(p + ".") for p in PIPELINE_MODULES) or m.split(".")[0] in PIPELINE_LIBRARIES)
    assert bad == []


def test_the_app_runs_with_every_pipeline_module_and_library_blocked(build_folder, tmp_path):
    code = textwrap.dedent(f"""
        import sys
        BLOCKED = {PIPELINE_MODULES + PIPELINE_LIBRARIES!r}
        class Block:
            def find_spec(self, name, path=None, target=None):
                if any(name == b or name.startswith(b + ".") for b in BLOCKED):
                    raise ImportError("app-only install: " + name)
        sys.meta_path.insert(0, Block())
        from steamstudy.cli import main
        assert main(["--root", {str(build_folder.parents[2])!r}, "app", "--clear-cache"]) == 0
        from steamstudy.app.server import create_app
        from steamstudy.app import callbacks as CB
        from steamstudy.app.export import export_zip, open_export
        from steamstudy.app.loader import load_build
        app = create_app({str(build_folder)!r})
        client = app.server.test_client()
        assert client.get("/").status_code == 302 and client.get(client.get("/").headers["Location"]).status_code == 200
        ctx = load_build({str(build_folder)!r})
        c = CB.controls_from_settings(ctx, ctx.default_settings("overall"))
        out = CB.recompute({str(build_folder)!r}, *[c[k] for k in CB.CONTROL_IDS], c["removed"], None)
        _, data = export_zip(ctx, ctx.default_settings("overall"))
        assert open_export(data, builds_root={str(build_folder.parents[1])!r}).state_id_matches
        print("ok", sorted(m for m in sys.modules if any(m == b or m.startswith(b + ".") for b in BLOCKED)))
    """)
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, encoding="utf-8", cwd=tmp_path)
    assert out.returncode == 0, out.stderr[-3000:]
    assert out.stdout.strip().endswith("ok []")


def test_declared_dependencies_are_the_app_set_and_python_is_3_12_to_3_14():
    project = tomllib.loads((REPO / "pyproject.toml").read_text(encoding="utf-8"))
    base = {d.split("=")[0].split(">")[0].split("<")[0].split("!")[0].strip().lower()
            for d in project["project"]["dependencies"]}
    assert base == {"dash", "dash-ag-grid", "diskcache", "multiprocess", "psutil", "networkx", "leidenalg",
                    "python-igraph", "numpy", "scipy", "scikit-learn"}
    pipeline = " ".join(project["dependency-groups"]["pipeline"])
    assert all(lib in pipeline for lib in PIPELINE_LIBRARIES)
    assert "pipeline" in project["tool"]["uv"]["default-groups"]  # `uv sync` still installs the pipeline
    assert project["project"]["requires-python"] == ">=3.12,!=3.14.1,<3.15"


def test_the_app_import_closure_type_checks_for_python_3_12():
    files = [str(p) for p in [*(SRC / "app").glob("*.py"), *(SRC / "network").glob("*.py"),
                               *(SRC / "export").glob("*.py"), *(SRC / "i18n").rglob("*.py"), SRC / "config.py",
                               SRC / "versions.py",
                               SRC / "builds.py", SRC / "cli.py", SRC / "snapshot.py", SRC / "__init__.py"]]
    out = subprocess.run([sys.executable, "-m", "mypy", "--python-version", "3.12", "--follow-imports", "silent",
                          *files], capture_output=True, text=True, encoding="utf-8", cwd=REPO)
    assert out.returncode == 0, out.stdout[-3000:]


# ----------------------------------------------------------------------------- the library-version banner


def _recorded_copy(build_folder, tmp_path, **changes):
    moved = tmp_path / "builds" / build_folder.parent.name / build_folder.name
    shutil.copytree(build_folder, moved)
    bj_path = moved / "datasets" / "build.json"
    bj = json.loads(bj_path.read_text(encoding="utf-8"))
    bj["software_versions"].update(changes)
    bj_path.write_text(json.dumps(bj), encoding="utf-8")
    return moved


def _banners(folder):
    ctx = load_build(folder)
    c = CB.controls_from_settings(ctx, ctx.default_settings("overall"))
    out = CB.recompute(str(folder), *[c[k] for k in CB.CONTROL_IDS], c["removed"], None)
    return [b.children for b in out[14]]


def test_a_library_at_another_version_than_the_build_recorded_shows_a_banner(build_folder, tmp_path):
    from importlib import metadata

    folder = _recorded_copy(build_folder, tmp_path, networkx="3.6", dash="4.0.0")
    text = " ".join(_banners(folder))
    assert f"networkx 3.6 (Build) vs {metadata.version('networkx')} (installed)" in text
    assert f"dash 4.0.0 (Build) vs {metadata.version('dash')} (installed)" in text
    assert "numpy" not in text


def test_pipeline_libraries_and_python_never_trigger_the_banner(build_folder, tmp_path):
    folder = _recorded_copy(build_folder, tmp_path, pandas="0.1", lxml="0.1", python="3.0.0", markdown="0.1")
    assert not any("library" in b.lower() for b in _banners(folder))
    assert not any("library" in b.lower() for b in _banners(build_folder))

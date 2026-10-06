"""App Bundle: the launcher's refusal checks and rebuild decision, and the wheel plan's completeness check."""

from __future__ import annotations

import copy
from pathlib import Path

import pytest

from conftest import REPO
from steamstudy.bundle import start_tag_network as L
from steamstudy.bundle.make import BundleError, make_bundle
from steamstudy.bundle.wheels import PYTHONS, closure, plan, read_lock, TARGETS


@pytest.fixture
def folder(tmp_path):
    (tmp_path / "wheels").mkdir()
    return tmp_path


@pytest.mark.parametrize("version, ok", [((3, 11, 9), False), ((3, 12, 0), True), ((3, 13, 0), True),
                                         ((3, 14, 1), False), ((3, 14, 8), True), ((3, 15, 0), False)])
def test_python_versions(folder, version, ok):
    problems = L.refusals(version, "Windows", "AMD64", folder, ["windows"], True, True)
    assert (problems == []) == ok


def test_each_refusal_says_what_to_do(folder, tmp_path):
    assert "made for linux" in L.refusals((3, 13, 0), "Windows", "AMD64", folder, ["linux"], True, True)[0]
    assert "Copy this folder to your own disk first" in L.refusals((3, 13, 0), "Windows", "AMD64", folder,
                                                                   ["windows"], False, True)[0]
    assert "python3-venv" in L.refusals((3, 13, 0), "Linux", "x86_64", folder, ["linux"], True, False)[0]
    zipped = tmp_path / "Temp1_tag-network.zip" / "tag-network"
    zipped.mkdir(parents=True)
    (zipped / "wheels").mkdir()
    assert "Extract the whole zip first" in L.refusals((3, 13, 0), "Windows", "AMD64", zipped, ["windows"], True, True)[0]


def test_targets_of_this_computer():
    assert L.target_name("Windows", "AMD64") == "windows" and L.target_name("Darwin", "arm64") == "macos"
    assert L.target_name("Linux", "x86_64") == "linux" and L.target_name("Darwin", "x86_64") is None


def test_the_environment_is_rebuilt_when_folder_python_or_bundle_changed(tmp_path):
    env_python = tmp_path / "python.exe"
    env_python.write_text("x")
    current = {"python": "a", "version": "3.13.0", "manifest": "m", "folder": "f"}
    assert not L.needs_rebuild(dict(current), current, env_python)
    for key in current:
        assert L.needs_rebuild({**current, key: "other"}, current, env_python)
    assert L.needs_rebuild(None, current, env_python)
    assert L.needs_rebuild(current, current, tmp_path / "missing.exe")


def test_bundles_for_other_targets_have_every_wheel_for_every_python():
    lock = read_lock(REPO / "uv.lock")
    p = plan(lock, ["linux", "macos", "windows"])
    assert p.complete, p.missing
    for target in ("linux", "macos", "windows"):
        for python in PYTHONS:
            assert set(p.wheels[(target, python)]) == set(closure(lock, TARGETS[target], python))
    assert {"lxml", "pandas", "markdown", "dash-cytoscape"}.isdisjoint(w.package for w in p.all_wheels())


def test_a_missing_wheel_writes_nothing(tmp_path, monkeypatch):
    lock = read_lock(REPO / "uv.lock")
    broken = copy.deepcopy(lock)
    numpy = next(p for p in broken["package"] if p["name"] == "numpy")
    numpy["wheels"] = [w for w in numpy["wheels"] if "cp313" not in w["url"] or "manylinux" not in w["url"]]
    import tomllib  # noqa: F401
    monkeypatch.setattr("steamstudy.bundle.make.read_lock", lambda _path: broken)
    root = tmp_path / "root"
    (root / "builds" / "s" / "b" / "datasets").mkdir(parents=True)
    (root / "builds" / "latest").write_text("s/b\n")
    with pytest.raises(BundleError, match="numpy .* for linux / Python 3.13"):
        make_bundle(root, targets=["linux"], out=tmp_path / "out")
    assert not (tmp_path / "out").exists()


def test_a_missing_build_writes_nothing(tmp_path):
    with pytest.raises(BundleError):
        make_bundle(tmp_path, targets=["linux"], out=tmp_path / "out")
    assert not (tmp_path / "out").exists()


def test_the_launcher_uses_only_the_standard_library_and_plain_ascii():
    import ast
    import sys

    source = Path(L.__file__).read_text(encoding="utf-8")
    assert source.isascii()  # old Windows console code pages print anything else as "?"
    imported = {n.name.split(".")[0] for node in ast.walk(ast.parse(source))
                for n in (node.names if isinstance(node, ast.Import) else [])}
    imported |= {node.module.split(".")[0] for node in ast.walk(ast.parse(source))
                 if isinstance(node, ast.ImportFrom) and node.module}
    assert imported - {"__future__"} <= set(sys.stdlib_module_names)

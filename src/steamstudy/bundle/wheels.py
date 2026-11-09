"""Which wheels an App Bundle carries: the app's dependencies from `uv.lock`, per target OS and Python version.

Everything is pinned to the lock: the package set is the closure of `steamstudy`'s own dependencies (never the
dependency groups), dependency markers are evaluated for each target and Python version, and every wheel the
lock lists that the target can install is kept (with its sha256), so pip can pick the best one on the user's
machine. A plan is complete only when every package has at least one wheel for every target and Python.
"""

from __future__ import annotations

import tomllib
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from packaging import tags
from packaging.markers import Marker
from packaging.utils import parse_wheel_filename

PYTHONS: tuple[tuple[int, int], ...] = ((3, 12), (3, 13), (3, 14))


@dataclass(frozen=True)
class Target:
    name: str
    sys_platform: str
    platform_system: str
    platform_machine: str
    os_name: str
    platforms: tuple[str, ...]  # wheel platform tags, most preferred first

    def label(self) -> str:
        return {"windows": "Windows x64", "macos": "macOS (Apple silicon)", "linux": "Linux x86_64"}[self.name]


TARGETS: dict[str, Target] = {
    "windows": Target("windows", "win32", "Windows", "AMD64", "nt", ("win_amd64",)),
    "macos": Target("macos", "darwin", "Darwin", "arm64", "posix", tuple(tags.mac_platforms((15, 0), "arm64"))),
    "linux": Target("linux", "linux", "Linux", "x86_64", "posix",
                    tuple(f"manylinux_2_{minor}_x86_64" for minor in range(28, 4, -1))
                    + ("manylinux2014_x86_64", "manylinux2010_x86_64", "manylinux1_x86_64")),
}


@dataclass(frozen=True)
class Wheel:
    package: str
    version: str
    filename: str
    url: str
    sha256: str


@dataclass
class Plan:
    """wheels[(target, python)] -> package -> every compatible wheel; missing lists what no wheel covers."""

    lock_packages: dict[str, dict[str, Any]]
    wheels: dict[tuple[str, tuple[int, int]], dict[str, list[Wheel]]] = field(default_factory=dict)
    missing: list[tuple[str, str, str, str]] = field(default_factory=list)  # package, version, target, python

    @property
    def complete(self) -> bool:
        return not self.missing

    def all_wheels(self) -> list[Wheel]:
        """Every wheel once (pure-Python wheels are shared by all targets and Pythons)."""
        unique = {w.filename: w for per in self.wheels.values() for ws in per.values() for w in ws}
        return [unique[name] for name in sorted(unique)]


def read_lock(path: Path) -> dict[str, Any]:
    return tomllib.loads(Path(path).read_text(encoding="utf-8"))


def environment(target: Target, python: tuple[int, int]) -> dict[str, str]:
    """PEP 508 marker variables of a CPython of this version on this target."""
    full = f"{python[0]}.{python[1]}.0"
    return {"implementation_name": "cpython", "implementation_version": full, "os_name": target.os_name,
            "platform_machine": target.platform_machine, "platform_python_implementation": "CPython",
            "platform_release": "", "platform_system": target.platform_system, "platform_version": "",
            "python_full_version": full, "python_version": f"{python[0]}.{python[1]}",
            "sys_platform": target.sys_platform, "extra": ""}


def closure(lock: dict[str, Any], target: Target, python: tuple[int, int], root: str = "steamstudy",
            extra: Sequence[str] = ()) -> list[str]:
    """The packages the app needs on this target and Python: `root`'s dependencies and theirs, markers applied,
    plus the `extra` packages (at their locked versions) and their dependencies."""
    packages = {p["name"]: p for p in lock["package"]}
    env = environment(target, python)
    todo = list(packages[root].get("dependencies", [])) + [{"name": name} for name in extra]
    seen: set[tuple[str, str]] = set()
    names: set[str] = set()
    while todo:
        dep = todo.pop()
        if "marker" in dep and not Marker(dep["marker"]).evaluate(env):
            continue
        name = dep["name"]
        for part in [""] + list(dep.get("extra", [])):
            if (name, part) in seen:
                continue
            seen.add((name, part))
            package = packages[name]
            todo.extend(package.get("dependencies", []) if part == "" else
                        package.get("optional-dependencies", {}).get(part, []))
        names.add(name)
    return sorted(names)


def supported_tags(target: Target, python: tuple[int, int]) -> list[tags.Tag]:
    interpreter = f"cp{python[0]}{python[1]}"
    return (list(tags.cpython_tags(python, abis=[interpreter, "abi3", "none"], platforms=target.platforms))
            + list(tags.compatible_tags(python, interpreter, target.platforms)))


def compatible(package: dict[str, Any], target: Target, python: tuple[int, int]) -> list[Wheel]:
    """Every wheel of a locked package this target and Python can install."""
    accepted = set(supported_tags(target, python))
    out = []
    for w in package.get("wheels", []):
        filename = w["url"].rsplit("/", 1)[1]
        if accepted & set(parse_wheel_filename(filename)[3]):
            out.append(Wheel(package["name"], package["version"], filename, w["url"], w["hash"].split(":", 1)[1]))
    return out


def plan(lock: dict[str, Any], targets: list[str], pythons: tuple[tuple[int, int], ...] = PYTHONS,
         extra: Sequence[str] = ()) -> Plan:
    """The wheels every target and Python needs: the app's, plus the `extra` packages (a bundle that makes Builds:
    `BUILD_LIBRARIES`)."""
    packages = {p["name"]: p for p in lock["package"]}
    result = Plan(packages)
    for name in targets:
        target = TARGETS[name]
        for python in pythons:
            per: dict[str, list[Wheel]] = {}
            for package in closure(lock, target, python, extra=extra):
                found = compatible(packages[package], target, python)
                if found:
                    per[package] = found
                else:
                    result.missing.append((package, packages[package]["version"], name, f"{python[0]}.{python[1]}"))
            result.wheels[(name, python)] = per
    return result


def requirements(wheels: dict[str, list[Wheel]], extra: Sequence[str] = ()) -> str:
    """A pip requirements file pinned to exact versions with every acceptable hash (for --require-hashes)."""
    lines = [f"{p}=={ws[0].version} " + " ".join(f"--hash=sha256:{w.sha256}" for w in ws)
             for p, ws in sorted(wheels.items())]
    return "\n".join(lines + list(extra)) + "\n"

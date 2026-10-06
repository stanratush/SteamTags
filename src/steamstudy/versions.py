"""Software versions: what a Build records, and what the running app compares them with.

Importable by the app without any pipeline module or pipeline dependency.
"""

from __future__ import annotations

import platform
from importlib import metadata

from steamstudy import __version__

# The libraries a Build records (python and steamstudy are recorded too).
RECORDED = ("networkx", "leidenalg", "igraph", "python-igraph", "numpy", "scipy", "scikit-learn", "pandas", "lxml",
            "dash", "dash-ag-grid")
# The libraries the Tag Network app uses: a different installed version may change what it shows.
APP_LIBRARIES = ("networkx", "leidenalg", "igraph", "python-igraph", "numpy", "scipy", "scikit-learn", "dash",
                 "dash-ag-grid")


def installed(package: str) -> str | None:
    try:
        return metadata.version(package)
    except metadata.PackageNotFoundError:
        return None


def software_versions() -> dict[str, str]:
    versions = {"python": platform.python_version(), "steamstudy": __version__}
    for package in RECORDED:
        version = installed(package)
        if version is not None:
            versions[package] = version
    return versions


def version_mismatches(recorded: dict[str, str]) -> list[tuple[str, str, str]]:
    """(library, recorded version, installed version) for every app library installed at another version than the
    Build recorded. Pipeline-only libraries the app lacks, and the Python version, never count."""
    out = []
    for package in APP_LIBRARIES:
        now = installed(package)
        if package in recorded and now is not None and recorded[package] != now:
            out.append((package, recorded[package], now))
    return out

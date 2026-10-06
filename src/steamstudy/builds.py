"""Where Builds live: `<root>/builds/<snapshot_id>/<build_id>/`, with `latest` pointers.

Importable by the app without any pipeline module (the App Bundle installs only the app).
"""

from __future__ import annotations

from pathlib import Path


def builds_dir(root: Path) -> Path:
    return Path(root) / "builds"


def resolve_build(root: Path, build: str | None = None, snapshot: str | None = None) -> Path:
    """A Build folder from an id (or `<snapshot>/<build>`), defaulting to the latest."""
    base = builds_dir(root)
    if build and "/" in build:
        snapshot, build = build.split("/", 1)
    if build is None:
        pointer = (base / snapshot / "latest") if snapshot else (base / "latest")
        if not pointer.is_file():
            raise FileNotFoundError(f"no Build found under {base}")
        ref = pointer.read_text(encoding="utf-8").strip()
        return (base / snapshot / ref) if snapshot else (base / ref)
    if snapshot:
        return base / snapshot / build
    matches = [p for p in base.glob(f"*/{build}") if p.is_dir()]
    if len(matches) != 1:
        raise FileNotFoundError(f"Build {build} not found (or ambiguous) under {base}")
    return matches[0]

"""Hashes of every Build output file (except build.json) for two fixed worlds; used to prove refactors move no byte."""
from __future__ import annotations

import hashlib
import tempfile
from pathlib import Path

from steamstudy.build.core import build
from steamstudy.build.writer import write_build
from steamstudy.snapshot import Snapshot


def hashes(config, world, build_id="20261005T140000Z-abcdef12") -> dict[str, str]:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        folder = write_build(build(Snapshot(world.snapshot(root / "snap")), config, build_id), root)
        return {p.relative_to(folder).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(folder.rglob("*")) if p.is_file() and p.name != "build.json"}


def all_worlds(config) -> dict[str, dict[str, str]]:
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from test_build_exclusions import _world
    from test_build_network import tagged_world

    return {"exclusions_world": hashes(config, _world()), "tagged_world": hashes(config, tagged_world())}

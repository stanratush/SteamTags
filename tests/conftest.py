from __future__ import annotations

from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
CONFIG_DIR = REPO / "config"


@pytest.fixture
def config_dir() -> Path:
    return CONFIG_DIR


def neutral_collection(cfg, user_agent: str = "steamstudy-test (contact: test@example.invalid)"):
    """The config with collection settings that do not depend on the researcher's local edits:
    a test User-Agent, and no gate or SteamDB permission recorded."""
    import dataclasses

    from steamstudy.config import GateRecord

    empty = GateRecord("", "")
    collection = dataclasses.replace(cfg.collection, user_agent=user_agent, operator_reply=empty, ethics_check=empty,
                                     steamdb_permission=empty, publish_monthly_players="")
    return dataclasses.replace(cfg, collection=collection)


@pytest.fixture(scope="session")
def tagged_build(tmp_path_factory) -> Path:
    """The tagged-world test Build (120 games; overall and puzzle), written once per session."""
    from steamstudy.build.core import build
    from steamstudy.build.writer import write_build
    from steamstudy.config import load_config
    from steamstudy.snapshot import Snapshot
    from test_build_network import tagged_world

    root = tmp_path_factory.mktemp("tagged")
    return write_build(build(Snapshot(tagged_world().snapshot(root / "snap")), load_config(CONFIG_DIR),
                             "20261005T140000Z-abcdef12"), root)

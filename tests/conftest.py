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

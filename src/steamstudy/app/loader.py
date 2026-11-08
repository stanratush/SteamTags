"""Loading one Build for the app: its datasets, provenance and the network defaults it was built with.

The app only ever analyses the pipeline's own exports, read through `steamstudy.dataset.read_dataset`.
Everything here is a plain function of the Build folder; nothing is cached between calls.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from steamstudy.config import ConfigError, DatasetDef, NetworkDefaults, TagRef, config_from_data
from steamstudy.dataset import Dataset, read_dataset
from steamstudy.network.defaults import default_settings
from steamstudy.network.model import Game, Settings, TagContext


@dataclass(frozen=True)
class BuildContext:
    path: Path
    build_json: dict[str, Any]
    network: NetworkDefaults
    datasets: tuple[DatasetDef, ...]
    genre_tags: tuple[TagRef, ...]
    tag_depth: int | str = "all"  # Tag Depth: an integer, or "all"

    @property
    def depth_cut(self) -> int | None:
        return None if self.tag_depth == "all" else int(self.tag_depth)

    @property
    def build_id(self) -> str:
        return str(self.build_json["build_id"])

    @property
    def mode(self) -> str:
        return str(self.build_json.get("mode", ""))

    def dataset(self, key: str) -> DatasetDef:
        return next(d for d in self.datasets if d.key == key)

    def read(self, dataset: str) -> Dataset:
        """The dataset through the one reader (Tag Depth applied)."""
        return read_dataset(self, dataset)

    def games(self, dataset: str) -> list[Game]:
        return self.read(dataset).games()

    def context(self, dataset: str) -> TagContext:
        return self.read(dataset).context()

    def default_settings(self, dataset: str) -> Settings:
        d = self.dataset(dataset)
        settings, _ = default_settings(self.build_id, dataset, d.defining_tag.id if d.defining_tag else None,
                                       (t.id for t in self.genre_tags), self.network)
        return settings

    @property
    def app_cache(self) -> Path:
        return self.path / "app_cache"

    def build_json_hash(self) -> str:
        return build_json_hash(self.build_json)


def build_json_hash(build_json: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(build_json, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
                          .encode("utf-8")).hexdigest()


def load_build(path: str | Path) -> BuildContext:
    path = Path(path)
    bj_path = path / "datasets" / "build.json"
    if not bj_path.is_file():
        raise FileNotFoundError(f"not a Build folder: {path}")
    build_json = json.loads(bj_path.read_text(encoding="utf-8"))
    files = dict(build_json["config"])
    files["collection"] = _MINIMAL_COLLECTION
    try:
        config = config_from_data(files)
    except ConfigError as exc:
        raise ValueError(f"build.json config of {path} is not readable: {exc}") from exc
    return BuildContext(path, build_json, config.network, config.datasets, config.genre_tags, config.tag_depth)


# build.json copies every file a Build reads; the collection settings are not among them.
_MINIMAL_COLLECTION: dict[str, Any] = {
    "contact": {"user_agent": "-"}, "listing": {"passes": 1},
    "rates": {"steamcharts_per_second": 1.0, "store_seconds_per_request": 1.0},
    "timeouts": {"connect_seconds": 1, "read_seconds": 1},
    "retry": {"schedule_seconds": [1], "parse_failures_in_a_row": 1},
}

"""Loading one Build for the app: its datasets, provenance and the network defaults it was built with.

The app only ever analyses the pipeline's own exports, read through `steamstudy.dataset.read_dataset`.
Everything here is a plain function of the Build folder; nothing is cached between calls.

A tab names its Build by a ref, `<source_id>/<build_id>` (its URL, ADR 0006, and the `build-path` store), resolved
under the app's builds root (`BUILDS_ROOT_ENV`, set by `server.create_app`, so job processes see it too). A value
from the browser is never taken as a filesystem path: inside a request only a ref is accepted. Code outside a
request (the CLI, tests) may still pass a Build folder.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from steamstudy.builds import ref_of  # noqa: F401  (re-exported: the app reads it from here)
from steamstudy.config import ConfigError, DatasetDef, NetworkDefaults, TagRef, build_config
from steamstudy.config import MINIMAL_COLLECTION, config_from_data
from steamstudy.dataset import Dataset, read_dataset
from steamstudy.network.defaults import default_settings
from steamstudy.network.model import Game, Settings, TagContext

BUILDS_ROOT_ENV = "STEAMSTUDY_BUILDS_ROOT"
# An id: a letter or digit, then letters, digits, '_', '.', '-' (never "..": no part may climb out of the root).
_ID = r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}"
_REF = re.compile(rf"({_ID})/({_ID})")


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
    def ref(self) -> str:
        """`<source_id>/<build_id>`: how a tab names this Build (its URL and the `build-path` store)."""
        return ref_of(self.path)

    @property
    def app_cache(self) -> Path:
        return self.path / "app_cache"

    def build_json_hash(self) -> str:
        return build_json_hash(self.build_json)


def build_json_hash(build_json: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(build_json, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
                          .encode("utf-8")).hexdigest()


def is_ref(value: object) -> bool:
    """Whether a value is a well-formed Build ref, `<source_id>/<build_id>` (and nothing that could climb)."""
    return isinstance(value, str) and _REF.fullmatch(value) is not None and ".." not in value


def builds_root() -> Path | None:
    """The app's builds root (`<root>/builds`), or None outside a running app."""
    value = os.environ.get(BUILDS_ROOT_ENV)
    return Path(value) if value else None


def set_builds_root(root: str | Path) -> None:
    os.environ[BUILDS_ROOT_ENV] = str(Path(root).resolve())


def resolve_ref(ref: str, root: str | Path | None = None) -> Path:
    """The Build folder a ref names under the builds root; FileNotFoundError when there is none."""
    base = Path(root) if root is not None else builds_root()
    if not is_ref(ref) or base is None:
        raise FileNotFoundError(f"not a Build id: {ref!r}")
    path = base / ref
    if not (path / "datasets" / "build.json").is_file():
        raise FileNotFoundError(f"no Build {ref} under {base}")
    return path


def _in_request() -> bool:
    try:
        import flask
    except ImportError:  # pragma: no cover - the app always has Flask
        return False
    return flask.has_request_context()


def store_value(ctx: BuildContext) -> str:
    """What the tab's `build-path` store holds: the ref when the app's root has this Build, else its folder (a
    layout built outside a running app, by a test)."""
    root = builds_root()
    if root is not None:
        try:
            if resolve_ref(ctx.ref, root).resolve() == ctx.path.resolve():
                return ctx.ref
        except FileNotFoundError:
            pass
    return str(ctx.path)


def build_folder(value: str | Path) -> Path:
    """A Build folder from a ref (resolved under the builds root) or, outside a request, a folder."""
    if is_ref(value):
        root = builds_root()
        if root is not None and (root / str(value) / "datasets" / "build.json").is_file():
            return root / str(value)
    if isinstance(value, str) and _in_request():
        raise FileNotFoundError(f"not a Build id: {value!r}")
    return Path(value)


def load_build(path: str | Path) -> BuildContext:
    path = build_folder(path)
    bj_path = path / "datasets" / "build.json"
    if not bj_path.is_file():
        raise FileNotFoundError(f"not a Build folder: {path}")
    build_json = json.loads(bj_path.read_text(encoding="utf-8"))
    try:
        if build_json.get("source") == "import":  # attribute names resolved at Build time (the Import is not shipped)
            config = config_from_data({**build_json["resolved_config"], "collection": MINIMAL_COLLECTION,
                                       "manual_metadata": {}}, source="import")
        else:
            config = build_config(dict(build_json["config"]))
    except ConfigError as exc:
        raise ValueError(f"build.json config of {path} is not readable: {exc}") from exc
    return BuildContext(path, build_json, config.network, config.datasets, config.genre_tags, config.tag_depth)


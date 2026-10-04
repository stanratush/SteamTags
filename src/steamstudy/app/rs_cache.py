"""The app's only persistent cache: Removal Sensitivity results per Network State, in `<build>/app_cache/`.

Keyed by the Network State key plus the method version. Never evicted automatically; "Clear app cache"
(button or `steamstudy app --clear-cache`) deletes it.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from steamstudy.network.model import canonical_key_json
from steamstudy.network.sensitivity import METHOD_VERSION

RESULTS_DIR = "removal_sensitivity"
JOBS_DIR = "jobs"


@dataclass
class CachedRun:
    state_key: dict[str, Any]
    method_version: str
    total: int
    rows: dict[int, dict[str, Any]] = field(default_factory=dict)  # tag -> row

    @property
    def done(self) -> int:
        return len(self.rows)

    @property
    def complete(self) -> bool:
        return self.done >= self.total

    def ordered_rows(self) -> list[dict[str, Any]]:
        return sorted(self.rows.values(), key=lambda r: r["run_order"])


def cache_key(state_key: dict[str, Any], method_version: str = METHOD_VERSION) -> str:
    return hashlib.sha256((canonical_key_json(state_key) + "|" + method_version).encode("utf-8")).hexdigest()


def _path(cache_root: Path, state_key: dict[str, Any]) -> Path:
    return Path(cache_root) / RESULTS_DIR / f"{cache_key(state_key)}.json"


def load(cache_root: Path, state_key: dict[str, Any]) -> CachedRun | None:
    path = _path(cache_root, state_key)
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return CachedRun(data["state_key"], data["method_version"], int(data["total"]),
                     {int(k): v for k, v in data["rows"].items()})


def save(cache_root: Path, run: CachedRun) -> None:
    path = _path(cache_root, run.state_key)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps({"state_key": run.state_key, "method_version": run.method_version, "total": run.total,
                               "rows": {str(k): v for k, v in run.rows.items()}}, ensure_ascii=False),
                   encoding="utf-8")
    tmp.replace(path)


def add_row(cache_root: Path, state_key: dict[str, Any], total: int, row: dict[str, Any]) -> CachedRun:
    run = load(cache_root, state_key) or CachedRun(state_key, METHOD_VERSION, total)
    run.rows[int(row["tag_id"])] = row
    save(cache_root, run)
    return run


def clear(cache_root: Path) -> int:
    """Delete every cached result (and so every Continue offer); returns how many were removed."""
    results = Path(cache_root) / RESULTS_DIR
    count = len(list(results.glob("*.json"))) if results.is_dir() else 0
    if results.is_dir():
        shutil.rmtree(results)
    return count

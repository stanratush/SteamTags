"""Export this state (one self-contained zip) and Open Network State… (reopen it exactly).

Nothing is ever written into the Build folder by an export.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import io
import json
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from steamstudy.app.loader import BuildContext, build_json_hash, load_build
from steamstudy.export import schema as S
from steamstudy.export.schema import SCHEMA_VERSION, columns_block
from steamstudy.export.writer import csv_bytes, parse_value
from steamstudy.network.layout import Layout, Positions, layout_state
from steamstudy.network.model import KEY_VERSION, Settings, state_id_of
from steamstudy.network.sensitivity import METHOD_VERSION
from steamstudy.network.stability import TRADES_PER_GAME
from steamstudy.network.state import NetworkState, compute_state
from steamstudy.network.tables import state_tables
from steamstudy.versions import software_versions

CENTER_TIE_BREAK = "smallest medoid_score (rounded to 12 decimals), then more n_games, then lower tag_id"
CLUSTER_LABEL_RULE = ("C1… by size descending, ties by smallest member tag_id; Multi-Tag Clusters first, then "
                      "One-Tag Clusters by tag_id")


class OpenRefused(ValueError):
    """The export cannot be reopened (Build changed, key_version differs, unreadable file)."""


class BuildNotFound(FileNotFoundError):
    """No Build available to the app has the export's identity (its build_id)."""

    def __init__(self, build_id: str, snapshot_id: str, builds_root: Path):
        super().__init__(f"this Network State needs Build {build_id} (Snapshot {snapshot_id}), which is not among the Builds "
                         f"in {builds_root}; copy that Build folder there and open again")
        self.build_id, self.snapshot_id = build_id, snapshot_id


def export_filename(dataset: str, state_id: str, now: dt.datetime) -> str:
    return f"steamstudy_{dataset}_{state_id}_{now.strftime('%Y%m%dT%H%M%SZ')}.zip"


def removal_status(rows: list[dict[str, Any]] | None, total: int) -> str | dict[str, Any]:
    if not rows:
        return "not_run"
    return {"status": "complete" if len(rows) >= total else "partial", "done": len(rows), "total": total}


def export_zip(
    ctx: BuildContext,
    settings: Settings,
    *,
    relayout_positions: Positions | None = None,
    removal_rows: list[dict[str, Any]] | None = None,
    state: NetworkState | None = None,
    layout: Layout | None = None,
    now: dt.datetime | None = None,
) -> tuple[str, bytes]:
    """The zip for one Network State. `removal_rows` must belong to this exact key (callers check). The layout
    is computed after the state, for the reference canvas, unless one is given."""
    now = now or dt.datetime.now(dt.UTC)
    state = state or compute_state(ctx.games(settings.dataset), settings, ctx.context(settings.dataset))
    layout = layout or layout_state(state, positions=relayout_positions or None)
    tables = state_tables(state, layout)
    files: dict[str, bytes] = {}
    for schema in S.APP_TABLES:
        if schema.name == "removal_sensitivity.csv":
            if removal_rows:
                ordered = sorted(removal_rows, key=lambda r: r["run_order"])
                files[schema.name] = csv_bytes(schema, ordered)
            continue
        files[schema.name] = csv_bytes(schema, tables[schema.name])
    row_counts = {name: len(tables[name]) for name in tables}
    if removal_rows:
        row_counts["removal_sensitivity.csv"] = len(removal_rows)
    export_json = {
        "schema_version": SCHEMA_VERSION,
        "state_key": settings.key(),
        "state_id": state.state_id,
        "layout_source": "relayout" if relayout_positions else "default",
        "exported_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "software_versions": software_versions(),
        "build_path": str(ctx.path.resolve()),
        "build_json": ctx.build_json,
        "files": {name: {"rows": row_counts[name], "sha256": hashlib.sha256(data).hexdigest()}
                  for name, data in sorted(files.items())},
        "method_constants": method_constants(state),
        "removal_sensitivity": removal_status(removal_rows, len(state.nodes)),
        "columns": columns_block([s for s in S.APP_TABLES if s.name in files]),
    }
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, data in sorted(files.items()):
            zf.writestr(name, data)
        zf.writestr("export.json", json.dumps(export_json, indent=2, ensure_ascii=False).encode("utf-8"))
    return export_filename(settings.dataset, state.state_id, now), buffer.getvalue()


def method_constants(state: NetworkState) -> dict[str, Any]:
    return {
        "null_replicates": state.settings.null_replicates,
        "replicate_seeds": [r.seed for r in state.null_replicates],
        "null_model": f"bipartite curveball, {TRADES_PER_GAME} trades per game, same games and visible tags",
        "noise_seeds_k": state.settings.noise_seeds,
        "noise_seeds": [r.seed for r in state.seed_runs],
        "removal_sensitivity_method_version": METHOD_VERSION,
        "center_tie_break": CENTER_TIE_BREAK,
        "cluster_label_rule": CLUSTER_LABEL_RULE,
        "silhouette": "jaccard_game_set",
    }


# ----------------------------------------------------------------------------- Open Network State…


@dataclass
class OpenedState:
    build_path: Path
    settings: Settings
    recorded_state_id: str
    layout_source: str
    schema_version: int
    relayout_positions: Positions = field(default_factory=dict)
    removal_rows: list[dict[str, Any]] = field(default_factory=list)
    recorded_files: dict[str, Any] = field(default_factory=dict)
    removal_total: int | None = None  # tags in the full run, from export.json (a partial run has fewer rows)

    @property
    def state_id_matches(self) -> bool:
        return state_id_of(self.settings.key()) == self.recorded_state_id


def read_export(data: bytes) -> tuple[dict[str, Any], dict[str, bytes]]:
    """(export.json, other files) from a zip or a bare export.json."""
    if data[:2] == b"PK":
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                files = {name: zf.read(name) for name in zf.namelist()}
        except zipfile.BadZipFile as exc:
            raise OpenRefused(f"not a readable zip: {exc}") from exc
        if "export.json" not in files:
            raise OpenRefused("the zip has no export.json")
        return json.loads(files.pop("export.json").decode("utf-8")), files
    try:
        return json.loads(data.decode("utf-8-sig")), {}
    except (UnicodeDecodeError, ValueError) as exc:
        raise OpenRefused("neither an export zip nor an export.json") from exc


def find_build(builds_root: str | Path, build_json: dict[str, Any]) -> Path:
    """The Build folder under `builds_root` (`<snapshot>/<build_id>/`) with this build.json's identity: the same
    build_id and the same build.json hash. A Build with the same id but another hash is refused."""
    build_id = str(build_json.get("build_id", ""))
    snapshot_id = str(build_json.get("snapshot_id", ""))
    root = Path(builds_root)
    candidates = (sorted(p for p in root.glob(f"*/{build_id}") if (p / "datasets" / "build.json").is_file())
                  if build_id else [])
    wanted = build_json_hash(build_json)
    for path in candidates:
        if build_json_hash(json.loads((path / "datasets" / "build.json").read_text(encoding="utf-8"))) == wanted:
            return path
    if candidates:
        raise OpenRefused(f"the Build {build_id} at {candidates[0]} differs from the one this Network State was "
                          f"exported from (its build.json changed)")
    raise BuildNotFound(build_id, snapshot_id, root)


def open_export(data: bytes, *, builds_root: str | Path) -> OpenedState:
    """Reopen an export. Its Build is found by identity among the Builds under `builds_root`; the recorded
    `build_path` is informational only."""
    export, files = read_export(data)
    try:
        key = export["state_key"]
        recorded = str(export["state_id"])
    except KeyError as exc:
        raise OpenRefused(f"export.json lacks {exc}") from exc
    if int(key.get("key_version", -1)) != KEY_VERSION:
        raise OpenRefused(f"key_version {key.get('key_version')} differs from this software's {KEY_VERSION}: "
                          f"the methods changed, so the state cannot be reproduced exactly")
    path = find_build(builds_root, export.get("build_json") or {})
    try:
        settings = Settings.from_key(key)
    except (KeyError, ValueError, TypeError) as exc:
        raise OpenRefused(f"the state key cannot be read: {exc}") from exc
    opened = OpenedState(path, settings, recorded, str(export.get("layout_source", "default")),
                         int(export.get("schema_version", 0)), recorded_files=dict(export.get("files", {})))
    status = export.get("removal_sensitivity")
    if isinstance(status, dict) and "total" in status:
        opened.removal_total = int(status["total"])
    if opened.layout_source == "relayout" and "nodes.csv" in files:
        for row in _raw_rows(files["nodes.csv"]):
            if row.get("x_global") and row.get("y_global"):
                opened.relayout_positions[int(row["tag_id"])] = (float(row["x_global"]), float(row["y_global"]))
    if "removal_sensitivity.csv" in files:
        schema = S.REMOVAL_SENSITIVITY
        for row in _raw_rows(files["removal_sensitivity.csv"]):
            opened.removal_rows.append({c.name: parse_value(c.type, row.get(c.name, "")) for c in schema.columns})
    return opened


def _raw_rows(data: bytes) -> list[dict[str, str]]:
    import csv

    return list(csv.DictReader(io.StringIO(data.decode("utf-8-sig"))))


COORDINATE_COLUMNS = ("x_global", "y_global", "x_cluster_separated", "y_cluster_separated")


def recorded_table_hashes_match(opened: OpenedState, data: bytes) -> bool:
    """Whether the recomputed state's tables equal the export's (beyond the state_id check), every column except
    the four coordinate columns: positions come from the layout, which is not part of the state (ADR 0002)."""
    ctx = load_build(opened.build_path)
    _, again = export_zip(ctx, opened.settings, removal_rows=opened.removal_rows or None)
    files = read_export(again)[1]
    original = read_export(data)[1]
    return all(name in files and _coordinate_blind(files[name]) == _coordinate_blind(original[name])
               for name in original if name.endswith(".csv"))


def _coordinate_blind(data: bytes) -> list[list[tuple[str, str]]]:
    return [[(k, v) for k, v in row.items() if k not in COORDINATE_COLUMNS] for row in _raw_rows(data)]

"""The `steamstudy` command line: collect, snapshot, build, import, app, bundle."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from steamstudy import __version__

STAGES = ("pool", "history", "store", "taglist")


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="steamstudy", description="Steam Success Study pipeline and Tag Network app.")
    p.add_argument("--version", action="version", version=f"steamstudy {__version__}")
    p.add_argument("--config", type=Path, default=Path("config"), help="config directory (default: ./config)")
    p.add_argument("--root", type=Path, default=Path("."), help="folder holding snapshots/ and builds/ (default: .)")
    sub = p.add_subparsers(dest="command", required=True)

    c = sub.add_parser("collect", help="collect a Snapshot (all stages in order, resuming), or one stage")
    c.add_argument(
        "stage", nargs="?", choices=(*STAGES, "steamdb"), help="run one stage only, or the SteamDB cross-check"
    )
    c.add_argument("--mode", choices=("test", "full"), help="test or full Snapshot (required for a new Snapshot)")
    c.add_argument("--snapshot", help="Snapshot id to resume (default: the latest)")
    c.add_argument("--build", help="Build id (collect steamdb only)")
    c.add_argument("--repair", type=int, metavar="APPID", help="refetch one app into a closed Snapshot")
    c.add_argument("--reason", help="written reason for --repair")

    s = sub.add_parser("snapshot", help="Lightweight Snapshots: make or verify one")
    s_sub = s.add_subparsers(dest="snapshot_command", required=True)
    s_light = s_sub.add_parser("lighten", help="write snapshots/<id>.light.zip from a closed Snapshot")
    s_light.add_argument("snapshot_id", nargs="?", help="Snapshot id (default: the latest closed Snapshot)")
    s_verify = s_sub.add_parser("verify-light", help="build from both forms and compare every file")
    s_verify.add_argument("snapshot_id", help="Snapshot id")

    b = sub.add_parser("build", help="derive a Build from a Snapshot (offline)")
    b.add_argument("--snapshot", help="Snapshot id (default: the latest)")
    b.add_argument("--import", dest="import_id", metavar="IMPORT_ID",
                   help="build an Import instead: its defaults, or the reduced config set in --config when that "
                        "folder holds one")
    b.add_argument("--from-raw", action="store_true",
                   help="read the raw pages even when a Lightweight Snapshot is present")
    b.add_argument("--allow-parse-errors", action="store_true", help="treat parse errors as unscored (never published)")
    b.add_argument("--dataset", help="limit what is printed to one dataset (every dataset is always built)")
    b.add_argument("--name", help="the Build's name, unique per Snapshot ignoring case (default: its build_id)")

    i = sub.add_parser("import", help="import a CSV of items with ordered attributes as a fixed Import")
    i.add_argument("file", type=Path, help="the CSV: id,name,attributes[,score][,numeric fields...] (UTF-8)")
    i.add_argument("--filter", help="the numeric column the app's filter slider uses (filled for every item)")
    i.add_argument("--attributes", type=Path,
                   help="an attributes.csv (id,name) supplying attribute ids (default: attributes.csv beside the "
                        "file, when present)")

    a = sub.add_parser("app", help="open the Tag Network Workbench at http://127.0.0.1:<port>")
    a.add_argument("--build", help="Build id (default: the latest)")
    a.add_argument("--snapshot", help="Snapshot id (default: the latest)")
    a.add_argument("--port", type=int, default=8050)
    a.add_argument("--no-browser", action="store_true", help="do not open the browser")
    a.add_argument("--clear-cache", action="store_true", help="delete the Build's app cache and exit")

    n = sub.add_parser("bundle", help="write an App Bundle zip: the Tag Network app and Builds for offline use")
    n.add_argument("--build", action="append", required=True,
                   help="a Build to include: its id, <source_id>/<build_id>, its name, <source_id>/<name>, or latest "
                        "(repeatable; the first opens by default)")
    n.add_argument("--allow-test", action="store_true", help="allow Builds of test Snapshots")
    n.add_argument("--with-sources", action="store_true",
                   help="also ship each Build's lightweight Snapshot (or Import), config/ and the Build's libraries, "
                        "so the bundled app can make new Builds")
    n.add_argument("--target", action="append", default=[], choices=("windows", "macos", "linux"),
                   help="an operating system to make it for (repeatable; default: this computer's)")
    n.add_argument("--out", type=Path, help="folder for the zip (default: <root>/bundles)")
    n.add_argument("--validate-all-pairs", action="append", default=[], metavar="BUILD",
                   help="validate every Parameter Selection pair of this Build (named as in --build), not only each "
                        "dataset's default-constraint pair; hours of work, reused from the Build's app cache")
    n.add_argument("--skip-parameter-selection", action="store_true",
                   help="ship no Parameter Selection results (quick test bundles only; never for a release)")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-7s %(message)s", datefmt="%H:%M:%S")
    handler = {"collect": _collect, "snapshot": _snapshot, "build": _build, "import": _import, "app": _app,
               "bundle": _bundle}[args.command]
    return handler(args)


def _collect(args: argparse.Namespace) -> int:
    from steamstudy.collect.fetcher import HardStop
    from steamstudy.collect.run import CollectRefused, run_collect
    from steamstudy.config import ConfigError, load_config

    from steamstudy.collect.run import run_repair, run_steamdb

    log = logging.getLogger("steamstudy.collect")
    try:
        config = load_config(args.config)
        if args.stage == "steamdb":
            if not args.build:
                log.error("collect steamdb needs --build <id>")
                return 2
            record = run_steamdb(args.root, config, args.build)
            log.info("SteamDB batch %s: %s", record["batch"], record["outcomes"])
            return 0
        if args.repair is not None:
            repair = run_repair(args.root, config, args.repair, args.reason or "", snapshot_id=args.snapshot)
            log.info("repaired AppID %s: %s", args.repair, repair["outcomes"])
            return 0
        snapshot_id = run_collect(args.root, config, mode=args.mode, snapshot_id=args.snapshot, stage=args.stage)
    except (CollectRefused, ConfigError) as exc:
        log.error("collection refused: %s", exc)
        return 2
    except HardStop as exc:
        log.error("HARD STOP: %s. Rerun the same command to resume.", exc)
        return 3
    log.info("Snapshot %s: done", snapshot_id)
    return 0


def _snapshot(args: argparse.Namespace) -> int:
    from steamstudy.collect.run import snapshots_dir
    from steamstudy.config import ConfigError, load_config
    from steamstudy.lightweight import LightweightError, lighten, verify_light

    log = logging.getLogger("steamstudy.snapshot")
    base = snapshots_dir(args.root)
    try:
        if args.snapshot_command == "lighten":
            snapshot_id = args.snapshot_id or _latest_closed_snapshot_id(base)
            if snapshot_id is None:
                log.error("no closed Snapshot found under %s", base)
                return 2
            log.info("Lightweight Snapshot written to %s", lighten(base / snapshot_id))
            return 0
        diffs = verify_light(base, args.snapshot_id, load_config(args.config))
    except (LightweightError, ConfigError, OSError, ValueError) as exc:  # ValueError: a page that does not parse
        log.error("%s", exc)
        return 2
    for diff in diffs:
        log.error("%s", diff)
    if diffs:
        log.error("the lightweight form does not give the same Build as the raw form (%d file(s) differ)",
                  len(diffs))
        return 1
    log.info("Snapshot %s: a Build from the lightweight form is byte-identical to one from the raw form",
             args.snapshot_id)
    return 0


def _latest_closed_snapshot_id(base: Path) -> str | None:
    import json

    closed = []
    for path in base.iterdir() if base.is_dir() else ():
        meta_path = path / "snapshot.json"
        if meta_path.is_file():
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            if meta.get("closed"):
                closed.append((str(meta.get("created_at", "")), path.name))
    return max(closed)[1] if closed else None


def _build(args: argparse.Namespace) -> int:
    from steamstudy.build.core import BuildFailed, BuildIdentity, build, new_build_id
    from steamstudy.build.writer import write_build, write_failed_parse_errors
    from steamstudy.collect.run import snapshots_dir
    from steamstudy.config import ConfigError, load_config
    from steamstudy.lightweight import LightweightError, latest_source_snapshot_id, open_build_source

    log = logging.getLogger("steamstudy.build")
    if args.import_id:
        return _build_import(args, log)
    try:
        config = load_config(args.config)
    except ConfigError as exc:
        log.error("config: %s", exc)
        return 2
    snapshot_id = args.snapshot or latest_source_snapshot_id(snapshots_dir(args.root))
    if snapshot_id is None:
        log.error("no Snapshot found under %s", snapshots_dir(args.root))
        return 2
    try:
        opened = open_build_source(snapshots_dir(args.root), snapshot_id, from_raw=args.from_raw)
    except LightweightError as exc:
        log.error("Build refused: %s", exc)
        return 2
    for warning in opened.warnings:
        log.warning("%s", warning)
    source = opened.source
    if source.form == "raw" and not source.meta.get("closed"):
        log.warning("Snapshot %s is not closed: collection has not finished", snapshot_id)
    if args.name is not None:
        from steamstudy.build_admin import NameClash, check_name

        try:
            check_name(args.root, snapshot_id, args.name)
        except NameClash as exc:
            log.error("Build refused: %s", exc)
            return 2
    log.info("reading the %s form of Snapshot %s", source.form, snapshot_id)
    build_id = new_build_id(config)
    identity = BuildIdentity(name=args.name.strip() if args.name else None)
    try:
        result = build(source, config, build_id, allow_parse_errors=args.allow_parse_errors, identity=identity)
    except BuildFailed as exc:
        if exc.parse_errors:
            path = write_failed_parse_errors(args.root, snapshot_id, build_id, exc.parse_errors)
            log.error("Build failed: %s (written to %s)", exc, path)
        else:
            log.error("Build failed: %s", exc)
        return 1
    for warning in result.warnings:
        log.warning("%s", warning)
    folder = write_build(result, args.root)
    log.info("Build written to %s", folder)
    for key, size in result.build_json["dataset_sizes"].items():
        if args.dataset is None or args.dataset == key:
            print(f"{key}: {size['rows']} games (Eligible Pool {size['eligible_pool']})")
    if args.allow_parse_errors:
        log.warning("built with --allow-parse-errors: this Build must never be published")
    return 0


def _build_import(args: argparse.Namespace, log: logging.Logger) -> int:
    from steamstudy.build.core import BuildFailed, BuildIdentity, new_build_id
    from steamstudy.build.import_build import build_import, import_defaults, open_import, read_import_config_dir
    from steamstudy.build.writer import write_build
    from steamstudy.build_admin import NameClash, check_name
    from steamstudy.config import BUILD_FILES, ConfigError, canonical_json, content_hash

    try:
        source = open_import(args.root, args.import_id)
        files = read_import_config_dir(args.config) or import_defaults(source, args.config)
        if args.name is not None:
            check_name(args.root, args.import_id, args.name)
    except (FileNotFoundError, ConfigError, NameClash) as exc:
        log.error("Build refused: %s", exc)
        return 2
    normalised = json.loads(canonical_json(files))
    build_id = new_build_id(content_hash({n: normalised[n] for n in BUILD_FILES if n in normalised}))
    try:
        result = build_import(source, files, build_id,
                              identity=BuildIdentity(name=args.name.strip() if args.name else None))
    except BuildFailed as exc:
        log.error("Build failed: %s", exc)
        return 1
    folder = write_build(result, args.root)
    log.info("Build written to %s", folder)
    for key, size in result.build_json["dataset_sizes"].items():
        if args.dataset is None or args.dataset == key:
            print(f"{key}: {size['rows']} items (Eligible Pool {size['eligible_pool']})")
    return 0


def _import(args: argparse.Namespace) -> int:
    from collections import Counter

    from steamstudy.imports import ATTRIBUTES_FILE, ImportRefused, make_import

    log = logging.getLogger("steamstudy.import")
    attributes = args.attributes
    sibling = args.file.parent / ATTRIBUTES_FILE
    if attributes is None and sibling.is_file() and sibling.resolve() != args.file.resolve():
        attributes = sibling
        log.info("using attribute ids from %s", sibling)
    try:
        folder = make_import(args.root, args.file, attributes_file=attributes, filter_field=args.filter)
    except ImportRefused as exc:
        log.error("Import refused: %s", exc)
        for code, count in sorted(Counter(e.code for e in exc.errors).items()):
            print(f"{code}: {count}")
        for e in exc.errors[:20]:
            print(f"{e.file} row {e.row or '-'} {e.column or '-'} [{e.code}] {e.value!r}: {e.message}")
        return 2
    except OSError as exc:
        log.error("Import refused: %s", exc)
        return 2
    log.info("Import written to %s", folder)
    return 0


def _app(args: argparse.Namespace) -> int:
    from steamstudy.app import app_cache
    from steamstudy.builds import resolve_build

    log = logging.getLogger("steamstudy.app")
    try:
        folder = resolve_build(args.root, args.build, args.snapshot)
    except FileNotFoundError as exc:
        log.error("%s", exc)
        return 2
    if args.clear_cache:
        counts = app_cache.clear_all(folder / "app_cache")
        log.info("%s (%s)", app_cache.cleared_text(counts), folder / "app_cache")
        return 0
    from steamstudy.app.server import run

    log.info("opening Build %s", folder)
    run(folder, port=args.port, open_browser=not args.no_browser)
    return 0


def _bundle(args: argparse.Namespace) -> int:
    from steamstudy.bundle.make import BundleError, make_bundle

    log = logging.getLogger("steamstudy.bundle")
    try:
        path = make_bundle(args.root, builds=args.build, targets=args.target, out=args.out,
                           skip_parameter_selection=args.skip_parameter_selection, allow_test=args.allow_test,
                           with_sources=args.with_sources, validate_all=args.validate_all_pairs)
    except BundleError as exc:
        log.error("bundle not written: %s", exc)
        return 2
    log.info("App Bundle written to %s (%.0f MB)", path, path.stat().st_size / 1e6)
    return 0


if __name__ == "__main__":
    sys.exit(main())

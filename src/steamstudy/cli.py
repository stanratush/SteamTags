"""The `steamstudy` command line: collect, build, app."""

from __future__ import annotations

import argparse
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

    b = sub.add_parser("build", help="derive a Build from a Snapshot (offline)")
    b.add_argument("--snapshot", help="Snapshot id (default: the latest)")
    b.add_argument("--allow-parse-errors", action="store_true", help="treat parse errors as unscored (never published)")
    b.add_argument("--dataset", help="limit what is printed to one dataset (all five are always built)")

    a = sub.add_parser("app", help="open the Tag Network Workbench at http://127.0.0.1:<port>")
    a.add_argument("--build", help="Build id (default: the latest)")
    a.add_argument("--snapshot", help="Snapshot id (default: the latest)")
    a.add_argument("--port", type=int, default=8050)
    a.add_argument("--no-browser", action="store_true", help="do not open the browser")
    a.add_argument("--clear-cache", action="store_true", help="delete the Build's app cache and exit")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    handler = {"collect": _collect, "build": _build, "app": _app}[args.command]
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


def _build(args: argparse.Namespace) -> int:
    from steamstudy.build.core import BuildFailed, build, new_build_id
    from steamstudy.build.writer import write_build, write_failed_parse_errors
    from steamstudy.collect.run import latest_snapshot_id, snapshots_dir
    from steamstudy.config import ConfigError, load_config
    from steamstudy.snapshot import Snapshot

    log = logging.getLogger("steamstudy.build")
    try:
        config = load_config(args.config)
    except ConfigError as exc:
        log.error("config: %s", exc)
        return 2
    snapshot_id = args.snapshot or latest_snapshot_id(args.root)
    if snapshot_id is None:
        log.error("no Snapshot found under %s", snapshots_dir(args.root))
        return 2
    snapshot = Snapshot(snapshots_dir(args.root) / snapshot_id)
    if not snapshot.meta.get("closed"):
        log.warning("Snapshot %s is not closed: collection has not finished", snapshot_id)
    build_id = new_build_id(config)
    try:
        result = build(snapshot, config, build_id, allow_parse_errors=args.allow_parse_errors)
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
    if args.allow_parse_errors:
        log.warning("built with --allow-parse-errors: this Build must never be published")
    return 0


def _app(args: argparse.Namespace) -> int:
    from steamstudy.app import rs_cache
    from steamstudy.build.writer import resolve_build

    log = logging.getLogger("steamstudy.app")
    try:
        folder = resolve_build(args.root, args.build, args.snapshot)
    except FileNotFoundError as exc:
        log.error("%s", exc)
        return 2
    if args.clear_cache:
        removed = rs_cache.clear(folder / "app_cache")
        log.info("cleared %d cached Removal Sensitivity result(s) in %s", removed, folder / "app_cache")
        return 0
    from steamstudy.app.server import run

    log.info("opening Build %s", folder)
    run(folder, port=args.port, open_browser=not args.no_browser)
    return 0


if __name__ == "__main__":
    sys.exit(main())

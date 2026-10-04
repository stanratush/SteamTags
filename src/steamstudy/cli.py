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
    print("collect: not implemented yet", file=sys.stderr)
    return 2


def _build(args: argparse.Namespace) -> int:
    print("build: not implemented yet", file=sys.stderr)
    return 2


def _app(args: argparse.Namespace) -> int:
    print("app: not implemented yet", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())

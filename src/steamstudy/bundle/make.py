"""`steamstudy bundle`: write one App Bundle zip (ADR 0001).

The zip holds the launcher and its double-click wrappers, `READ ME FIRST.txt`, the User Guide, the app-only
`steamstudy` wheel, every dependency wheel each target needs for Python 3.12-3.14 (pinned to `uv.lock`,
hash-checked, pure-Python wheels stored once), per-target requirement files with hashes, the chosen Build
folders (without the maker's `app_cache/`) with `latest` pointers, and `bundle.json`. Making a bundle needs internet
(to fetch wheels); using one never does. On any failure nothing is written.

Every carried Build ships its Parameter Selection results under the shipped code's default Selection Settings (each
dataset's grid and the default-constraint pair's validation), always recomputed into the staging Build; the maker's
own cache is only compared with them, never shipped or modified.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import logging
import platform
import shutil
import subprocess
import tempfile
import urllib.request
import zipfile
from collections.abc import Callable, Iterable, Sequence
from pathlib import Path
from typing import Any

from steamstudy import __version__
from steamstudy.builds import resolve_build
from steamstudy.i18n import text
from steamstudy.bundle import start_tag_network as launcher
from steamstudy.bundle.wheels import PYTHONS, TARGETS, Wheel, plan, read_lock, requirements

BUNDLE_FORMAT = 1
REPO = Path(__file__).resolve().parents[3]
FILES = Path(__file__).resolve().parent / "files"
EXECUTABLE = 0o100755 << 16
REGULAR = 0o100644 << 16
# Windows Explorer shows a zip as empty ("the compressed folder is invalid") when any entry path has 260 characters
# or more, and Windows without long-path support cannot open a longer file at all. The margin leaves room to extract
# into a short folder such as C:\TagNetwork\.
MAX_ENTRY_PATH = 240


log = logging.getLogger("steamstudy.bundle")


class BundleError(Exception):
    pass


def _comparable(path: Path) -> str | None:
    """A cache file's content without timings and `computed_with`."""
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    for key in ("seconds", "computed_with"):
        data.pop(key, None)
    return json.dumps(data, sort_keys=True)


def stale_files(fresh: Path, maker: Path) -> list[str]:
    """Cache files the maker's cache holds under the same keys whose content differs from the fresh result."""
    out = []
    for path in sorted(fresh.rglob("*.json")):
        relative = path.relative_to(fresh)
        if path.name == "manifest.json" and not json.loads((maker / relative).read_text(encoding="utf-8")
                                                            if (maker / relative).is_file() else "{}").get("complete"):
            continue  # a cancelled or partial grid in the maker's cache: only its graph files compare
        mine = _comparable(maker / relative)
        if mine is not None and mine != _comparable(path):
            out.append(relative.as_posix())
    return out


def ship_parameter_selection(source: Path, staged: Path, map_fn: Callable[..., Iterable[Any]]) -> dict[str, Any]:
    """Run Parameter Selection for the staged Build under the default Selection Settings into its app cache, compare
    with the maker's cache and return what shipped (grid and validation key hashes)."""
    from steamstudy.app import ps_cache, ps_run
    from steamstudy.app.loader import load_build
    from steamstudy.network import selection as SEL

    ctx = load_build(staged)
    settings = SEL.load_selection_settings(ctx.network, (t.id for t in ctx.genre_tags), ctx.build_id)
    reported: set[tuple[str, str]] = set()

    def progress(record: dict[str, Any]) -> None:
        key = (record["dataset"], record["phase"])
        if record["done"] >= record["total"] and key not in reported:
            reported.add(key)
            unit = "pairs" if record["phase"] == "grid" else "replicates"
            log.info("Build %s, %s: %s %d of %d %s, %s", staged.name, record["dataset"], record["phase"],
                     record["done"], record["total"], unit, ps_run.eta_text(record, text("en")))

    datasets = [d.key for d in ctx.datasets]
    outcomes = ps_run.run(ctx, settings, datasets, map_fn=map_fn, on_progress=progress,
                          cache_root=staged / "app_cache")
    stale = stale_files(ps_cache.root(staged / "app_cache"), ps_cache.root(source / "app_cache"))
    if stale:
        log.warning("Build %s: the maker's Parameter Selection cache differs from the fresh result in %d file(s) "
                    "(%s): it is stale, and a method version probably needed a bump. The fresh result ships.",
                    staged.name, len(stale), ", ".join(stale[:3]) + (", …" if len(stale) > 3 else ""))
    grids = [SEL.key_hash(settings.grid_key(d, ctx.context(d))) for d in datasets]
    validations = [SEL.key_hash(settings.validation_key(o.dataset, ctx.context(o.dataset), *o.chosen))
                   for o in outcomes if o.chosen is not None]
    return {"settings_key_hash": SEL.key_hash(settings.settings_key()), "grids": grids, "validations": validations}


def current_target() -> str:
    target = launcher.target_name(platform.system(), platform.machine())
    if target is None:
        raise BundleError(f"this computer ({platform.system()} {platform.machine()}) is not a bundle target; "
                          f"pass --target ({', '.join(TARGETS)})")
    return target


def fetch_wheel(wheel: Wheel, cache: Path) -> Path:
    """The wheel from the cache, or downloaded from its locked URL; its sha256 must match the lock."""
    path = cache / wheel.filename
    if path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == wheel.sha256:
        return path
    try:
        with urllib.request.urlopen(wheel.url, timeout=120) as response:
            data = response.read()
    except OSError as exc:
        raise BundleError(f"could not fetch {wheel.filename} ({exc}); making a bundle needs internet") from exc
    if hashlib.sha256(data).hexdigest() != wheel.sha256:
        raise BundleError(f"{wheel.filename} does not match its hash in uv.lock")
    cache.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def build_steamstudy_wheel(repo: Path, out: Path) -> Path:
    """The app-only `steamstudy` wheel (its metadata lists only the app's dependencies)."""
    done = subprocess.run(["uv", "build", "--wheel", "--out-dir", str(out), str(repo)], capture_output=True,
                          text=True, encoding="utf-8")
    wheels = sorted(out.glob("steamstudy-*.whl"))
    if done.returncode != 0 or not wheels:
        raise BundleError(f"could not build the steamstudy wheel: {done.stderr[-1000:]}")
    return wheels[-1]


def make_bundle(root: Path, *, builds: Sequence[str] = (), targets: Sequence[str] = (), out: Path | None = None,
                repo: Path = REPO, lock_path: Path | None = None, cache: Path | None = None,
                fetch: Callable[[Wheel, Path], Path] = fetch_wheel,
                build_wheel: Callable[[Path, Path], Path] = build_steamstudy_wheel,
                now: dt.datetime | None = None, skip_parameter_selection: bool = False,
                map_fn: Callable[..., Iterable[Any]] | None = None) -> Path:
    """Write `<out>/tag-network-<build_id>-<targets>.zip` and return its path. `skip_parameter_selection` makes a
    bundle without Parameter Selection results (test bundles only, never a release); `map_fn` replaces the worker
    pool (tests)."""
    root = Path(root)
    targets = list(dict.fromkeys(targets or [current_target()]))
    for name in targets:
        if name not in TARGETS:
            raise BundleError(f"unknown target {name!r} (choose from {', '.join(TARGETS)})")
    try:
        folders = list(dict.fromkeys([resolve_build(root)] + [resolve_build(root, b) for b in builds]))
    except FileNotFoundError as exc:
        raise BundleError(str(exc)) from exc
    lock_path = lock_path or repo / "uv.lock"
    wheel_plan = plan(read_lock(lock_path), targets)
    if not wheel_plan.complete:
        listed = "; ".join(f"{p} {v} for {t} / Python {py}" for p, v, t, py in wheel_plan.missing)
        raise BundleError(f"no wheel in uv.lock for: {listed}")
    out = Path(out) if out else root / "bundles"
    cache = cache or out / ".cache" / "wheels"
    now = now or dt.datetime.now(dt.UTC)
    first = folders[0]
    name = f"tag-network-{first.name}-{'-'.join(targets)}"
    with tempfile.TemporaryDirectory() as tmp:
        stage = Path(tmp) / name
        (stage / "wheels").mkdir(parents=True)
        for wheel in wheel_plan.all_wheels():
            shutil.copy2(fetch(wheel, cache), stage / "wheels" / wheel.filename)
        own = build_wheel(repo, Path(tmp) / "dist")
        shutil.copy2(own, stage / "wheels" / own.name)
        own_line = f"steamstudy=={__version__} --hash=sha256:{hashlib.sha256(own.read_bytes()).hexdigest()}"
        (stage / "requirements").mkdir()
        for (target, python), per in sorted(wheel_plan.wheels.items()):
            (stage / "requirements" / f"{target}-py{python[0]}.{python[1]}.txt").write_text(
                requirements(per, [own_line]), encoding="utf-8")
        shipped: dict[str, Any] = {}
        for folder in folders:
            dest = stage / "builds" / folder.parent.name / folder.name
            shutil.copytree(folder, dest, ignore=shutil.ignore_patterns("app_cache"))
            (dest.parent / "latest").write_text(folder.name + "\n", encoding="utf-8")
            build_ref = f"{folder.parent.name}/{folder.name}"
            if skip_parameter_selection:
                shipped[build_ref] = "skipped"
            elif map_fn is not None:
                shipped[build_ref] = ship_parameter_selection(folder, dest, map_fn)
            else:
                shipped[build_ref] = _ship_with_pool(folder, dest)
        (stage / "builds" / "latest").write_text(f"{first.parent.name}/{first.name}\n", encoding="utf-8")
        (stage / "builds" / first.parent.name / "latest").write_text(first.name + "\n", encoding="utf-8")
        shutil.copytree(repo / "docs" / "user-guide", stage / "User Guide")
        shutil.copy2(Path(launcher.__file__), stage / "start_tag_network.py")
        shutil.copy2(FILES / "Start Tag Network.bat", stage / "Start Tag Network.bat")
        command = (FILES / "Start Tag Network.command").read_bytes().replace(b"\r\n", b"\n")
        (stage / "Start Tag Network.command").write_bytes(command)
        manifest = {
            "bundle_format": BUNDLE_FORMAT, "steamstudy_version": __version__,
            "uv_lock_sha256": hashlib.sha256(lock_path.read_bytes()).hexdigest(), "targets": targets,
            "python_versions": [f"{a}.{b}" for a, b in PYTHONS], "excluded_python_versions": ["3.14.1"],
            "builds": [f"{f.parent.name}/{f.name}" for f in folders], "latest_build": first.name,
            "created_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "parameter_selection": shipped,
        }
        (stage / "bundle.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
        readme = (FILES / "READ ME FIRST.txt").read_text(encoding="utf-8").format(
            builds="\n".join(f"  {f.parent.name}/{f.name}" + ("  (opens by default)" if i == 0 else "")
                             for i, f in enumerate(folders)),
            targets=", ".join(TARGETS[t].label() for t in targets), created=now.strftime("%Y-%m-%d"),
            version=__version__)
        (stage / "READ ME FIRST.txt").write_text(readme, encoding="utf-8")
        longest = max((str(Path(name) / p.relative_to(stage)).replace("\\", "/") for p in stage.rglob("*")
                       if p.is_file()), key=len)
        if len(longest) > MAX_ENTRY_PATH:
            raise BundleError(f"a path in the zip has {len(longest)} characters, more than {MAX_ENTRY_PATH}: Windows "
                              f"Explorer could not open the bundle ({longest})")
        out.mkdir(parents=True, exist_ok=True)
        target_zip = out / f"{name}.zip"
        partial = target_zip.with_suffix(".zip.partial")
        try:
            with zipfile.ZipFile(partial, "w", zipfile.ZIP_DEFLATED) as zf:
                for path in sorted(p for p in stage.rglob("*") if p.is_file()):
                    info = zipfile.ZipInfo(str(Path(name) / path.relative_to(stage)).replace("\\", "/"),
                                           date_time=now.timetuple()[:6])
                    info.external_attr = EXECUTABLE if path.suffix in (".command", ".py") and path.parent == stage \
                        else REGULAR
                    info.compress_type = zipfile.ZIP_STORED if path.suffix == ".whl" else zipfile.ZIP_DEFLATED
                    zf.writestr(info, path.read_bytes())
            partial.replace(target_zip)
        finally:
            partial.unlink(missing_ok=True)  # never leave a half-written zip behind
    return target_zip


def _ship_with_pool(source: Path, staged: Path) -> dict[str, Any]:
    """`ship_parameter_selection` through a pool of `[parameter_selection] workers` (0 = cpu - 1)."""
    import multiprocess as mp

    from steamstudy.app import ps_run
    from steamstudy.app.loader import load_build

    workers = ps_run.worker_count(load_build(staged).network.parameter_selection.workers)
    with mp.Pool(workers) as pool:
        return ship_parameter_selection(source, staged, pool.imap_unordered)

"""`steamstudy bundle`: write one App Bundle zip (ADR 0001).

The zip holds the launcher and its double-click wrappers, `READ ME FIRST.txt`, the User Guide, the app-only
`steamstudy` wheel, every dependency wheel each target needs for Python 3.12-3.14 (pinned to `uv.lock`,
hash-checked, pure-Python wheels stored once), per-target requirement files with hashes, the chosen Build
folders (without `app_cache/`) with `latest` pointers, and `bundle.json`. Making a bundle needs internet (to
fetch wheels); using one never does. On any failure nothing is written.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import platform
import shutil
import subprocess
import tempfile
import urllib.request
import zipfile
from collections.abc import Callable, Sequence
from pathlib import Path

from steamstudy import __version__
from steamstudy.builds import resolve_build
from steamstudy.bundle import start_tag_network as launcher
from steamstudy.bundle.wheels import PYTHONS, TARGETS, Wheel, plan, read_lock, requirements

BUNDLE_FORMAT = 1
REPO = Path(__file__).resolve().parents[3]
FILES = Path(__file__).resolve().parent / "files"
EXECUTABLE = 0o100755 << 16
REGULAR = 0o100644 << 16


class BundleError(Exception):
    pass


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
                now: dt.datetime | None = None) -> Path:
    """Write `<out>/tag-network-<build_id>-<targets>.zip` and return its path."""
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
        for folder in folders:
            dest = stage / "builds" / folder.parent.name / folder.name
            shutil.copytree(folder, dest, ignore=shutil.ignore_patterns("app_cache"))
            (dest.parent / "latest").write_text(folder.name + "\n", encoding="utf-8")
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
            "created_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        (stage / "bundle.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
        readme = (FILES / "READ ME FIRST.txt").read_text(encoding="utf-8").format(
            builds="\n".join(f"  {f.parent.name}/{f.name}" + ("  (opens by default)" if i == 0 else "")
                             for i, f in enumerate(folders)),
            targets=", ".join(TARGETS[t].label() for t in targets), created=now.strftime("%Y-%m-%d"),
            version=__version__)
        (stage / "READ ME FIRST.txt").write_text(readme, encoding="utf-8")
        out.mkdir(parents=True, exist_ok=True)
        target_zip = out / f"{name}.zip"
        partial = target_zip.with_suffix(".zip.partial")
        with zipfile.ZipFile(partial, "w", zipfile.ZIP_DEFLATED) as zf:
            for path in sorted(p for p in stage.rglob("*") if p.is_file()):
                info = zipfile.ZipInfo(str(Path(name) / path.relative_to(stage)).replace("\\", "/"),
                                       date_time=now.timetuple()[:6])
                info.external_attr = EXECUTABLE if path.suffix in (".command", ".py") and path.parent == stage \
                    else REGULAR
                info.compress_type = zipfile.ZIP_STORED if path.suffix == ".whl" else zipfile.ZIP_DEFLATED
                zf.writestr(info, path.read_bytes())
        partial.replace(target_zip)
    return target_zip

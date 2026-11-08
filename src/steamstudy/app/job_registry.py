"""Which background jobs run on which Build, so that deleting a Build can cancel them first.

Removal Sensitivity and Parameter Selection jobs run in the background-callback manager's own processes. Each
records itself here while it runs: a small file named by its process id, holding the Build's ref, in the app
process's temporary job store (`server.job_store`; the folder reaches the job processes through an environment
variable, as the builds root does). Deleting a Build stops the processes recorded for it (and their worker
processes), so that none still holds a file of the folder about to be removed (on Windows an open cache file
blocks the delete).
"""

from __future__ import annotations

import functools
import json
import os
import secrets
import signal
import subprocess
import sys
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

ENV = "STEAMSTUDY_JOB_REGISTRY"


def set_folder(folder: Path) -> None:
    path = Path(folder) / "running"
    path.mkdir(parents=True, exist_ok=True)
    os.environ[ENV] = str(path)


def _folder() -> Path | None:
    value = os.environ.get(ENV)
    return Path(value) if value else None


def _ref(build_path: Any) -> str:
    from steamstudy.app.loader import build_folder, ref_of

    return ref_of(build_folder(build_path))


@contextmanager
def running(build_path: Any) -> Iterator[None]:
    """Record the calling process as a job on this Build while the block runs."""
    folder = _folder()
    if folder is None:
        yield
        return
    path = folder / f"{os.getpid()}-{secrets.token_hex(4)}.json"
    path.write_text(json.dumps({"pid": os.getpid(), "ref": _ref(build_path)}), encoding="utf-8")
    try:
        yield
    finally:
        path.unlink(missing_ok=True)


def tracked(job: Callable[..., Any]) -> Callable[..., Any]:
    """A background job `(set_progress, request, build_path, ...)` recorded on its Build while it runs."""

    @functools.wraps(job)
    def run(set_progress: Any, request: Any, build_path: Any, *args: Any, **kwargs: Any) -> Any:
        with running(build_path):
            return job(set_progress, request, build_path, *args, **kwargs)

    return run


def jobs_on(ref: str) -> list[tuple[Path, int]]:
    """(record, process id) of every job recorded on this Build."""
    folder = _folder()
    found = []
    for path in sorted(folder.glob("*.json")) if folder is not None and folder.is_dir() else []:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if data.get("ref") == ref:
            found.append((path, int(data["pid"])))
    return found


def cancel_jobs_on(ref: str) -> int:
    """Stop every job running on this Build, with its worker processes; returns how many were stopped."""
    jobs = jobs_on(ref)
    for path, pid in jobs:
        if pid != os.getpid():
            _stop(pid)
        path.unlink(missing_ok=True)
    return len(jobs)


def _stop(pid: int) -> None:
    """Stop a job's process and every process under it (a Parameter Selection run's worker pool)."""
    if sys.platform == "win32":
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True, check=False)
        return
    tree = [pid, *_descendants(pid)]  # found first: once the job stops, its workers are no longer its children
    for each in tree:
        try:
            os.kill(each, signal.SIGTERM)
        except ProcessLookupError:
            pass


def _descendants(pid: int) -> list[int]:
    """The processes under `pid`, children before their own children (`pgrep -P`, on Linux and macOS)."""
    try:
        out = subprocess.run(["pgrep", "-P", str(pid)], capture_output=True, text=True, check=False).stdout
    except FileNotFoundError:  # no pgrep: only the job itself is stopped
        return []
    found: list[int] = []
    for child in (int(word) for word in out.split()):
        found += [child, *_descendants(child)]
    return found

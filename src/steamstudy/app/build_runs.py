"""Build runs from drafts: a server-wide job, one at a time per app process, in a background thread.

A run is started from a draft's Review step and is shown in every tab (the strip under the header) until it is
dismissed. Switching or closing a tab never cancels it; Cancel does (between stages). A second run waits for the
first. `build_admin.build_draft` does the work: on success the draft becomes a Build, on failure the draft keeps the
failure.

The estimate is about 24 s from a lightweight Snapshot and about 99 s from raw (issue 17's measurements); an Import
is treated as lightweight.
"""

from __future__ import annotations

import threading
import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ESTIMATE_LIGHT_S = 24
ESTIMATE_RAW_S = 99


@dataclass
class Run:
    run_id: int
    root: Path
    source_id: str
    slug: str
    name: str
    estimate_s: int
    status: str = "waiting"  # waiting | running | done | failed | cancelled
    kind: str = "build"  # "build" (a draft) or "lighten" (Make lightweight Snapshot)
    stage: str = ""
    started: float | None = None
    finished: float | None = None
    ref: str | None = None  # the new Build's ref on success
    error: str | None = None
    stop: threading.Event = field(default_factory=threading.Event)

    def view(self) -> dict[str, Any]:
        now = self.finished or time.time()
        return {"run_id": self.run_id, "kind": self.kind, "source_id": self.source_id, "slug": self.slug, "name": self.name,
                "status": self.status, "stage": self.stage, "estimate_s": self.estimate_s,
                "elapsed_s": round(now - self.started) if self.started else 0, "ref": self.ref, "error": self.error,
                "started": self.started, "finished": self.finished}


_LOCK = threading.Lock()
_RUNS: dict[int, Run] = {}
_QUEUE: deque[int] = deque()
_WORKER: threading.Thread | None = None
_NEXT = [1]


def estimate(root: Path, source_id: str) -> int:
    from steamstudy.imports import is_import
    from steamstudy.builds import light_path

    if is_import(root, source_id) or light_path(root / "snapshots", source_id).is_file():
        return ESTIMATE_LIGHT_S
    return ESTIMATE_RAW_S


def start(root: Path, source_id: str, slug: str, name: str) -> int:
    """Queue a draft's Build run; it starts when no other run is running. Returns its id."""
    with _LOCK:
        for run in _RUNS.values():  # the same draft is never queued twice
            if (run.source_id, run.slug) == (source_id, slug) and run.status in ("waiting", "running"):
                return run.run_id
        run_id = _NEXT[0]
        _NEXT[0] += 1
        _enqueue(Run(run_id, Path(root), source_id, slug, name, estimate(Path(root), source_id)))
    return run_id


def start_lighten(root: Path, snapshot_id: str) -> int:
    """Queue Make lightweight Snapshot (a server job like a Build run, shown on the same strip)."""
    with _LOCK:
        run_id = _NEXT[0]
        _NEXT[0] += 1
        _enqueue(Run(run_id, Path(root), snapshot_id, "", snapshot_id, 60, kind="lighten"))
    return run_id


def _enqueue(run: Run) -> None:
    """Queue a run and start the worker if none is working (call with `_LOCK` held)."""
    global _WORKER
    _RUNS[run.run_id] = run
    _QUEUE.append(run.run_id)
    if _WORKER is None:  # the worker clears it, under the lock, when it finds the queue empty
        _WORKER = threading.Thread(target=_work, name="build-runs", daemon=True)
        _WORKER.start()


def cancel(run_id: int) -> None:
    with _LOCK:
        run = _RUNS.get(run_id)
        if run is None:
            return
        if run.status == "waiting":
            run.status, run.finished = "cancelled", time.time()
            if run_id in _QUEUE:
                _QUEUE.remove(run_id)
        run.stop.set()


def dismiss(run_id: int) -> None:
    with _LOCK:
        run = _RUNS.get(run_id)
        if run is not None and run.status not in ("waiting", "running"):
            del _RUNS[run_id]


def runs() -> list[dict[str, Any]]:
    with _LOCK:
        return [r.view() for r in sorted(_RUNS.values(), key=lambda r: r.run_id)]


def running_draft(source_id: str, slug: str) -> dict[str, Any] | None:
    """The waiting or running run of a draft (the tree's "running %"), if any."""
    for view in runs():
        if (view["source_id"], view["slug"]) == (source_id, slug) and view["status"] in ("waiting", "running"):
            return view
    return None


def wait_idle(timeout: float = 300.0) -> bool:
    """Block until no run is waiting or running (tests)."""
    end = time.time() + timeout
    while time.time() < end:
        if not any(v["status"] in ("waiting", "running") for v in runs()):
            return True
        time.sleep(0.1)
    return False


def _work() -> None:
    global _WORKER
    from steamstudy.build_admin import BuildCancelled, BuildFailed, build_draft, list_drafts

    while True:
        with _LOCK:
            if not _QUEUE:
                _WORKER = None  # a run queued from now on starts a new worker
                return
            run = _RUNS[_QUEUE.popleft()]
            run.status, run.started = "running", time.time()

        def progress(stage: str, run: Run = run) -> None:
            run.stage = stage

        try:
            if run.kind == "lighten":
                from steamstudy.lightweight import lighten

                run.stage = "lighten"
                lighten(run.root / "snapshots" / run.source_id)
                run.status, run.finished = "done", time.time()
                continue
            draft = next((d for d in list_drafts(run.root, run.source_id) if d.stored_slug == run.slug), None)
            if draft is None:
                raise BuildFailed(f"the draft {run.name} no longer exists")
            folder = build_draft(run.root, draft, on_progress=progress, should_stop=run.stop.is_set)
            run.status, run.ref = "done", f"{folder.parent.name}/{folder.name}"
        except BuildCancelled:
            run.status = "cancelled"
        except BuildFailed as exc:
            run.status, run.error = "failed", str(exc)
        except Exception as exc:  # noqa: BLE001 - a run never takes the server down; the draft keeps what it can
            run.status, run.error = "failed", f"{type(exc).__name__}: {exc}"
        run.finished = time.time()

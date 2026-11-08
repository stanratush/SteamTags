"""Build runs from drafts: a server-wide job, one at a time per app process, each in its own process.

A run is started from a draft's Review step and is shown in every tab (the strip under the header) until it is
dismissed. Switching or closing a tab never cancels it; Cancel does (between stages). A second run waits for the
first. A worker thread of the app process starts each run's process and relays its stages, so a Build never holds
the server's interpreter. `build_admin.build_draft` does the work: on success the draft becomes a Build, on failure
the draft keeps the failure.

The estimate is about 24 s from a lightweight Snapshot and about 99 s from raw (issue 17's measurements); an Import
is treated as lightweight.
"""

from __future__ import annotations

import multiprocessing
import queue
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from steamstudy.build_admin import DraftRef
from steamstudy.builds import ref_of

ESTIMATE_LIGHT_S = 24
ESTIMATE_RAW_S = 99
ESTIMATE_LIGHTEN_S = 60
ACTIVE = ("waiting", "running")  # a run's statuses before it ends (then: done, failed or cancelled)


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

    @property
    def active(self) -> bool:
        return self.status in ACTIVE

    @property
    def draft(self) -> DraftRef:
        return DraftRef(self.source_id, self.slug)

    def view(self) -> dict[str, Any]:
        """The run as the strip and the tree read it (plain values: it crosses the callback boundary)."""
        elapsed = round((self.finished or time.time()) - self.started) if self.started else 0
        return {"run_id": self.run_id, "kind": self.kind, "source_id": self.source_id, "slug": self.slug, "name": self.name,
                "status": self.status, "active": self.active, "stage": self.stage, "estimate_s": self.estimate_s,
                "elapsed_s": elapsed, "pct": min(99, round(100 * elapsed / max(self.estimate_s, 1))),
                "ref": self.ref, "error": self.error, "started": self.started, "finished": self.finished}


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


def start(root: Path, draft: DraftRef, name: str) -> int:
    """Queue a draft's Build run; it starts when no other run is running. Returns its id."""
    with _LOCK:
        for run in _RUNS.values():  # the same draft is never queued twice
            if run.draft == draft and run.active:
                return run.run_id
        run_id = _NEXT[0]
        _NEXT[0] += 1
        _enqueue(Run(run_id, Path(root), draft.source_id, draft.slug, name, estimate(Path(root), draft.source_id)))
    return run_id


def start_lighten(root: Path, snapshot_id: str) -> int:
    """Queue Make lightweight Snapshot (a server job like a Build run, shown on the same strip)."""
    with _LOCK:
        run_id = _NEXT[0]
        _NEXT[0] += 1
        _enqueue(Run(run_id, Path(root), snapshot_id, "", snapshot_id, ESTIMATE_LIGHTEN_S, kind="lighten"))
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
        if run is not None and not run.active:
            del _RUNS[run_id]


def runs() -> list[dict[str, Any]]:
    with _LOCK:
        return [r.view() for r in sorted(_RUNS.values(), key=lambda r: r.run_id)]


def running_draft(draft: DraftRef) -> dict[str, Any] | None:
    """The waiting or running run of a draft (the tree's "running %"), if any."""
    with _LOCK:
        run = next((r for r in _RUNS.values() if r.draft == draft and r.active), None)
        return run.view() if run else None


def wait_idle(timeout: float = 300.0) -> bool:
    """Block until no run is waiting or running (tests)."""
    end = time.time() + timeout
    while time.time() < end:
        if not any(v["active"] for v in runs()):
            return True
        time.sleep(0.1)
    return False


def _work() -> None:
    """The queue's worker thread: each run in its own process, one at a time."""
    global _WORKER
    while True:
        with _LOCK:
            if not _QUEUE:
                _WORKER = None  # a run queued from now on starts a new worker
                return
            run = _RUNS[_QUEUE.popleft()]
            run.status, run.started = "running", time.time()
        status, value = _in_process(run)
        run.status = status
        if status == "done":
            run.ref = value
        elif status == "failed":
            run.error = value
        run.finished = time.time()


def _in_process(run: Run) -> tuple[str, str | None]:
    """Run one Build (or Make lightweight Snapshot) in a child process; its stages reach `run.stage`, and Cancel
    reaches it as an event it checks between stages. Returns (status, the new Build's ref or the error)."""
    context = multiprocessing.get_context("spawn")
    messages = context.Queue()
    stop = context.Event()
    child = context.Process(target=run_child, args=(run.kind, str(run.root), run.source_id, run.slug, run.name,
                                                    messages, stop), name=f"build-run-{run.run_id}")
    child.start()
    try:
        while True:
            if run.stop.is_set():
                stop.set()
            try:
                kind, value = messages.get(timeout=0.2)
            except queue.Empty:
                if child.is_alive():
                    continue
                try:  # the last message may arrive just after the child ended
                    kind, value = messages.get(timeout=1.0)
                except queue.Empty:
                    return "failed", f"the Build process ended without a result (exit code {child.exitcode})"
            if kind == "stage":
                run.stage = value
            else:
                return kind, value
    finally:
        child.join(timeout=10)
        messages.close()


def run_child(kind: str, root: str, source_id: str, slug: str, name: str, messages: Any, stop: Any) -> None:
    """The child process: build the draft (or lighten the Snapshot) and report stages, then one result:
    ("done", ref), ("failed", message) or ("cancelled", None). Never raises."""
    from steamstudy.build_admin import BuildCancelled, BuildFailed, build_draft, find_draft

    try:
        if kind == "lighten":
            from steamstudy.lightweight import lighten

            messages.put(("stage", "lighten"))
            lighten(Path(root) / "snapshots" / source_id)
            messages.put(("done", None))
            return
        draft = find_draft(Path(root), DraftRef(source_id, slug))
        if draft is None:
            raise BuildFailed(f"the draft {name} no longer exists")
        folder = build_draft(Path(root), draft, on_progress=lambda stage: messages.put(("stage", stage)),
                             should_stop=stop.is_set)
        messages.put(("done", ref_of(folder)))
    except BuildCancelled:
        messages.put(("cancelled", None))
    except BuildFailed as exc:
        messages.put(("failed", str(exc)))
    except Exception as exc:  # noqa: BLE001 - the parent reports it; the draft keeps what build_draft saved
        messages.put(("failed", f"{type(exc).__name__}: {exc}"))

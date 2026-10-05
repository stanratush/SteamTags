"""Progress feedback for long collection stages: periodic log lines with counts and a time estimate."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable

log = logging.getLogger("steamstudy.collect")


def duration(seconds: float) -> str:
    seconds = max(0, int(seconds))
    hours, rest = divmod(seconds, 3600)
    minutes, secs = divmod(rest, 60)
    if hours:
        return f"{hours}h {minutes:02d}m"
    if minutes:
        return f"{minutes}m {secs:02d}s"
    return f"{secs}s"


class Progress:
    """Counts items of one stage and logs a line at most every `every` seconds (and at the end).

    Items already collected in an earlier run (resume) count as done but not as fetched, so the time
    estimate uses only this run's network pace.
    """

    def __init__(self, label: str, total: int, *, unit: str = "apps", every: float = 10.0,
                 clock: Callable[[], float] = time.monotonic, emit: Callable[[str], None] | None = None):
        self.label, self.total, self.unit, self.every = label, total, unit, every
        self.clock = clock
        self.emit = emit or log.info
        self.done = self.fetched = self.skipped = self.resumed = 0
        self.started = self._last = clock()

    def step(self, *, fetched: bool, skipped: bool = False) -> None:
        self.done += 1
        if fetched:
            self.fetched += 1
        else:
            self.resumed += 1
        if skipped:
            self.skipped += 1
        if self.clock() - self._last >= self.every:
            self._last = self.clock()
            self.emit(self.line())

    def line(self) -> str:
        share = f" ({100 * self.done / self.total:.1f}%)" if self.total else ""
        parts = [f"{self.label}: {self.done:,} / {self.total:,} {self.unit}{share}"]
        if self.resumed:
            parts.append(f"{self.resumed:,} already collected")
        if self.skipped:
            parts.append(f"{self.skipped:,} skipped")
        elapsed = self.clock() - self.started
        if self.fetched and self.done < self.total:
            parts.append(f"about {duration(elapsed / self.fetched * (self.total - self.done))} left")
        return " · ".join(parts)

    def finish(self, summary: str = "") -> None:
        text = f"{self.label} finished: {self.done:,} {self.unit} in {duration(self.clock() - self.started)}"
        if self.resumed:
            text += f" ({self.resumed:,} from an earlier run)"
        if summary:
            text += f"; {summary}"
        self.emit(text)

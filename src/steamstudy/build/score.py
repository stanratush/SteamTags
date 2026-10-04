"""`score(history, window) -> Score`: the single scoring function (Build and the Collect store stage).

A Placeholder Row (Avg 0.00 and Peak 0, at any position) is treated exactly like an omitted row.
Release Month is the first month with a row that is not a Placeholder Row. Mean Monthly Players is
the mean of Monthly Avg. Players over the months from the Release Month on that have a value and
fall inside the Observation Window. Missing Months stay missing.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from steamstudy.build.parse import MonthlyHistory


@dataclass(frozen=True)
class Window:
    first: str  # YYYY-MM
    last: str

    def __contains__(self, month: str) -> bool:
        return self.first <= month <= self.last


@dataclass(frozen=True)
class Score:
    mean_monthly_players: float  # rounded to 6 decimals, the published value the rank is built from
    months_observed: int
    release_month: str


def release_month(history: MonthlyHistory) -> str | None:
    for row in history.rows:
        if not row.is_placeholder:
            return row.month
    return None


def score(history: MonthlyHistory, window: Window) -> Score | None:
    """The app's Score, or None when it has no Monthly Avg. Players value in the window (unscored)."""
    release = release_month(history)
    if release is None:
        return None
    values = [r.avg for r in history.rows if not r.is_placeholder and r.month >= release and r.month in window]
    if not values:
        return None
    return Score(round(math.fsum(values) / len(values), 6), len(values), release)


def unscored_reason(history: MonthlyHistory | None, window: Window) -> str:
    """Why an unscored app has no score: no month rows / only Placeholder Rows / none in the window."""
    if history is None or not history.rows:
        return "no_month_rows"
    if all(r.is_placeholder for r in history.rows):
        return "only_placeholder_rows"
    return "no_month_in_window"


def placeholder_rows(history: MonthlyHistory) -> list[tuple[str, str]]:
    """(month, position) for every Placeholder Row: leading / interior / trailing relative to the data rows."""
    data = [r.month for r in history.rows if not r.is_placeholder]
    out = []
    for r in history.rows:
        if not r.is_placeholder:
            continue
        if not data or r.month < data[0]:
            position = "leading"
        elif r.month > data[-1]:
            position = "trailing"
        else:
            position = "interior"
        out.append((r.month, position))
    return out

"""The Build's app cache, `<build>/app_cache/`: Removal Sensitivity and Parameter Selection results.

"Clear app cache" (the button and `steamstudy app --clear-cache`) goes through `clear_all`.
"""

from __future__ import annotations

from pathlib import Path

from steamstudy.app import ps_cache, rs_cache


def clear_all(cache_root: Path) -> dict[str, int]:
    return {"removal_sensitivity": rs_cache.clear(cache_root), "parameter_selection": ps_cache.clear(cache_root)}


def cleared_text(counts: dict[str, int]) -> str:
    return (f"Cleared {counts['removal_sensitivity']} cached Removal Sensitivity result(s) and "
            f"{counts['parameter_selection']} Parameter Selection result(s).")

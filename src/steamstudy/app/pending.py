"""Exports waiting to be reopened in another tab's Build (Open Network State with another Build's export).

The tab that received the upload stashes it here and navigates to the export's Build with `?open=<token>`; the new
page takes it back once and reopens it there. The stash lives in the app process's temporary job store
(`server.job_store`), so it never outlives the process and is never written into a Build.
"""

from __future__ import annotations

import json
import re
import secrets
from pathlib import Path

_TOKEN = re.compile(r"[0-9a-f]{32}")
_STORE: Path | None = None


def set_store(folder: Path) -> None:
    global _STORE
    _STORE = Path(folder) / "pending"
    _STORE.mkdir(parents=True, exist_ok=True)


def stash(contents: str, filename: str | None) -> str:
    if _STORE is None:
        raise RuntimeError("no pending store: the app sets one at start")
    token = secrets.token_hex(16)
    (_STORE / f"{token}.json").write_text(json.dumps({"contents": contents, "filename": filename}), encoding="utf-8")
    return token


def take(token: object) -> tuple[str, str | None] | None:
    """The stashed upload for a token, once (it is removed); None for an unknown or malformed token."""
    if _STORE is None or not isinstance(token, str) or not _TOKEN.fullmatch(token):
        return None
    path = _STORE / f"{token}.json"
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    path.unlink(missing_ok=True)
    return str(data["contents"]), data.get("filename")

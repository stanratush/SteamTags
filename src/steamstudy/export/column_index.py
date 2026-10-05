"""Generate User Guide Appendix B, the alphabetical column index, from the export schema.

    uv run python -m steamstudy.export.column_index      # rewrites docs/user-guide/appendix-b-column-index.md

A test fails when the committed file differs from what this module generates.
"""

from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

from steamstudy.export.guide_index import GUIDE_CHAPTER
from steamstudy.export.schema import REGISTRY

INDEX_FILE = "appendix-b-column-index.md"

GROUP_LABEL = {
    "build_datasets": "Build datasets/",
    "build_reports": "Build reports/",
    "analysis": "Build analysis/",
    "app_export": "app export zip",
    "snapshot": "Snapshot folder",
}


def render() -> str:
    rows: dict[tuple[str, str], dict[str, set[str]]] = defaultdict(lambda: {"files": set(), "panels": set(),
                                                                             "reports": set()})
    for schema in REGISTRY:
        for column in schema.columns:
            entry = rows[(column.name, column.guide_entry or "")]
            entry["files"].add(f"`{schema.name}` ({GROUP_LABEL.get(schema.group, schema.group)})")
            entry["panels"].add(column.app_panel or "")
            entry["reports"].add(column.report_section or "")
    lines = [
        "# Appendix B. Column index",
        "",
        "Every exported column in alphabetical order, with the files it appears in, where the app shows it, where a "
        "generated report uses it, and its entry in [chapter 3](03-metric-reference.md). This file is generated "
        "from `steamstudy.export.schema` by `python -m steamstudy.export.column_index`; do not edit it by hand.",
        "",
        "| Column | File(s) | App panel | Report section | Explained in |",
        "|---|---|---|---|---|",
    ]
    for (name, anchor), info in sorted(rows.items(), key=lambda kv: (kv[0][0].lower(), kv[0][1])):
        lines.append(
            f"| `{name}` | {'<br>'.join(sorted(info['files']))} | {'; '.join(sorted(p for p in info['panels'] if p))} "
            f"| {'; '.join(sorted(r for r in info['reports'] if r))} | [{anchor}]({GUIDE_CHAPTER}#{anchor}) |"
        )
    return "\n".join(lines) + "\n"


def guide_dir() -> Path:
    return Path(__file__).resolve().parents[3] / "docs" / "user-guide"


def main() -> int:
    path = guide_dir() / INDEX_FILE
    path.write_text(render(), encoding="utf-8", newline="\n")
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

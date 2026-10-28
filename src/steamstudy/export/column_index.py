"""Generate User Guide Appendix B, the alphabetical column index, from the export schema.

    uv run python -m steamstudy.export.column_index      # rewrites docs/user-guide/appendix-b-column-index.md

It is generated once per language whose fixed labels are in `FIXED`: the Bulgarian copy goes to
`docs/user-guide/bg/` (issue 38 adds its labels). Column names, file names and anchors stay English in both. A test
fails when a committed file differs from what this module generates.
"""

from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from steamstudy.export.guide_index import GUIDE_CHAPTER
from steamstudy.export.schema import REGISTRY

INDEX_FILE = "appendix-b-column-index.md"

GROUP_LABEL = {
    "build_datasets": "Build datasets/",
    "build_reports": "Build reports/",
    "analysis": "Build analysis/",
    "app_export": "app export zip",
    "snapshot": "Snapshot folder",
    "parameter_selection": "Parameter Selection export zip",
}

# The appendix's fixed text per language: its title, introduction, table header and the file groups' labels.
FIXED: dict[str, dict[str, Any]] = {
    "en": {
        "title": "# Appendix B. Column index",
        "intro": "Every exported column in alphabetical order, with the files it appears in, where the app shows it, "
                 "where a generated report uses it, and its entry in [chapter 3](03-metric-reference.md). This file is "
                 "generated from `steamstudy.export.schema` by `python -m steamstudy.export.column_index`; do not edit "
                 "it by hand.",
        "header": "| Column | File(s) | App panel | Report section | Explained in |",
        "groups": GROUP_LABEL,
    },
}


def render(lang: str = "en") -> str:
    fixed = FIXED[lang]
    rows: dict[tuple[str, str], dict[str, set[str]]] = defaultdict(lambda: {"files": set(), "panels": set(),
                                                                             "reports": set()})
    for schema in REGISTRY:
        for column in schema.columns:
            entry = rows[(column.name, column.guide_entry or "")]
            entry["files"].add(f"`{schema.name}` ({fixed['groups'].get(schema.group, schema.group)})")
            entry["panels"].add(column.app_panel or "")
            entry["reports"].add(column.report_section or "")
    lines = [fixed["title"], "", fixed["intro"], "", fixed["header"], "|---|---|---|---|---|"]
    for (name, anchor), info in sorted(rows.items(), key=lambda kv: (kv[0][0].lower(), kv[0][1])):
        lines.append(
            f"| `{name}` | {'<br>'.join(sorted(info['files']))} | {'; '.join(sorted(p for p in info['panels'] if p))} "
            f"| {'; '.join(sorted(r for r in info['reports'] if r))} | [{anchor}]({GUIDE_CHAPTER}#{anchor}) |"
        )
    return "\n".join(lines) + "\n"


def guide_dir(lang: str = "en") -> Path:
    base = Path(__file__).resolve().parents[3] / "docs" / "user-guide"
    return base if lang == "en" else base / lang


def main() -> int:
    for lang in FIXED:
        path = guide_dir(lang) / INDEX_FILE
        path.write_text(render(lang), encoding="utf-8", newline="\n")
        print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

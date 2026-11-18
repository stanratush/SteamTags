"""Generate User Guide Appendix B, the alphabetical column index, from the export schema.

    uv run python -m steamstudy.export.column_index      # rewrites docs/user-guide/appendix-b-column-index.md

The Steam table lists every column of a Steam Build's files (`would_be_rank_<dataset>` as one row); an *Import
Builds* section follows with the columns Import Builds add or rename, the Steam columns they drop and the Steam files
they do not write, all read from the schema's Build kinds.

It is generated once per language in `FIXED`: the Bulgarian copy goes to `docs/user-guide/bg/`, with its fixed
text, file-group labels and app panels in Bulgarian. Column names, file names, anchors and a report's own section names
stay English in both. A test fails when a committed file differs from what this module generates.
"""

from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from steamstudy.export.guide_index import GUIDE_CHAPTER
from steamstudy.export import schema as S
from steamstudy.export.schema import REGISTRY

INDEX_FILE = "appendix-b-column-index.md"

GROUP_LABEL = {
    "build_datasets": "Build datasets/",
    "build_reports": "Build reports/",
    "analysis": "Build analysis/",
    "app_export": "app export zip",
    "snapshot": "Snapshot folder",
    "parameter_selection": "Parameter Selection export zip",
    "cluster_comparison": "Cluster Comparison export zip",
}

# The appendix's fixed text per language: its title, introduction, table header and the file groups' labels, and
# for Bulgarian the schema's app panels and report sections (English shows the schema's own words).
FIXED: dict[str, dict[str, Any]] = {
    "en": {
        "title": "# Appendix B. Column index",
        "intro": "Every exported column in alphabetical order, with the files it appears in, where the app shows it, "
                 "where a generated report uses it, and its entry in [chapter 3](03-metric-reference.md). This file is "
                 "generated from `steamstudy.export.schema` by `python -m steamstudy.export.column_index`; do not edit "
                 "it by hand.",
        "header": "| Column | File(s) | App panel | Report section | Explained in |",
        "groups": GROUP_LABEL,
        "import_title": "## Import Builds",
        "import_intro": "Import Builds write the files above under the same names, except the Steam-only files "
                        "listed below. The columns in this table are new or renamed in Import Builds; every other "
                        "column is as above.",
        "dropped": "Steam columns absent from Import Builds:",
        "not_written": "Steam files Import Builds do not write (`topn_<dataset>.csv` replaces "
                       "`top100_<dataset>.csv`):",
    },
    "bg": {
        "title": "# Приложение B. Индекс на колоните {#appendix-b-column-index}",
        "intro": "Всяка експортирана колона по азбучен ред, с файловете, в които се появява, мястото, където я "
                 "показва приложението, мястото, където я използва генериран доклад, и статията ѝ в "
                 "[глава 3](03-metric-reference.md). Имената на колоните и файловете, както и разделите на "
                 "докладите, които остават на английски, са както в експорта. Този файл се генерира от "
                 "`steamstudy.export.schema` с `python -m steamstudy.export.column_index`; не го редактирайте "
                 "ръчно.",
        "header": "| Колона | Файл(ове) | Панел в приложението | Раздел на доклада | Обяснена в |",
        "import_title": "## Компилации от импорт {#import-builds}",
        "import_intro": "Компилациите от импорт записват файловете по-горе със същите имена, освен файловете само "
                        "за Steam, изброени по-долу. Колоните в тази таблица са нови или преименувани в "
                        "компилациите от импорт; всяка друга колона е както по-горе.",
        "dropped": "Колони от Steam, които липсват в компилациите от импорт:",
        "not_written": "Файлове от Steam, които компилациите от импорт не записват (`topn_<dataset>.csv` "
                       "заменя `top100_<dataset>.csv`):",
        "groups": {
            "build_datasets": "компилация: datasets/",
            "build_reports": "компилация: reports/",
            "analysis": "компилация: analysis/",
            "app_export": "експортиран zip на приложението",
            "snapshot": "папка на моментната снимка",
            "parameter_selection": "zip от избора на параметри",
            "cluster_comparison": "zip от сравнението на клъстери",
        },
        # The schema's app panels and report sections; a report's own section names stay English, as the report does.
        "panels": {
            "Cluster Comparison: dataset pairs": "Сравнение на клъстери: двойки набори",
            "Cluster Comparison: dataset table": "Сравнение на клъстери: таблица с наборите",
            "Cluster Comparison: link diagram": "Сравнение на клъстери: диаграма на връзките",
            "Cluster Comparison: match detail": "Сравнение на клъстери: подробности за съвпадението",
            "Cluster quality tab": "раздел „Качество на клъстерите“",
            "Cluster quality tab (replicates)": "раздел „Качество на клъстерите“ (повторения)",
            "Cluster-quality row; Cluster quality tab":
                "редът от „Качество на клъстерите“; раздел „Качество на клъстерите“",
            "Clusters table; cluster inspector": "таблица „Клъстери“; инспектор на клъстера",
            "Edges table; edge inspector": "таблица „Ребра“; инспектор на реброто",
            "Nodes table; node inspector": "таблица „Възли“; инспектор на възела",
            "Not in network tab (Analysis Report section 2)":
                "раздел „Извън мрежата“ (раздел 2 на режима „Аналитичен доклад“)",
            "Parameter Selection: Pair Constraints": "Избор на параметри: ограничения за двойката",
            "Parameter Selection: Pair Inspector": "Избор на параметри: Инспектор на двойката",
            "Parameter Selection: Selection settings": "Избор на параметри: настройки на избора",
            "Parameter Selection: Why this pair": "Избор на параметри: „Защо тази двойка“",
            "Parameter Selection: dataset strip": "Избор на параметри: лента с наборите",
            "Parameter Selection: heatmap and Pair Inspector":
                "Избор на параметри: топлинна карта и Инспектор на двойката",
            "Parameter Selection: validation card": "Избор на параметри: карта на валидирането",
            "Removal sensitivity tab": "раздел „Чувствителност към премахване“",
            "cluster inspector (Games)": "инспектор на клъстера (Игри)",
            "loaded dataset (edge inspector lists its games)":
                "зареденият набор (инспекторът на реброто изброява игрите му)",
            "none (Build only)": "няма (само в компилацията)",
        },
        "reports": {"none": "няма"},
    },
}


def _column_name(name: str) -> str:
    """`would_be_rank_<key>` columns are one templated column, expanded once per dataset of the Build."""
    return f"{S.WOULD_BE_RANK}<dataset>" if name.startswith(S.WOULD_BE_RANK) else name


def _table(fixed: dict[str, Any], columns: list[tuple[S.FileSchema, S.Column]]) -> list[str]:
    rows: dict[tuple[str, str], dict[str, set[str]]] = defaultdict(lambda: {"files": set(), "panels": set(),
                                                                             "reports": set()})
    for schema, column in columns:
        entry = rows[(_column_name(column.name), column.guide_entry or "")]
        entry["files"].add(f"`{schema.name}` ({fixed['groups'].get(schema.group, schema.group)})")
        entry["panels"].add(fixed.get("panels", {}).get(column.app_panel, column.app_panel or ""))
        entry["reports"].add(fixed.get("reports", {}).get(column.report_section, column.report_section or ""))
    lines = [fixed["header"], "|---|---|---|---|---|"]
    for (name, anchor), info in sorted(rows.items(), key=lambda kv: (kv[0][0].lower(), kv[0][1])):
        lines.append(
            f"| `{name}` | {'<br>'.join(sorted(info['files']))} | {'; '.join(sorted(p for p in info['panels'] if p))} "
            f"| {'; '.join(sorted(r for r in info['reports'] if r))} | [{anchor}]({GUIDE_CHAPTER}#{anchor}) |"
        )
    return lines


def _import_differences() -> tuple[list[tuple[S.FileSchema, S.Column]], list[str], list[str]]:
    """(columns new or renamed in Import Builds, Steam columns they drop, Steam files they do not write)."""
    new: list[tuple[S.FileSchema, S.Column]] = []
    dropped: set[str] = set()
    for schema in REGISTRY.of_kind("import"):
        if schema.kind != "import":
            continue  # declared once for both kinds
        if schema.name == S.TOPN.name:  # replaces top100_<dataset>.csv: every column is listed
            new += [(schema, c) for c in schema.columns]
            dropped |= {c for c in S.TOP100.column_names if c not in schema.column_names and c not in S.IMPORT_RENAMED}
            continue
        steam = REGISTRY.variant(schema, "steam")
        if steam is None:  # an Import-only file
            new += [(schema, c) for c in schema.columns]
            continue
        new += [(schema, c) for c in schema.columns if c.name not in steam.column_names]
        dropped |= {c for c in steam.column_names if c not in schema.column_names and c not in S.IMPORT_RENAMED}
    not_written = sorted({s.name for s in REGISTRY.of_kind("steam") if s.name != S.TOP100.name
                          and s.group not in S.STEAM_ONLY_GROUPS and REGISTRY.variant(s, "import") is None})
    return new, sorted(dropped), not_written


def render(lang: str = "en") -> str:
    fixed = FIXED[lang]
    steam = [(schema, column) for schema in REGISTRY.of_kind("steam") for column in schema.columns]
    new, dropped, not_written = _import_differences()
    lines = [fixed["title"], "", fixed["intro"], "", *_table(fixed, steam), "",
             fixed["import_title"], "", fixed["import_intro"], "", *_table(fixed, new), "",
             f"{fixed['dropped']} {', '.join(f'`{c}`' for c in dropped)}.", "",
             f"{fixed['not_written']} {', '.join(f'`{f}`' for f in not_written)}."]
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

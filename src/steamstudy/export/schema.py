"""The single declaration of every exported file and column.

Every CSV the package writes is declared here with its columns, types and one-line descriptions, and
every writer validates against these declarations (`steamstudy.export.writer`). `export.json` and
`analysis.json` embed a `columns` block generated from here.

Adding, removing or renaming a column bumps `SCHEMA_VERSION` (separate from the Network State
`key_version`).
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

SCHEMA_VERSION = 1

# Column types and how the writer renders them:
#   str        as is
#   int        decimal integer
#   float      shortest round-trip repr, so app and Build values compare exactly
#   float6     exactly 6 decimals (mean_monthly_players, so the rank can be reproduced)
#   bool       true / false
#   str_list   ;-separated strings
#   int_list   ;-separated integers
# None is n/a and is written as an empty cell, whatever the type.
COLUMN_TYPES = ("str", "int", "float", "float6", "bool", "str_list", "int_list")


@dataclass(frozen=True)
class Column:
    name: str
    type: str
    description: str
    guide_entry: str | None = None
    app_panel: str | None = None
    report_section: str | None = None

    def __post_init__(self) -> None:
        if self.type not in COLUMN_TYPES:
            raise ValueError(f"column {self.name}: unknown type {self.type!r}")
        if not self.description.strip():
            raise ValueError(f"column {self.name}: a one-line description is required")


@dataclass(frozen=True)
class FileSchema:
    name: str
    description: str
    columns: tuple[Column, ...]
    group: str = ""  # "build_datasets", "build_reports", "analysis", "app_export", ...

    def __post_init__(self) -> None:
        names = [c.name for c in self.columns]
        if len(set(names)) != len(names):
            raise ValueError(f"{self.name}: duplicate column names")

    @property
    def column_names(self) -> tuple[str, ...]:
        return tuple(c.name for c in self.columns)

    def column(self, name: str) -> Column:
        for c in self.columns:
            if c.name == name:
                return c
        raise KeyError(f"{self.name} has no column {name!r}")

    def with_prefix(self, name: str, prefix: tuple[Column, ...], group: str = "") -> FileSchema:
        """The same file with leading columns, e.g. an app table stacked by dataset in the Build."""
        return replace(self, name=name, columns=(*prefix, *self.columns), group=group or self.group)


@dataclass
class Registry:
    files: dict[str, FileSchema] = field(default_factory=dict)

    def declare(self, schema: FileSchema) -> FileSchema:
        if schema.name in self.files:
            raise ValueError(f"file {schema.name} declared twice")
        self.files[schema.name] = schema
        return schema

    def __getitem__(self, name: str) -> FileSchema:
        return self.files[name]

    def __iter__(self):
        return iter(self.files.values())


REGISTRY = Registry()


def declare(name: str, description: str, columns: list[Column] | tuple[Column, ...], group: str = "") -> FileSchema:
    return REGISTRY.declare(FileSchema(name, description, tuple(columns), group))


def file(name: str) -> FileSchema:
    return REGISTRY[name]


def columns_block(schemas: list[FileSchema] | tuple[FileSchema, ...]) -> dict[str, dict[str, dict[str, str]]]:
    """The `columns` block embedded in `export.json` / `analysis.json`: file -> column -> type/description."""
    return {
        s.name: {c.name: {"type": c.type, "description": c.description} for c in s.columns} for s in schemas
    }

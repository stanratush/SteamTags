# 01: Package skeleton, config and export-schema core

**What to build:** The empty-but-runnable `steamstudy` package that every other ticket builds on. Anyone can install it with uv on Python 3.14 (bytecode compiled), run the `steamstudy` CLI, load and validate the TOML config set, and write CSVs only through validated writers declared in one export-schema module. This is the prefactor ticket: it ships no domain behaviour, only the seams the rest of the work plugs into.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

Spec: [Steam Success Study spec](../../steam-success-study/spec.md): "Package, runtime and dependencies", "Commands", "Config", "Export schemas".

- [ ] One uv-managed package with a `src/` layout and the subpackages `collect`, `build`, `network`, `analysis`, `export`, `app`. `requires-python = ">=3.14,<3.15"`. Dependencies are pinned as the spec says (`dash-cytoscape==1.0.2` exact; Dash, dash-ag-grid, networkx, leidenalg, python-igraph, scikit-learn, numpy, scipy, pandas, an HTML parser). A lockfile is committed.
- [ ] The install instructions compile bytecode, and nothing in the package sets `PYTHONDONTWRITEBYTECODE`.
- [ ] A `steamstudy` CLI entry point exists with the `collect`, `build` and `app` subcommands stubbed, plus `--help`.
- [ ] Every config file named in the spec (`collection`, `exclusions`, `genres`, `datasets`, `network`, `analysis`, and the three researcher-maintained lists) is loaded from TOML with the spec's defaults. Validation rejects `noise_seeds < 2` and `null_replicates < 2`.
- [ ] `collection_config_hash` and `build_config_hash` are computed over the parsed, normalised contents, so whitespace or key order does not change them.
- [ ] The `export.schema` module can declare a file with its columns (name, type, one-line description). A validated CSV writer applies the shared conventions: UTF-8 with BOM written with an explicit encoding, comma, `\n`, `true`/`false`, empty cell for n/a, shortest round-trip floats, `;`-lists. It refuses undeclared columns and missing declared columns.
- [ ] `schema_version` exists as an integer, and the schema module can generate a `columns` block for a JSON metadata file.
- [ ] Every file read and write in the package passes an explicit encoding (enforced by a test or lint check).
- [ ] The test suite runs offline with `-W default -X faulthandler` and covers the writer conventions and the config validation.

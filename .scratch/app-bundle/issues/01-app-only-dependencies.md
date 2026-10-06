# 01: App-only dependencies, Python 3.12–3.14 and the library-version banner

**What to build:** the `steamstudy` package can be installed with only the Tag Network app's dependencies, on Python 3.12–3.14, and the app runs without any pipeline module or pipeline dependency. The app warns when a library it uses differs from the version the loaded Build recorded.

**Blocked by:** [App readability 01: Plain Cytoscape.js renderer](../../app-readability/issues/01-plain-cytoscape-renderer.md) (removes dash-cytoscape; the App Bundle is made after the renderer switch)

**Status:** done

Spec: [App Bundle spec](../spec.md): "Scope and naming", "Python and platforms", "App behaviour changes". Decision: [ADR 0001](../../../docs/adr/0001-app-bundle-wheels-not-frozen.md).

Facts found while grilling:
- `src/steamstudy/app/export.py` imports `steamstudy.build.core` only for `software_versions()`; `build.core` pulls in `build.parse` and so lxml.
- Pipeline-only imports: pandas, markdown (`analysis/`), lxml (`build/parse.py`), requests (`collect/fetcher.py`). The app never imports them.
- `uv.lock` is resolved for `==3.14.*` only, so it holds no wheels for 3.12/3.13 yet.
- networkx 3.7 declares `!=3.14.1,>=3.12`; numpy 2.5.3 and scipy 1.18.1 declare `>=3.12`.

- [x] `software_versions()` (or its replacement) lives where the app can import it without pipeline modules; no module under `app/`, `network/`, `export/` or `config.py` imports `build`, `collect` or `analysis`, enforced by a test.
- [x] Declared dependencies split: the base set is exactly what the app needs (dash, dash-ag-grid, diskcache, multiprocess, psutil, networkx, leidenalg, python-igraph, numpy, scikit-learn and their dependencies); lxml, requests, pandas and markdown move to a pipeline set that the developer environment still installs by default (`uv sync` and `uv run steamstudy build` keep working unchanged).
- [x] The package's Python range is 3.12–3.14 excluding 3.14.1; `uv.lock` is re-resolved to cover it with the same pinned versions as today; the developer environment still uses 3.14.
- [x] No source under the app's import closure uses syntax or APIs newer than 3.12 (checked with mypy at `python_version = "3.12"` on that closure, and by running the app tests on 3.13 here).
- [x] Library-version banner: when any library the app uses is installed at a version different from the loaded Build's `software_versions`, the app shows a banner naming each library with both versions. Libraries absent from the environment that the app does not use, and the Python version, never trigger it. Tested with a Build whose recorded versions are edited.
- [x] Existing test suite passes.

## Comments

**2026-10-06 (implemented):** `software_versions()` moved to the new `steamstudy/versions.py` (with `APP_LIBRARIES` and `version_mismatches`), and `builds_dir` / `resolve_build` to the new `steamstudy/builds.py` (re-exported by `build.writer`), because `cli app` reached `build.core` and so lxml through `build.writer`. `pyproject.toml`: the base dependencies are exactly the app set; pandas, requests, lxml and markdown are the `pipeline` dependency group, installed by default (`tool.uv.default-groups`), so the wheel's metadata lists only the app set while `uv sync` / `uv run steamstudy build` are unchanged. `requires-python = ">=3.12,!=3.14.1,<3.15"`; `uv lock` re-resolved to the same 61 versions; `.python-version` keeps the developer environment on 3.14 (3.14.8). `tests/test_app_only.py`: a static import check of app/, network/, export/, config.py, versions.py, builds.py; a subprocess that blocks every pipeline module and library and still runs `steamstudy app --clear-cache`, serves the page, recomputes, exports and reopens; the dependency split; mypy `--python-version 3.12` on the app's import closure; and the banner, tested with Builds whose recorded versions are edited (app libraries trigger it with both versions named; pandas, lxml, markdown and Python never do). The app, export, layout and network tests (106) also passed on Python 3.13.0 in an isolated environment built from the new lock.

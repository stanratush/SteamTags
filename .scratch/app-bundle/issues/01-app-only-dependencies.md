# 01: App-only dependencies, Python 3.12–3.14 and the library-version banner

**What to build:** the `steamstudy` package can be installed with only the Tag Network app's dependencies, on Python 3.12–3.14, and the app runs without any pipeline module or pipeline dependency. The app warns when a library it uses differs from the version the loaded Build recorded.

**Blocked by:** [App readability 01: Plain Cytoscape.js renderer](../../app-readability/issues/01-plain-cytoscape-renderer.md) (removes dash-cytoscape; the App Bundle is made after the renderer switch)

**Status:** ready-for-agent

Spec: [App Bundle spec](../spec.md): "Scope and naming", "Python and platforms", "App behaviour changes". Decision: [ADR 0001](../../../docs/adr/0001-app-bundle-wheels-not-frozen.md).

Facts found while grilling:
- `src/steamstudy/app/export.py` imports `steamstudy.build.core` only for `software_versions()`; `build.core` pulls in `build.parse` and so lxml.
- Pipeline-only imports: pandas, markdown (`analysis/`), lxml (`build/parse.py`), requests (`collect/fetcher.py`). The app never imports them.
- `uv.lock` is resolved for `==3.14.*` only, so it holds no wheels for 3.12/3.13 yet.
- networkx 3.7 declares `!=3.14.1,>=3.12`; numpy 2.5.3 and scipy 1.18.1 declare `>=3.12`.

- [ ] `software_versions()` (or its replacement) lives where the app can import it without pipeline modules; no module under `app/`, `network/`, `export/` or `config.py` imports `build`, `collect` or `analysis`, enforced by a test.
- [ ] Declared dependencies split: the base set is exactly what the app needs (dash, dash-ag-grid, diskcache, multiprocess, psutil, networkx, leidenalg, python-igraph, numpy, scikit-learn and their dependencies); lxml, requests, pandas and markdown move to a pipeline set that the developer environment still installs by default (`uv sync` and `uv run steamstudy build` keep working unchanged).
- [ ] The package's Python range is 3.12–3.14 excluding 3.14.1; `uv.lock` is re-resolved to cover it with the same pinned versions as today; the developer environment still uses 3.14.
- [ ] No source under the app's import closure uses syntax or APIs newer than 3.12 (checked with mypy at `python_version = "3.12"` on that closure, and by running the app tests on 3.13 here).
- [ ] Library-version banner: when any library the app uses is installed at a version different from the loaded Build's `software_versions`, the app shows a banner naming each library with both versions. Libraries absent from the environment that the app does not use, and the Python version, never trigger it. Tested with a Build whose recorded versions are edited.
- [ ] Existing test suite passes.

## Comments

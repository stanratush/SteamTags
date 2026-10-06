# Spec: App Bundle

Settled in a grilling session on 2026-10-05. Glossary: [CONTEXT.md](../../CONTEXT.md) (**App Bundle**). Decision record: [ADR 0001](../../docs/adr/0001-app-bundle-wheels-not-frozen.md).

## Goal

A researcher with Python installed copies one zip to another computer, extracts it, double-clicks a launcher and gets the Tag Network app with the Builds the zip carries. No uv, no repository, no internet, no development tools.

## Decisions

### Scope and naming
- The application is the **Tag Network app**; the copyable thing is the **App Bundle**. Avoid "visualization tool", "standalone app", "portable version", "offline bundle".
- Only one kind of bundle exists, and it is always offline: everything except Python itself is inside.
- uv stays the tool for development and the pipeline (`collect`, `build`, tests, mypy). The App Bundle is a second way to deliver the app, made from the repository; the app code lives only once, in the repo.
- The bundle contains the app only: no `collect`/`build`, no lxml, requests, pandas or markdown.

### Python and platforms
- Supported Python: 3.12, 3.13, 3.14, except 3.14.1 (networkx 3.7 excludes it). The floor comes from numpy 2.5.3, scipy 1.18.1 and networkx 3.7. The pipeline keeps running on 3.14.
- Targets: Windows x64, macOS arm64, Linux x86_64. A bundle covers the OS of the machine making it by default; `--target` (repeatable) adds others. Each target carries wheels for all three Python versions (about 200–250 MB per target). Intel Macs and ARM Linux are out of scope.
- Every library is pinned exactly to `uv.lock`, so a bundle gives the same Clusters and metrics as the pipeline machine.
- The graph is drawn by a vendored Cytoscape.js inside the `steamstudy` package's `app/assets/` ([App readability](../app-readability/spec.md) issue 01), so it ships in the `steamstudy` wheel. dash-cytoscape is no longer a dependency and no wheel has to be built for it.
- Order: the App Bundle is made after the renderer switch. App-bundle 01 is blocked by [App readability 01](../app-readability/issues/01-plain-cytoscape-renderer.md).

### Making a bundle
- `steamstudy bundle` writes one zip to the git-ignored `bundles/`, e.g. `bundles/tag-network-<build_id>-windows.zip`. Making a bundle needs internet (to fetch wheels); using one never does.
- Builds: the latest by default; `--build` (repeatable) adds others. Each Build goes in as its whole folder (datasets and reports) without `app_cache/`.
- The bundle root holds `READ ME FIRST.txt`: what it is, the Python versions and OS it was made for, how to start it, and where the User Guide is (shipped inside, also opened by each `?` in the app).

### Running a bundle
- `start_tag_network.py` (stdlib only) is the one real launcher; `Start Tag Network.bat` (Windows: `py -3`, then `python`) and `Start Tag Network.command` (macOS) are double-click wrappers that call it.
- First run: install the bundled wheels into a private environment inside the bundle folder, with no package index. Rebuild it automatically when the folder has moved to another computer or the Python changed.
- Refuse, with a message saying what to do, when: started from inside a zip (not extracted), the folder is read-only ("copy this folder to your own disk first"), Python is unsupported (incl. 3.14.1), or `venv`/`ensurepip` is missing (e.g. Debian without `python3-venv`).
- Opens the latest included Build unless `--build` is given. If port 8050 is taken, use the next free port and open the browser there (launcher only; `steamstudy app --port` stays strict).

### App behaviour changes (also in the developer app)
- The app never imports pipeline modules (today `app/export.py` imports `build.core` only for `software_versions()`).
- Opening an exported Network State finds its Build by identity (`build_id` plus the `build.json` hash already checked) among the available Builds; the recorded `build_path` is informational only. An export whose Build is not available is refused, naming the Build it needs.
- Library-version banner: when a library the app uses is installed at a version different from the one the Build recorded in `software_versions`, the app shows a banner (like the test-Snapshot banner). Libraries the bundle intentionally lacks (pipeline-only) and a different Python version are never warned about; they stay visible in the export's provenance.

### Docs
- User Guide "Getting started" describes opening the app from an App Bundle instead of `uv run steamstudy app`.
- Running Guide gains "Making an App Bundle", and says plainly that macOS/Linux bundles are checked for completeness but untested on real hardware.

### Acceptance
- An automated test makes a bundle, installs it with no package index into fresh environments on every Python available on the test machine (here 3.13 and 3.14; 3.12 is not installed), starts the app and loads a dataset.
- Bundles for other targets are checked for completeness: every required wheel present for every supported Python.

## Issues

- [01: App-only dependencies, Python 3.12–3.14 and the library-version banner](issues/01-app-only-dependencies.md)
- [02: Open exports by Build identity](issues/02-export-build-identity.md)
- [03: The bundle command and the launcher](issues/03-bundle-command-and-launcher.md)
- [04: Docs and the App Bundle acceptance test](issues/04-docs-and-acceptance-test.md)

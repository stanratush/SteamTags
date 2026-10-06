# 03: The bundle command and the launcher

**What to build:** `steamstudy bundle` writes an App Bundle zip; extracting it and double-clicking the launcher on a computer with Python 3.12–3.14 and no internet opens the Tag Network app on the bundled Builds.

**Blocked by:** 01

**Status:** done

Spec: [App Bundle spec](../spec.md): "Making a bundle", "Running a bundle", "Python and platforms". Decision: [ADR 0001](../../../docs/adr/0001-app-bundle-wheels-not-frozen.md).

Facts found while grilling: dash-cytoscape is no longer a dependency (the vendored Cytoscape.js ships inside the `steamstudy` wheel, [App readability 01](../../app-readability/issues/01-plain-cytoscape-renderer.md)); igraph, leidenalg and psutil ship one abi3 wheel per OS; numpy, scipy, scikit-learn and markupsafe ship one wheel per OS and Python version; `resolve_build(root, ...)` reads `<root>/builds/[<snapshot>/]latest`.

### Bundle command
- [x] `steamstudy bundle [--build ID]... [--target windows|macos|linux]... [--out DIR]`; defaults: latest Build, the current OS, `bundles/`. Output is one zip named `tag-network-<build_id>-<targets>.zip`; `/bundles/` is git-ignored.
- [x] Contents: the launcher and wrappers, `READ ME FIRST.txt`, the app-only `steamstudy` wheel (User Guide included as package data), per-target wheels for Python 3.12, 3.13 and 3.14 with pure-Python wheels stored once, per-target requirements pinned exactly to `uv.lock` with hashes, the selected Build folders without `app_cache/` under `builds/` with `latest` pointers, and a manifest (bundle format version, `steamstudy` version, `uv.lock` hash, targets, Python versions, Build ids, creation date).
- [x] The command fails, writing nothing, when any required wheel is unavailable for any target × Python, or a selected Build does not exist.

### Launcher (`start_tag_network.py`, stdlib only, runs on 3.12–3.14)
- [x] Refuses with a plain message saying what to do: Python outside 3.12–3.14 or exactly 3.14.1; OS/architecture not among the bundle's targets; started from inside a zip; bundle folder not writable ("copy this folder to your own disk first"); `venv`/`ensurepip` unavailable (names `python3-venv` on Debian/Ubuntu).
- [x] First run creates a private environment inside the bundle and installs from the bundled wheels only (no package index, hashes required); later runs reuse it. It is rebuilt when the recorded Python executable/version or bundle manifest no longer match (folder moved to another computer, Python changed).
- [x] Starts the app on the latest bundled Build (`--build` selects another), on port 8050 or the next free one, and opens the browser at `http://127.0.0.1:<port>/`. Extra arguments such as `--clear-cache` and `--no-browser` pass through.
- [x] `Start Tag Network.bat` (tries `py -3`, then `python`) and `Start Tag Network.command` (macOS, executable bit set in the zip) call the launcher and keep the window open on error.
- [x] `READ ME FIRST.txt` states what the bundle is, the OS and Python versions it was made for, how to start it, and where the User Guide is.

### Tests
- [x] Unit tests for the launcher's refusal checks and the environment-rebuild decision.
- [x] The bundle command's completeness check is tested for a non-current target (every required wheel present for every supported Python).

## Comments

**2026-10-06 (in progress, not done):** Implemented `steamstudy bundle` (`src/steamstudy/bundle/make.py`, `wheels.py`), the stdlib launcher `start_tag_network.py`, the `.bat` / `.command` wrappers and `READ ME FIRST.txt`, with unit tests (`tests/test_bundle.py`: refusals, rebuild decision, completeness for every target × Python, nothing written on a missing wheel or Build). Still open: `/bundles/` in `.gitignore` (left out because `.gitignore` has uncommitted local edits), and a real end-to-end bundle run (fetch wheels, install offline, start), which ticket 04's acceptance test covers. Deviation to decide: dash 4 declares `requests` as a dependency, so the bundle installs it although the app never imports it; the spec says "no requests".

**2026-10-06 (done):** `/bundles/` is git-ignored. End-to-end run on the real Build: `uv run steamstudy bundle` wrote `bundles/tag-network-20261006T062622Z-7a23ae9f-windows.zip` (218 MB; 217 MB of wheels for Python 3.12-3.14) in about a minute; extracted and started with Python 3.13.0 and `--no-browser`, it built its private environment offline from the bundled wheels, moved to port 8051 because 8050 was taken, and served the app with the vendored `cytoscape.min.js`; lxml, pandas and markdown were not installed. Deviation from the spec, kept on purpose: `requests` is installed because dash 4 declares it as a dependency (the app never imports it; stripping it would mean installing dash against its own metadata). The launcher's messages are plain ASCII (a test checks it, and that it imports only the standard library).

**2026-10-06 (review fix):** A missing `wheels/` folder now gets its own refusal ("this folder is incomplete") instead of being reported as "still inside its zip"; a failed zip write never leaves a `.zip.partial` behind (tested); `Start Tag Network.bat` falls back to `python` when `py -3` fails, not only when `py` is missing. `packaging` moved from the `pipeline` dependency group to its own default `bundle` group.

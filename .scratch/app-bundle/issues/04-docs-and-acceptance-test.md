# 04: Docs and the App Bundle acceptance test

**What to build:** the guides describe the App Bundle, and an automated test proves a bundle installs and runs offline on every Python available on the test machine.

**Blocked by:** 01, 02, 03

**Status:** done

Spec: [App Bundle spec](../spec.md): "Docs", "Acceptance".

### Docs
- [x] `docs/user-guide/01-getting-started.md` "Open the app" describes extracting an App Bundle and double-clicking the launcher (supported Python versions and OS, first-run install, read-only and zip refusals, port fallback); `uv run steamstudy app` moves to the Running Guide.
- [x] `docs/running-guide.md` gains "Making an App Bundle": the command, its options, what goes in, that making one needs internet and using one does not, and that macOS/Linux bundles are checked for completeness but untested on real hardware.
- [x] Opening an export by Build identity (02) and the library-version banner (01) are described where the guides cover exports and banners.
- [x] `README.md` points researchers to the App Bundle. No researcher-facing text still says they need uv.
- [x] The guide/schema consistency checks pass.

### Acceptance test
- [x] An automated test makes a bundle from a test-mode Build, extracts it to a temporary folder, runs the launcher's install with no package index on every Python 3.12–3.14 found on the machine (here 3.13 and 3.14), starts the app with `--no-browser`, and loads a dataset through the running server. Skipped with a clear reason when wheels cannot be fetched (no internet while making the bundle).
- [x] The installed environment contains none of lxml, pandas, markdown, dash-cytoscape. `requests` is installed because dash declares it (spec amended 2026-10-06), and the running app never imports it.
- [x] The running app serves the vendored `cytoscape.min.js` from its own assets, and the page requests nothing from outside 127.0.0.1, so the graph renders with no network.
- [x] Moving the extracted folder and launching again rebuilds the environment and still works.
- [x] Every command shown in the new guide sections is run once as written.

## Comments

**2026-10-06 (implemented):** Docs: Getting started "Open the app" now describes the App Bundle (Python versions and systems, extract first, read-only and zip refusals, first-run setup, port fallback, `--build`), the library-version banner, and the summary row / quality tab that replaced the two lines under the graph (issue 08); the Running Guide gains "Making an App Bundle" (command, options, contents, internet only for making, macOS/Linux checked for completeness but untested on real hardware), the dependency split, `bundles/` in the folder layout, the banner and opening exports by Build identity; the README points researchers to the App Bundle, and the User Guide no longer mentions uv. `tests/test_bundle_acceptance.py` (marked `slow`, about six minutes; `tests/dash_http.py` fires the recompute callback over HTTP as the browser does) makes a bundle from a test-mode Build, installs it with no package index on every CPython 3.12-3.14 uv finds (here 3.13.0 and 3.14.8), starts the app with `--no-browser`, checks that the page loads only local assets and the vendored `cytoscape.min.js`, loads the Overall dataset through the running server, checks that lxml, pandas, markdown and dash-cytoscape are not installed and that the app imports none of them nor requests (requests is installed because dash declares it), then moves the folder and checks that the next start rebuilds the environment and works. It skips when the wheels cannot be fetched.

Commands from the new sections, run once each: `uv run steamstudy bundle` (Windows zip, 218 MB); `uv run steamstudy bundle --target windows --target macos --target linux` (654 MB, 114 wheels, nine requirement files), which needed `--no-sync` because a `steamstudy app` started in a terminal held `.venv\Scripts\steamstudy.exe` open; `Start Tag Network.bat` with `--clear-cache` and `--no-browser` (it used `py -3` = 3.13.0, reused the environment and served on 8051 because 8050 was taken). `Start Tag Network.command` and `python3 start_tag_network.py` cannot run on this Windows machine; the guide says macOS and Linux bundles are untested on real hardware.

**2026-10-06 (review):** One box is not met: `requests` is installed, because dash 4 declares it as a dependency (uv.lock); the acceptance test checks that lxml, pandas, markdown and dash-cytoscape are absent and that the running app imports none of them nor `requests`. The spec owner decides: accept the exception (and amend the spec's "no lxml, requests, pandas or markdown"), or strip `requests` by installing dash against its declared dependencies (`pip install --no-deps` with an explicit closure), which `pip check` would then report as broken. Everything else in this ticket is done.

**2026-10-06 (decision):** The spec owner accepted the `requests` exception and the spec was amended ("The bundle contains the app only"). The acceptance test already checks exactly this, so the ticket is done.

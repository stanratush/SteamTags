# 04: Docs and the App Bundle acceptance test

**What to build:** the guides describe the App Bundle, and an automated test proves a bundle installs and runs offline on every Python available on the test machine.

**Blocked by:** 01, 02, 03

**Status:** ready-for-agent

Spec: [App Bundle spec](../spec.md): "Docs", "Acceptance".

### Docs
- [ ] `docs/user-guide/01-getting-started.md` "Open the app" describes extracting an App Bundle and double-clicking the launcher (supported Python versions and OS, first-run install, read-only and zip refusals, port fallback); `uv run steamstudy app` moves to the Running Guide.
- [ ] `docs/running-guide.md` gains "Making an App Bundle": the command, its options, what goes in, that making one needs internet and using one does not, and that macOS/Linux bundles are checked for completeness but untested on real hardware.
- [ ] Opening an export by Build identity (02) and the library-version banner (01) are described where the guides cover exports and banners.
- [ ] `README.md` points researchers to the App Bundle. No researcher-facing text still says they need uv.
- [ ] The guide/schema consistency checks pass.

### Acceptance test
- [ ] An automated test makes a bundle from a test-mode Build, extracts it to a temporary folder, runs the launcher's install with no package index on every Python 3.12–3.14 found on the machine (here 3.13 and 3.14), starts the app with `--no-browser`, and loads a dataset through the running server. Skipped with a clear reason when wheels cannot be fetched (no internet while making the bundle).
- [ ] The installed environment contains none of lxml, requests, pandas, markdown, dash-cytoscape.
- [ ] The running app serves the vendored `cytoscape.min.js` from its own assets, and the page requests nothing from outside 127.0.0.1, so the graph renders with no network.
- [ ] Moving the extracted folder and launching again rebuilds the environment and still works.
- [ ] Every command shown in the new guide sections is run once as written.

## Comments

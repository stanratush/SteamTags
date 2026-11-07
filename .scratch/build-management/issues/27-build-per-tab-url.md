# 27: Build per tab in the URL

**What to build:** each tab names its Build in the URL, `/build/<source_id>/<build_id>`, through Dash Pages. Every startup binding becomes per tab. The job store moves to a per-process temporary folder. A switch keeps language, mode and the same-keyed dataset, and cancels the tab's jobs after confirming. Open Network State navigates to the export's Build, and a missing Build gets its own page. Opening a Build does not need the Build menu yet; issue 28 adds the tree.

**Blocked by:** 24

**Status:** ready-for-agent

Spec: [Build management spec](../spec.md): "Switching Builds and caches". ADR 0006. Decision tickets: [switch in one process](03-switch-builds-in-one-process.md), [switching and cache separation](10-switching-and-cache-separation.md). Findings: [research 03](../research/03-switch-builds.md).

- [ ] Dash Pages route `/build/<source_id>/<build_id>`. The server resolves ids under the builds root, rejects anything that is not an id, and never takes a path from the browser. `/` redirects to the startup Build (`--build`, else root `latest`).
- [ ] The bindings in `app/server.py:29-38`, `app/layout.py:235-327` and `:463`, and `app/ps_view.py:987-1031` are resolved from the tab's Build. The relabel entries `brand-build`, `ps-run-one` and `ps-s-defining` stop closing over the startup Build.
- [ ] The job store is one temporary folder per app process under the OS temp directory, removed at exit, never inside a Build or bundle.
- [ ] A switch keeps the Interface Language, the open mode, and the dataset when the new Build has the same key (else its first). Network State resets to the new Build's defaults.
- [ ] Before switching, a confirmation names the tab's running Removal Sensitivity and Parameter Selection jobs ("N running jobs will be cancelled; finished parts stay cached"), then cancels them.
- [ ] Open Network State with another Build's export navigates to that Build's URL and reopens the export there (this fixes the half-switch).
- [ ] A missing Build shows "This Build no longer exists" with a link to the latest Build.
- [ ] Clear app cache and `--clear-cache` clear the open Build only.
- [ ] App Bundles use the same URLs.
- [ ] bg entries for every new string.
- [ ] Tests (with `tests/dash_http.py`):
  - Two tabs on two Builds keep their own datasets, header and Parameter Selection keys.
  - Cross-Build Open Network State lands on the right Build with every option correct.
  - A switch cancels only that tab's jobs.
  - A deleted Build's URL shows the notice, and deleting a Build works on Windows while the app runs (the job store is outside it).

## Comments

# 27: Build per tab in the URL

**What to build:** each tab names its Build in the URL, `/build/<source_id>/<build_id>`, through Dash Pages. Every startup binding becomes per tab. The job store moves to a per-process temporary folder. A switch keeps language, mode and the same-keyed dataset, and cancels the tab's jobs after confirming. Open Network State navigates to the export's Build, and a missing Build gets its own page. Opening a Build does not need the Build menu yet; issue 28 adds the tree.

**Blocked by:** 24

**Status:** done

Spec: [Build management spec](../spec.md): "Switching Builds and caches". ADR 0006. Decision tickets: [switch in one process](03-switch-builds-in-one-process.md), [switching and cache separation](10-switching-and-cache-separation.md). Findings: [research 03](../research/03-switch-builds.md).

- [x] Dash Pages route `/build/<source_id>/<build_id>`. The server resolves ids under the builds root, rejects anything that is not an id, and never takes a path from the browser. `/` redirects to the startup Build (`--build`, else root `latest`).
- [x] The bindings in `app/server.py:29-38`, `app/layout.py:235-327` and `:463`, and `app/ps_view.py:987-1031` are resolved from the tab's Build. The relabel entries `brand-build`, `ps-run-one` and `ps-s-defining` stop closing over the startup Build.
- [x] The job store is one temporary folder per app process under the OS temp directory, removed at exit, never inside a Build or bundle.
- [x] A switch keeps the Interface Language, the open mode, and the dataset when the new Build has the same key (else its first). Network State resets to the new Build's defaults.
- [x] Before switching, a confirmation names the tab's running Removal Sensitivity and Parameter Selection jobs ("N running jobs will be cancelled; finished parts stay cached"), then cancels them.
- [x] Open Network State with another Build's export navigates to that Build's URL and reopens the export there (this fixes the half-switch).
- [x] A missing Build shows "This Build no longer exists" with a link to the latest Build.
- [x] Clear app cache and `--clear-cache` clear the open Build only.
- [x] App Bundles use the same URLs.
- [x] bg entries for every new string.
- [x] Tests (with `tests/dash_http.py`):
  - Two tabs on two Builds keep their own datasets, header and Parameter Selection keys.
  - Cross-Build Open Network State lands on the right Build with every option correct.
  - A switch cancels only that tab's jobs.
  - A deleted Build's URL shows the notice, and deleting a Build works on Windows while the app runs (the job store is outside it).

## Comments

### Implementation note (done)

- `app/server.py`: Dash Pages (`use_pages=True, pages_folder=""`), page `/build/<source_id>/<build_id>` and a
  `not_found_404` page, both the missing-Build notice (link to the root `latest`, else the startup Build). `/` is a
  302 to the startup Build. Query parameters `mode`, `dataset` and `open` carry what a switch keeps.
- `app/loader.py`: a tab names its Build by a ref, `<source_id>/<build_id>` (the `build-path` store now holds it),
  resolved under the builds root (`STEAMSTUDY_BUILDS_ROOT`, set by `create_app` so job processes see it). Inside a
  request only a ref is accepted; tests and the CLI may still pass folders.
- `app/relabel.py`: `PerBuild` messages (`brand-build`, `ps-run-one`, `ps-s-defining`) take the tab's Build when
  the language switch relabels them (`relabel` has `State("build-path")`).
- Job store: `server.job_store()`, a `tempfile.mkdtemp` folder per process removed at exit; `app/pending.py` stashes a
  cross-Build Open there. `do_open`'s first output is now `switch-to` (a URL): another Build's export navigates to
  `/build/<ref>?mode=…&dataset=…&open=<token>`, whose page takes the upload back once (`reopen`) and opens it.
- A switch goes through `workbench.js` `switchBuild`: it counts the tab's running jobs by their enabled Cancel buttons
  (both now start disabled), confirms, clicks them, then navigates. Checked in the browser pane (confirm text,
  decline keeps the tab, accept cancels and lands on the other Build).
- Clear app cache was already per open Build; App Bundles run the same app, so the same URLs.
- Tests: `tests/test_build_tabs.py`; `tests/dash_http.py` gains `page`/`client_page`/`start_path` (the page comes
  from the router callback, as the browser fetches it).


# How does switching Builds keep caches apart and avoid recalculation?
Type: grilling
Status: resolved
Blocked by: 03, 07

## Question

Charted: switching Builds should cause no unnecessary recalculation, and each Build keeps its own configuration, results and caches. Today each Build folder has `app_cache/` (jobs, parameter_selection, removal_sensitivity), and `state_id` hashes `build_id`, so no result is shared between Builds.

Using [Can one app process switch Builds?](03-switch-builds-in-one-process.md) and [Build identity](07-build-identity-and-lifecycle.md), decide:
- in-place switching or a restart, and what the user keeps across a switch (dataset choice, Network State settings, the Interface Language, the open mode);
- what "unnecessary recalculation" means: per-Build caches only, or reuse across Builds whose Top-N rows are identical;
- what happens to running jobs when the user switches (cancel, keep running, block the switch);
- when a new Build's Parameter Selection grid runs: at creation, on demand, or never in the app (today the bundle maker runs it);
- where a Build made in the app writes its caches, and what `--clear-cache` and delete clear;
- where the shared background job store lives once it leaves `<build>/app_cache/jobs`: the research measured that an open `cache.db` blocks deleting the Build on Windows (WinError 32).

## Answer

Grilled with the researcher, 2026-11-07. Code read at `app/app_cache.py`, `app/ps_cache.py`, `app/rs_cache.py`, `app/server.py`, `bundle/make.py`, plus [the switching findings](../research/03-switch-builds.md). Facts that shaped it: the job store holds only short-lived handles and a signing secret, keyed by args that include the Build; Removal Sensitivity and Parameter Selection results are already per Build, keyed with `build_id`; a full Parameter Selection Run is about 8½ min per Build on 12 workers.

1. **Switching: the Build is in the tab's URL** (option B, [ADR 0006](../../../docs/adr/0006-build-per-tab-in-the-url.md)). `/build/<snapshot_id>/<build_id>` through Dash Pages. Each tab holds one Build; a switch navigates and rebuilds the page from the layout. The server resolves the id under the builds root and never accepts a path from the browser. `/` redirects to the startup Build (`--build`, else root `latest`). Open Network State with another Build's export navigates to that Build's URL and reopens the export there, which fixes today's half-switch.
2. **Kept across a switch:** the Interface Language, the open mode, and the dataset if the new Build has one with the same name (else its first). Network State settings (g, s, resolution, hidden and removed tags) reset to the new Build's network defaults.
3. **Unnecessary recalculation** means recomputing something the Build already cached. Caches stay per Build only; nothing is reused across Builds, even with identical Top-N rows. Cross-Build reuse can be added later without breaking this.
4. **Running jobs on a switch:** a confirmation ("N running jobs will be cancelled; finished parts stay cached"), then that tab's Removal Sensitivity and Parameter Selection jobs are cancelled. Never left orphaned, never blocking.
5. **A Build run from a draft** is a server-wide job, one at a time per app process, in a background process, shown on its draft. Switching or closing the tab never cancels it.
6. **Parameter Selection for a new Build** runs on demand (Run in the Parameter Selection mode). Nothing runs at creation; the bundle maker is unchanged.
7. **Caches:** a Build made in the app writes `<build>/app_cache/`, like a CLI Build. Clear app cache (button and `--clear-cache`) clears the open Build only. Delete removes the folder, cache included, cancelling any job running on that Build first (the confirmation says so). No clear-all command.
8. **Job store:** one temporary folder per app process under the OS temp directory, removed at exit. Never inside a Build or a bundle; two processes never share it.
9. **Missing Build:** a URL whose Build doesn't exist (stale bookmark, or deleted from another tab) shows "This Build no longer exists" with a link to the latest Build.
10. **"The open Build" for Delete** is the Build of the tab deleting. That refusal from [Build identity](07-build-identity-and-lifecycle.md) holds; deleting a Build another tab has open is allowed, and that tab falls under 9.
11. **App Bundles** get the same URLs and a switcher among the Builds they ship (hidden for a single-Build bundle), with no create, duplicate, delete or drafts.
12. **Glossary:** no new terms. **ADR:** [0006, Build per tab in the URL](../../../docs/adr/0006-build-per-tab-in-the-url.md).

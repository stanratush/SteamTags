# How does switching Builds keep caches apart and avoid recalculation?
Type: grilling
Status: open
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

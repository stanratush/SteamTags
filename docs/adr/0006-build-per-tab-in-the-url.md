# Each tab names its Build in the URL

The Tag Network app switches Builds in one process by giving each browser tab one Build, named in its URL as `/build/<snapshot_id>/<build_id>` (Dash Pages). A switch navigates the tab to the other Build's URL and the page is rebuilt from the layout. The server resolves the id under the builds root and never accepts a filesystem path from the browser. We chose this because every callback already reads the Build per request from a per-tab store, so only the layout needed a per-tab source, and rebuilding the page from it leaves nothing stale. It also lets two tabs show two Builds side by side for comparison.

## Considered Options

- **A cookie plus reload.** Cheapest, but a cookie is shared by every tab, and by every app on `127.0.0.1` whatever the port, so tabs on different Builds would fight over it at their next reload.
- **An in-place swap by callback.** No reload, but every Build-dependent prop must be updated by hand. Today's cross-Build Open Network State shows how easily one is missed.
- **Restarting the server through a parent process.** Slow, needs a supervisor loop in the CLI, and running jobs must be killed and the port handed over.
- **One Dash app per Build under a URL prefix.** One app per Build, module globals shared across them, and runtime mounting through an undocumented route.

## Consequences

- `/` redirects to the startup Build (`--build`, else the root `latest`). A URL whose Build is gone shows "This Build no longer exists" with a link to the latest Build.
- "The open Build" means the Build of the current tab. Delete is refused only there. Other tabs on a deleted Build fall back to the missing-Build page.
- Open Network State with another Build's export becomes a navigation to that Build's URL.
- The background job store lives in a per-process temporary folder, not in a Build folder, so an open `cache.db` never blocks deleting a Build on Windows.
- Decided in `.scratch/build-management/issues/10-switching-and-cache-separation.md`. Options and Dash facts: `.scratch/build-management/research/03-switch-builds.md`.

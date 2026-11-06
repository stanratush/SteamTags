# Can one app process switch Builds without a restart?
Type: research
Status: resolved
Blocked by:

## Question

The app binds one Build when it starts. `create_app(build_path)` loads one `BuildContext`, `build_layout(ctx)` fills the relabel registry, the callbacks read it, and the background job store is `<build>/app_cache/jobs`. What does Dash (the version in `uv.lock`) allow for switching Builds in place?

- Can the layout function and the callbacks resolve the Build per request or per browser session (e.g. from a `dcc.Store` or the URL) instead of from a module-level context?
- Can `DiskcacheManager` background callbacks use one job store per Build, or does one manager per app force a shared store?
- Is a lighter route sound: restarting the server process from inside the app, or serving several Builds under URL prefixes?
- Known pitfalls: stale client-side state, `suppress_callback_exceptions`, the i18n relabel registry being filled once.

Answer from the Dash and diskcache documentation and source, cited, plus a reading of this repo's `app/` modules. Findings go in `research/03-switch-builds.md`.

## Answer

Checked against Dash 4.4.1 and diskcache 5.6.3 (`uv.lock`), from the installed source.

- **Yes, in one process.** Every callback already loads the Build per request from the per-tab `build-path` store. The Build is bound at startup in only a few places: `app/server.py:29-38`, the layout's Build-dependent values (`app/layout.py:235-327`, `:463`) and the Parameter Selection stores (`app/ps_view.py:987-1031`).
- **The layout function runs on every page load, but it sees no query string.** It can read cookies (as the language does) but not the URL. To get a Build per tab from the URL, use Dash Pages (`/build/<id>`) or a callback-rendered body.
- **A background manager is fixed when a callback is registered, never per request.** One job store per Build would mean one callback per Build. It is also unnecessary: the store holds only short-lived job handles keyed by args that include `build_path`. The real caches (`rs_cache`, `ps_cache`) are already per Build on each call.
- **Move the job store out of `<build>/app_cache/`.** On Windows an open diskcache `cache.db` blocks deleting the Build (WinError 32, measured). diskcache's connections are per thread and per process, so it cannot be closed reliably while the app runs.
- **Relabel registry:** its ids are the same for every Build (measured: 210 entries, same order). Three entries close over the startup Build and go stale after a switch: `brand-build`, `ps-run-one`, `ps-s-defining`.
- **Latent bug today:** Open Network State… with another Build's export switches `build-path` but leaves the dataset and Genre Tag options, the header and `ps-active` on the startup Build. `ps-active` keeps its `build_id`, so Parameter Selection keys go wrong.
- **Restart:** sound only with a parent process (the bundle launcher is one; the CLI is not). Running jobs must be terminated first, since multiprocess joins non-daemon children at exit. The port must be kept and the page reloaded.
- **URL prefixes:** possible (`url_base_pathname`, Werkzeug `DispatcherMiddleware`). Costs: one Dash app per Build, module globals shared by all of them, and no new routes after the first request.
- **Options for grilling:** A cookie plus reload (cheapest), B Build in the URL via Pages, C in-place swap by callback, D supervisor restart, E URL prefix per Build. Costs and risks are in the findings.

[Findings](../research/03-switch-builds.md)

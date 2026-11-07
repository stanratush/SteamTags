# How does the bundle maker pick in-app Builds, and what does a Bundle show of their names and lineage?
Type: grilling
Status: resolved
Blocked by:

## Question

`steamstudy bundle` always ships `latest` plus each `--build <build_id>`. It names the zip `tag-network-<build_id>-<targets>.zip` and runs Parameter Selection for every Build it carries (`bundle/make.py`, [releasing guide](../../../docs/releasing-an-app-bundle.md)). Builds made in the app have a required name, a description and a parent ([Build identity](07-build-identity-and-lifecycle.md)). Delete moves `latest`. An Import Build lives under `builds/<import_id>/` and is self-contained ([export schema](13-export-schema.md)). A Bundle gets the Build tree for switching only ([Build menu](12-build-menu.md)).

Decide:
- whether `latest` stays the implicit default once Builds are made often in the app, or a Bundle names its Builds explicitly, and whether `--build` accepts a Build's name as well as its id;
- whether Import Builds can be bundled (the Import folder is not shipped), and with what checks;
- whether the zip name and `bundle.json` carry the Build's name, and how the bundled tree shows a parent that is not in the Bundle;
- whether the bundle maker refuses or warns about a Build with a failed draft, a test Snapshot, or a lightweight-only source.

## Answer

Grilled with the researcher, 2026-11-07. Code read at `src/steamstudy/bundle/make.py` (`make_bundle`), `docs/releasing-an-app-bundle.md`, and the [Build identity](07-build-identity-and-lifecycle.md) answer.

**Facts that shaped it.** `write_build` points both `latest` pointers at the Build just written, so every menu save becomes `latest`. The maker ships `latest` plus each `--build`, copying only `builds/<snapshot>/<build_id>/` without `app_cache/`: drafts and Snapshots never ship. Nothing refuses a test Build today; only the guide warns. `build.json` stores `parent_build_id`, not the parent's name.

1. **Explicit Builds.** `steamstudy bundle` needs at least one `--build`; `latest` is no longer implicit. The first one named opens by default (the Bundle's own `latest` pointers name it). `--build latest` stays as a shorthand. The releasing guide's command gains that argument.
2. **Naming a Build.** `--build` accepts a `build_id`, `<snapshot_id>/<build_id>`, a name, or `<snapshot_id>/<name>` (names compared ignoring case, as at save). A name that matches Builds on more than one Snapshot is refused, listing the matches.
3. **Import Builds** can be bundled, mixed with Steam Builds, with the same treatment and no extra checks: Parameter Selection runs, the path-length check applies, and the `imports/` folder is not shipped (the Import Build is self-contained).
4. **Names in the Bundle.** The zip name is unchanged (`tag-network-<build_id>-<targets>.zip`, after the default Build), since names are free text. Each `bundle.json` Build entry gains its name, description and `parent_build_id`, and `READ ME FIRST.txt` lists each name beside its id.
5. **Lineage in the bundled tree.** The maker looks up each parent's name at make time and writes it into `bundle.json`. The tree has a top level per Snapshot (no `config/` root, no drafts). A Build whose parent is in the Bundle nests under it; one whose parent is not is a top-level row "from <parent name> (not in this Bundle)", or "from a deleted Build" when the parent was already gone at make time.
6. **Checks.**
   - A Build from a test Snapshot is refused unless `--allow-test` is passed (test bundles only, like `--skip-parameter-selection`).
   - Failed drafts: nothing to check (a failed run is not a Build; drafts never ship).
   - A Build made from a lightweight Snapshot: no check (byte-identical apart from `snapshot_form`; no Snapshot ships).
   - Two Builds with the same Snapshot and config hash in one Bundle: a warning naming both, like the save-time warning.
7. **Glossary / ADR:** none. The App Bundle definition already says it carries the Builds it opens; ADR 0001 is unchanged. Each choice is cheap to reverse.

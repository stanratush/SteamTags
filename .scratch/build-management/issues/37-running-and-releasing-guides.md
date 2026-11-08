# 37: Running Guide and releasing guide

**What to build:** the Running Guide covers Lightweight Snapshots, Imports, the new folder layouts and the Build menu. The releasing guide's bundle command names its Builds. English only.

**Blocked by:** 23, 25, 34

**Status:** done

Spec: [Build management spec](../spec.md): "Documentation" (Running Guide, releasing guide), "Lightweight Snapshots", "Imports", "Bundles". Decision tickets: [User Guide outline](15-user-guide-outline.md) (point 9), [bundles and in-app Builds](16-bundles-and-in-app-builds.md).

- [x] Running Guide changes:
  - *Build* says the datasets and List Sizes come from config, and documents `--from-raw`, `--name` and `--import`;
  - a new *Lightweight Snapshots* section after *Collect* (`snapshot lighten`, `verify-light`, the automatic lightening, staleness, moving a Snapshot as one zip);
  - a new *Import* section after *Build*;
  - *Folder layouts* gains `imports/`, Import Builds, `drafts/`, `<snapshot_id>.light.zip`, and the job store's move to the OS temp directory;
  - *The app* links User Guide chapter 7.
- [x] Releasing guide: the bundle command with `--build` (by name or id; the first one opens by default), `--allow-test` for test bundles only, the identical-settings warning, and what a Bundle shows of names and lineage.
- [x] Before editing either file, check that `git status` shows it clean. If either carries the researcher's uncommitted work, stop and say so in Comments.

## Comments

## Implementation note

Both files were clean in `git status` before editing. Running Guide changes:
- *Build* documents `--name`, `--from-raw` and `--import`, and says that datasets, List Sizes and Tag Depth come from `config/datasets.toml`.
- New *Lightweight Snapshots* section (after Collect): lighten, verify-light, automatic lightening on close and after repair, staleness, moving a Snapshot as its zip.
- New *Import* section (after Build): `steamstudy import`, `--filter`, `--attributes`, `imports/failed/`, `build --import`.
- *Folder layouts* gains `.light.zip`, `imports/`, `imports/failed/`, `drafts/` and Import Builds, plus the job store's move to the OS temp folder.
- *The app* mentions per-tab URLs and the Build menu, with a link to chapter 7.
- *Making an App Bundle* documents the required `--build` and `--allow-test`.

Releasing guide changes:
- The build command adds `--name`.
- The bundle command names its Builds; the first one opens by default.
- It covers `--allow-test`, the identical-settings warning, and what a Bundle shows of names and lineage.
- The 2026-10-09 example gains a note on today's equivalent command.


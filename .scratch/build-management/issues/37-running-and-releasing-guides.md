# 37: Running Guide and releasing guide

**What to build:** the Running Guide covers Lightweight Snapshots, Imports, the new folder layouts and the Build menu. The releasing guide's bundle command names its Builds. English only.

**Blocked by:** 23, 25, 34

**Status:** ready-for-agent

Spec: [Build management spec](../spec.md): "Documentation" (Running Guide, releasing guide), "Lightweight Snapshots", "Imports", "Bundles". Decision tickets: [User Guide outline](15-user-guide-outline.md) (point 9), [bundles and in-app Builds](16-bundles-and-in-app-builds.md).

- [ ] Running Guide changes:
  - *Build* says the datasets and List Sizes come from config, and documents `--from-raw`, `--name` and `--import`;
  - a new *Lightweight Snapshots* section after *Collect* (`snapshot lighten`, `verify-light`, the automatic lightening, staleness, moving a Snapshot as one zip);
  - a new *Import* section after *Build*;
  - *Folder layouts* gains `imports/`, Import Builds, `drafts/`, `<snapshot_id>.light.zip`, and the job store's move to the OS temp directory;
  - *The app* links User Guide chapter 7.
- [ ] Releasing guide: the bundle command with `--build` (by name or id; the first one opens by default), `--allow-test` for test bundles only, the identical-settings warning, and what a Bundle shows of names and lineage.
- [ ] Before editing either file, check that `git status` shows it clean. If either carries the researcher's uncommitted work, stop and say so in Comments.

## Comments

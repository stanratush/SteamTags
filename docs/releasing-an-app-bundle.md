# Releasing an updated App Bundle

How to turn a code update into a new App Bundle and hand it to researchers. The [Running Guide](running-guide.md#making-an-app-bundle) describes what `steamstudy bundle` does and its options; this page is the checklist to follow each time the app changes. [ADR 0001](adr/0001-app-bundle-wheels-not-frozen.md) explains why a bundle is wheels plus a launcher.

Two things make this checklist necessary:

- **A bundle is made from the working tree as it is.** `steamstudy bundle` runs `uv build` on the repository, so the `steamstudy` wheel holds whatever `src/` and `docs/user-guide/` contain at that moment, committed or not, on whatever branch is checked out.
- **Nothing inside a bundle names the code it came from.** The `steamstudy` version stays `0.1.0` and `bundle.json` records no commit. The zip is named only after its latest Build and its targets (`tag-network-<build_id>-<targets>.zip`), so a bundle made from new code with the same Build gets the **same file name** as the old one and replaces it in `bundles/`.

## 1. Pick the code

Check out the code you want researchers to run, and make sure nothing that ships is uncommitted:

```bash
git status --short -- src docs/user-guide pyproject.toml uv.lock
```

This must print nothing. Then note the commit; you will use it to name the bundle and in the hand-over message:

```bash
git rev-parse --short HEAD
```

If the update lives on a feature branch, decide first whether to merge it into `main` and bundle from `main` (preferred: a bundle then matches a commit everyone can find) or bundle from the branch.

Uncommitted changes elsewhere do not reach the bundle. `config/collection.toml` never affects a Build or a bundle; any other `config/` file changes the next Build's `build_config_hash` and must be logged in `config/CHANGELOG.md` first.

## 2. Sync and test

```bash
uv sync
```

```bash
uv run python -W default -X faulthandler -m pytest
```

Run the full suite, including the `slow` App Bundle acceptance test (`tests/test_bundle_acceptance.py`, about six minutes): it makes a Windows bundle, installs it with no package index on every local Python and loads a dataset. Then type-check:

```bash
uv run mypy
```

Do not bundle while anything fails.

## 3. Decide whether you need a new Build

A bundle carries Builds, and a Build is not remade when the code changes. **App-only changes** (`src/steamstudy/app/`, the User Guide) never need a new Build: the app computes every Network State itself from the Build's datasets.

Make a new Build when any of these changed since the Build the bundle carries:

- a `config/` file other than `collection.toml` (the new Build gets a new `build_config_hash`);
- the Snapshot (a new collection or a `--repair`);
- code under `src/steamstudy/build/`, `analysis/` or `network/`, if the Build's own reports (`analysis/report.html`, the network tables) should match what the app now shows;
- a library version in `uv.lock` that the app computes with (otherwise the app shows the library-version banner, because the bundle installs `uv.lock`'s versions, not the Build's).

To see what changed, compare with the commit of the previous bundle:

```bash
git diff --stat <previous-commit> HEAD -- src/steamstudy/build src/steamstudy/analysis src/steamstudy/network config uv.lock
```

```bash
uv run steamstudy build --snapshot <snapshot_id>
```

makes the new Build and makes it `latest`. Always name the Snapshot: without `--snapshot` the Build uses the newest one, which may be a test Snapshot made after the full one (`snapshot.json` says `mode: test`), and a bundle must never carry a test Build. It never touches the old Build, and its new `build_id` also gives the zip a new name.

**Keep the previous Build in the bundle** when researchers may have exported Network States from it: **Open Network State…** only opens an export whose Build (by `build_id` and `build.json` hash) is in the bundle. Add it with `--build` in the next step.

## 4. Make the bundle

Write each release to its own folder named after the commit, so it never replaces an earlier zip:

```bash
uv run steamstudy bundle --target windows --target macos --target linux --out bundles/<commit>
```

Drop the `--target` options to make it for this computer's system only (about 220 MB per target). Add `--build <build_id>` for each extra Build to carry; the latest Build is always included and opens by default.

The command needs internet only for wheels it has not cached yet: they go to `bundles/<commit>/.cache/wheels/` when you use `--out`, so copy `bundles/.cache/` there first to avoid downloading them again. It refuses, writing nothing, if a Build does not exist or `uv.lock` lacks a wheel for some target and Python. When it finishes it logs the zip's path and size.

**Making a bundle runs Parameter Selection for every Build it carries.** It recomputes each dataset's grid and the validation of its default-constraint pair, under the shipped code's default Selection Settings, into the bundle's copy of the Build. That takes about 8½ minutes per Build on 12 workers (`[parameter_selection] workers` in `config/network.toml`), so a two-Build bundle needs about 17 minutes more than before. It logs one line per Build, dataset and phase as each finishes, for example `Build 20261008T221504Z-7a23ae9f, puzzle: grid 153 of 153 pairs, about 6 min left`.

Your own `app_cache/` is never shipped or changed; it is only compared with the fresh results. A warning that **the maker's Parameter Selection cache differs from the fresh result** means your cache was made by older code that computed something differently without bumping `selection.METHOD_VERSION` or `validation.METHOD_VERSION`. The bundle still ships the fresh result, so the release is fine, but fix the code before the next release: bump the method version that the change affected, so that old caches are no longer read as current. Clearing your app cache makes the warning go away without fixing that.

**Never use `--skip-parameter-selection` for a release.** It makes a bundle without results, for quick test bundles only; researchers would then have to run every grid themselves.

## 5. Check the bundle like a researcher would

Extract it to a fresh folder outside the repository, at a **short path**, and start it with a Python other than the repository's `.venv`. On Windows, a deep folder (such as one under `%TEMP%`) makes the first start fail with `[WinError 206] The filename or extension is too long` while scikit-learn loads its DLL, even with long paths enabled: Windows does not allow longer paths when loading a DLL, and the bundle's own folder name and `environment/` add about 150 characters.

```bash
python -m zipfile -e bundles/<commit>/tag-network-<build_id>-<targets>.zip ../bundle-check
```

(Git Bash's `tar` cannot read zip files; `python -m zipfile` works in every shell.)

Then double-click `Start Tag Network.bat` in the extracted folder (or run `py -3 start_tag_network.py` there). Check that:

- the first start sets up the environment and opens the app in the browser;
- `READ ME FIRST.txt` lists the Builds and systems you meant, and the right Build opens;
- no library-version banner appears (one means the Build was made with other library versions: go back to step 3);
- the update itself is visible (look for the change you are releasing);
- if you included an older Build, an export made from it opens with **Open Network State…**;
- the **Parameter Selection** mode opens on finished results with no Run: every dataset in the strip shows its ★ pair (or "no qualifying pair"), and every row in the Run section reads "grid done, validated" ("grid done, not validated" only for a dataset with no qualifying pair);
- the provenance line under Run names the computer the bundle was made on, for example "Computed when this bundle was made: Python 3.14.8, Windows AMD64, 2026-10-27". It appears only when the Python version or system differs from the one checking, so start the bundle with a Python version other than the maker's to see it. A banner ending "Clear app cache and Run to recompute here" instead means an app library differs from the maker's: go back to step 2.

Delete `../bundle-check` afterwards. macOS and Linux bundles can only be checked for completeness here; they have not been tested on real hardware.

## 6. Hand it over

Send the zip and say which commit and Build it carries. Ask researchers to:

1. extract it to a **new** folder with a short path (on Windows, for example `C:\TagNetwork`, not deep inside Downloads or Documents) rather than over the old bundle's folder;
2. start it as before (the first start takes about a minute again);
3. delete the old folder once the new one works, after copying out any exports they saved inside it.

Extracting over the old folder would also work (the launcher rebuilds its environment whenever `bundle.json` changes), but it keeps the old folder's app cache (Removal Sensitivity and Parameter Selection results) and any Build the new bundle no longer carries.

A message like this is enough:

> New Tag Network App Bundle (code `<commit>`, Build `<build_id>`): `<what changed>`. Extract it to a new folder with a short path (e.g. `C:\TagNetwork`) and double-click "Start Tag Network.bat" (macOS: "Start Tag Network.command"). Once it works, delete the old bundle folder.

## Example: the graph-readability update (2026-10-09)

The last bundles (`bundles/tag-network-20261006T062622Z-7a23ae9f-*.zip`, 6 October) predate about 50 commits on the `graph-readability` branch (the readable layout, Tidy, the metric help, edge thickness by Clustering Weight), which is not yet merged into `main`. Those commits also changed `analysis/templates.py`, `analysis/network_stage.py` and `network/` (layout moved downstream of analysis, [ADR 0002](adr/0002-layout-is-downstream-of-analysis.md)), and Build `20261006T062622Z-7a23ae9f` still records `dash-cytoscape` in its `software_versions`. So this release got a new Build, with the old Build kept for existing exports. It was made straight from the branch at `0e37893`:

```bash
uv run steamstudy build --snapshot 20261005T062558Z-full
```

```bash
uv run steamstudy bundle --target windows --target macos --target linux --build 20261006T062622Z-7a23ae9f --out bundles/0e37893
```

The result is `bundles/0e37893/tag-network-20261008T221504Z-7a23ae9f-windows-macos-linux.zip` (655 MB), carrying Build `20261008T221504Z-7a23ae9f` (opens by default) and `20261006T062622Z-7a23ae9f`. The tests passed except `test_shipped_config_loads_with_spec_defaults`, which failed only because of an uncommitted local edit to `config/collection.toml`; that file reaches neither a Build nor a bundle. Started from a short path with Python 3.13, the bundle set up its environment, opened both Builds without a banner and showed the update (Tidy, "Edge thickness: shared games" in the key).

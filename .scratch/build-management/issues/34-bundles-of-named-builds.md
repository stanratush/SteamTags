# 34: Bundles of named Builds

**What to build:** `steamstudy bundle` takes explicit `--build`s (by id, name or `<source_id>/…`). The first one opens by default. `bundle.json` and the README carry names, descriptions and parents. The bundled tree shows lineage, Import Builds bundle like Steam ones, and test Builds need `--allow-test`.

**Blocked by:** 24, 26, 28

**Status:** done

Spec: [Build management spec](../spec.md): "Bundles". Decision ticket: [bundles and in-app Builds](16-bundles-and-in-app-builds.md).

- [x] At least one `--build` is required, and `latest` is no longer implicit. `--build latest` stays a shorthand. The first one named is the Bundle's `latest` and opens by default.
- [x] `--build` resolves a `build_id`, `<source_id>/<build_id>`, a name, or `<source_id>/<name>` (case-insensitive). An ambiguous name is refused, listing the matches.
- [x] Import Builds are copied from `builds/<import_id>/<build_id>/` (without `app_cache/`). Parameter Selection runs and the path-length check applies. `imports/` is never shipped.
- [x] `bundle.json` Build entries gain name, description, `parent_build_id`, and the parent's name looked up at make time (or "deleted"). `READ ME FIRST.txt` lists each name beside its id. The zip name is unchanged.
- [x] The bundled tree (issue 28's switching-only mode) has a top level per source. A Build nests under its parent when the parent is in the Bundle; otherwise it is a top-level row "from <parent name> (not in this Bundle)" or "from a deleted Build".
- [x] A test-Snapshot Build is refused without `--allow-test`. Two Builds with the same source and config hash warn, naming both.
- [x] Tests (extend `test_bundle.py`):
  - The resolution forms, and the ambiguity refusal.
  - The first `--build` is `latest`.
  - The lineage labels, for a parent inside the Bundle, outside it, and deleted.
  - Refusal without `--allow-test`, and the identical-settings warning.
  - A bundle with an Import Build opens it.

## Comments

## Implementation note

`bundle/make.py` gains `resolve_bundle_build`, which accepts `latest`, a `build_id`, `<source_id>/<build_id>`, a name or `<source_id>/<name>` (case-insensitive) and refuses an ambiguous name, listing the matches. It also gains `build_entry`, which builds the `bundle.json` `build_entries` entry: name, description, `parent_build_id` and the parent's name at make time, or "deleted".

`make_bundle(builds=…)` needs at least one Build. The CLI's `--build` is required and `--build latest` stays a shorthand. The first Build named is the Bundle's `latest`, and each source's first named Build is that source's `latest`. Test-Snapshot Builds need `allow_test` / `--allow-test`. Two Builds with the same source and config hash log a warning naming both. `READ ME FIRST.txt` lists each Build's name beside its ref.

`build_tree` reads the recorded parent name. It shows "from <name> (not in this Bundle)", or "from a deleted Build" when the parent was already gone at make time. Import Builds are copied like Steam ones (without `app_cache/`), with Parameter Selection and the path-length check; `imports/` is never shipped.

Tests in `tests/test_bundle.py` cover:
- the resolution forms and the ambiguity refusal
- the first Build named is `latest`, plus the entries and README
- the lineage labels: parent inside the Bundle, outside it, and deleted
- the `--allow-test` refusal and the identical-settings warning
- an Import Build bundle that opens

The existing bundle tests now pass `builds=["latest"]` and `allow_test=True`.


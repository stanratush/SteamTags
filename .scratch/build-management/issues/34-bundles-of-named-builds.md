# 34: Bundles of named Builds

**What to build:** `steamstudy bundle` takes explicit `--build`s (by id, name or `<source_id>/…`). The first one opens by default. `bundle.json` and the README carry names, descriptions and parents. The bundled tree shows lineage, Import Builds bundle like Steam ones, and test Builds need `--allow-test`.

**Blocked by:** 24, 26, 28

**Status:** ready-for-agent

Spec: [Build management spec](../spec.md): "Bundles". Decision ticket: [bundles and in-app Builds](16-bundles-and-in-app-builds.md).

- [ ] At least one `--build` is required, and `latest` is no longer implicit. `--build latest` stays a shorthand. The first one named is the Bundle's `latest` and opens by default.
- [ ] `--build` resolves a `build_id`, `<source_id>/<build_id>`, a name, or `<source_id>/<name>` (case-insensitive). An ambiguous name is refused, listing the matches.
- [ ] Import Builds are copied from `builds/<import_id>/<build_id>/` (without `app_cache/`). Parameter Selection runs and the path-length check applies. `imports/` is never shipped.
- [ ] `bundle.json` Build entries gain name, description, `parent_build_id`, and the parent's name looked up at make time (or "deleted"). `READ ME FIRST.txt` lists each name beside its id. The zip name is unchanged.
- [ ] The bundled tree (issue 28's switching-only mode) has a top level per source. A Build nests under its parent when the parent is in the Bundle; otherwise it is a top-level row "from <parent name> (not in this Bundle)" or "from a deleted Build".
- [ ] A test-Snapshot Build is refused without `--allow-test`. Two Builds with the same source and config hash warn, naming both.
- [ ] Tests (extend `test_bundle.py`):
  - The resolution forms, and the ambiguity refusal.
  - The first `--build` is `latest`.
  - The lineage labels, for a parent inside the Bundle, outside it, and deleted.
  - Refusal without `--allow-test`, and the identical-settings warning.
  - A bundle with an Import Build opens it.

## Comments

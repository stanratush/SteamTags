# 24: Build identity, drafts and lifecycle (Dash-free)

**What to build:** Builds get a name, description and parent in `build.json`. A Dash-free module manages Build Drafts (create, save, list, discard, build), Duplicate, identical-settings detection and Delete, including moving `latest`. `steamstudy build` gains `--name`. The app and the menu (issues 27–29) call this module and nothing else.

**Blocked by:** 20

**Status:** done

Spec: [Build management spec](../spec.md): "Build identity and lifecycle", "Resolved while writing this spec" (`source_id`, drafts are menu-only). Decision ticket: [Build identity](07-build-identity-and-lifecycle.md).

- [x] `build.json` gains `name`, `description` and `parent_build_id` (`<source_id>/<build_id>` or null). The description is appended as the Build's own changelog entry after the inherited entries. None of them enters `build_id` or the config hash. Old `build.json` files read with name = `build_id` and no description or parent; they are never rewritten.
- [x] `steamstudy build --name <name>`; the default name is the `build_id`. Names are unique per source, ignoring case, across Builds and drafts; a clash is refused.
- [x] A module (e.g. `steamstudy/build_admin.py`):
  - `start_draft(source_id, from_build=None)` copies the complete config from `config/` or from a Build (through the old-shape converter of issue 19), with parent set;
  - `save_draft` writes atomically to `builds/<source_id>/drafts/<name-slug>.json` (the `build.json` `config` block plus name, description, parent);
  - `list_drafts`, `discard_draft`;
  - `build_draft(draft, on_progress, should_stop)`: on success the draft is removed and `latest` moves as `write_build` does today; on failure the draft keeps a `last_failure` (parse-error count and the `failed/` CSV path, or the causal word and sentence), and that `failed/` file is deleted when the draft later builds or is discarded;
  - `duplicate(build, target_source_id)` gives a draft with parent set;
  - `identical_builds(source_id, config_hash)` names the matches and whether their software versions differ;
  - `delete_build(build, open_build)` refuses the caller's open Build, removes the folder (cache included), moves the per-source and root `latest` pointers to the newest remaining Build (by `build_id` timestamp) or removes them, and returns what the confirmation lists: sizes, `bundles/` zips whose name contains the `build_id`, where `latest` moves, and the Builds and drafts that lose their parent.
- [x] `config/` is never written by this module.
- [x] Tests:
  - Name clash (case-insensitive, against a draft too) is refused. A CLI Build is named after its `build_id`.
  - A draft survives a process restart. A failed draft build keeps the draft and its failure, and a later success removes both the draft and the `failed/` file.
  - Duplicate onto another Snapshot records the parent. Deleting the parent shows the child as "from a deleted Build".
  - Delete moves both `latest` pointers correctly, removes a pointer with no Build left, and refuses the open Build.
  - An identical-settings Build is allowed and reported, with the version difference flag.

## Comments

Implemented in `steamstudy/build_admin.py` (lifecycle) and `steamstudy/builds.py` (`BuildInfo`, `list_builds`: read-only, importable by the app without the pipeline). `build()` takes a `BuildIdentity` (name, description, parent, inherited changelog); `config.build_config` reads a `config` block alone and `config.exclusions_new_shape` is the old-shape converter for drafts. Delete is split into `deletion_plan` (what the confirmation lists) and `delete_build`; cancelling jobs on the Build stays with the app (issue 28). Tests: `tests/test_build_admin.py`.

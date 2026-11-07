# What is a Build's identity and lifecycle?
Type: grilling
Status: resolved
Blocked by:

## Question

Charted: a Build is immutable. Save = the Build is written; duplicate = a new Build from another Build's settings; delete = its folder and cache are removed. Today `build_id` = UTC timestamp + config hash, under `builds/<snapshot_id>/<build_id>/`, with `latest` pointers and a `failed/` folder.

Decide:
- whether a Build gets a user-given name beside its id, and whether it records its **parent** when duplicated;
- whether unsaved **settings drafts** exist (edit, close the app, come back), or a Build's settings exist only once it has been run;
- what delete does to the `latest` pointer and to exports and bundles that name the Build, and whether some Builds (e.g. a published one) are protected;
- deleting the Build that is open, given that Windows blocks deleting a folder whose job store is open ([Can one app process switch Builds?](03-switch-builds-in-one-process.md));
- how failed Builds (parse errors, a causal word in a report) are shown and cleaned up;
- whether two Builds with identical settings from the same Snapshot may coexist, or the second is refused. Today such Builds differ only in `build_id`, which is also in every `state_id`, and in the recorded software versions ([What does a Build read from a Snapshot?](02-build-inputs-and-timings.md));
- where config lives once the menu edits it: still `config/`, or only in each Build's settings.

## Answer

Grilled with the researcher, 2026-11-07. Code read at `src/steamstudy/build/core.py` (`new_build_id`, `_build_json`), `build/writer.py`, `builds.py`, `app/export.py` (`_find_build`), `bundle/make.py`, `cli.py` (`_build`), and `builds/` on disk.

**Facts that shaped it.** `build_id` is `<UTC timestamp>-<build_config_hash[:8]>`. The two full-Snapshot Builds already share hash `7a23ae9f`, so identical-settings Builds coexist today. `build.json` copies every config file except `collection`, plus the `config/CHANGELOG.md` entries. Opening an exported Network State needs the same `build_id` and the same `build.json` hash. `write_build` writes both `latest` pointers to the Build just written. A parse failure writes `builds/<snapshot>/failed/<build_id>-parse_errors.csv`; a causal-word failure writes nothing. Bundles are self-contained zips named `tag-network-<build_id>-<targets>.zip`. Nothing in the repo marks a Build as published.

1. **Name.** Every Build has a required **name** beside its `build_id`. It is stored in `build.json`, fixed at save (renaming would change the `build.json` hash and break opening exports), and part of neither `build_id` nor the config hash. It is unique within its Snapshot, ignoring case, across both Builds and drafts; a clash is refused when the draft is saved. It is shown beside the id wherever the id is shown. CLI Builds default the name to their `build_id`.
2. **Description.** A menu Build also requires a short **description** of why it exists. It is stored in `build.json` as that Build's own changelog entry, after the entries inherited from its starting point, so the changelog stays complete.
3. **Parent.** A duplicated Build records `parent_build_id` as `<snapshot_id>/<build_id>`, shown as "from <parent name>", or "from a deleted Build" once the parent is gone. It is only information: nothing reads it.
4. **Duplicate onto another Snapshot.** Duplicate lets you pick the Snapshot, defaulting to the parent's. Settings that don't fit the new Snapshot (e.g. a Manual Metadata Entry for a game the store now provides) fail that Build through today's validation.
5. **Drafts.** Unsaved settings persist as a **Build Draft**: the complete settings, copied when the draft is started from `config/` or from a Build (never a set of changes on its source), with its name, description and parent. Drafts are saved automatically, survive closing the app, are listed in the menu, and can be any number per Snapshot. They are stored at `builds/<snapshot_id>/drafts/<name-slug>.json`, in the shape of `build.json`'s `config` block plus name, description and parent. A successful Build uses its draft up. A failed one keeps it. You discard drafts explicitly.
6. **Where config lives.** `config/` stays the repository's hand-edited defaults (with its CHANGELOG) and the CLI's input. The menu never writes it. Each Build's settings live in its `build.json`, as they already do.
7. **Identical settings.** A Build with the same Snapshot and config hash as an existing one is allowed with a warning that names the existing Build and says whether the software versions differ (rebuilding after a code change is legitimate).
8. **Delete and `latest`.** When the Build a `latest` pointer names is deleted, the per-Snapshot pointer moves to the newest remaining Build of that Snapshot (by `build_id` timestamp), and the root pointer to the newest of any Snapshot. A pointer with no Build left is removed.
9. **Delete confirmation, no protection.** Delete shows an informational confirmation: zips in `bundles/` whose name contains the `build_id` (they keep working, since they carry their own copy), and that Network States exported from it will no longer open here. There is no protected flag: nothing marks a Build as published, and a flag would be mutable state on an immutable Build.
10. **Deleting the open Build** is refused: "switch to another Build first". This holds even after the job store moves out of the Build folder ([Can one app process switch Builds?](03-switch-builds-in-one-process.md)).
11. **Failed runs are not Builds**: no folder, no list entry. The failure is shown on the draft that produced it: the parse-error count with a link to the `failed/` CSV, or the causal word and its sentence. That `failed/` file is deleted when the draft is built successfully or discarded. The CLI is unchanged.
12. **Glossary:** Build adjusted (name, description, parent, identical settings allowed, a failed run is not a Build), and **Build Draft** added, in [CONTEXT.md](../../../CONTEXT.md). No ADR: each choice is cheap to reverse.

Left in the fog: how Bundles show names and parents (map, "Bundles and in-app Builds").

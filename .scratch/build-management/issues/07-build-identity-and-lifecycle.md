# What is a Build's identity and lifecycle?
Type: grilling
Status: open
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

# 29: Draft dialog shell, Start, Review and the Build run

**What to build:** a draft opens in a full-screen dialog of six steps with green/red markers and automatic saving. This issue builds the Start and Review steps (Review without the pool preview, which is issue 32) and the Build run: a server-wide background job, one at a time per process, shown as a strip under the header in every mode. The Top-N, Curation, Reports and Network steps are placeholders filled by issues 30–31.

**Blocked by:** 28

**Status:** done

Spec: [Build management spec](../spec.md): "The Build menu" (dialog, Start, Review, a running Build), "Switching Builds and caches" (Build run job), "Build identity and lifecycle". Decision tickets: [Build menu](12-build-menu.md), [switching and cache separation](10-switching-and-cache-separation.md).

- [x] The dialog has the steps Start, Changes the Top-N, Curation, Reports and analysis, Network defaults and Review. Markers go green when a step has changes and red when it needs a fix. Every edit saves the draft through `save_draft`. Close keeps the draft.
- [x] Start: name (clash refused, case-insensitive), description (required), started from, Snapshot or Import, and the last failure (parse-error count with a link to the `failed/` CSV, or the causal word and its sentence). For a raw-only Snapshot, a **Make lightweight Snapshot** button runs `lighten` (issue 23) as a server job.
- [x] Review lists:
  - every changed setting, with the source value struck through and the draft value beside it, and Top-N changes badged;
  - the identical-settings warning (from `identical_builds`), naming the Build and any version difference;
  - every problem still to fix, each linking to its step.

  Build is the only place a draft is built.
- [x] The Build run is a background process via `build_draft`, one at a time per app process, cancellable. Switching or closing the tab never cancels it. The draft row shows "running %".
- [x] The strip under the header shows the stage, seconds against the estimate (~24 s lightweight, ~99 s raw) and a bar. On success it offers "Open it in this tab" (no automatic switch). On failure it offers "Open the draft", and the dialog shows the failure.
- [x] bg entries for every string.
- [x] Tests:
  - A draft edited in the dialog survives a reload.
  - Review lists a changed setting.
  - A Build run completes on the test Snapshot and appears in the tree as `latest`, and the strip offers to open it.
  - A failing run (a causal word in a report setting) keeps the draft and shows the failure.
  - A second Build run waits for the first.

## Comments

## Implementation note

`app/draft_dialog.py` renders the six steps. It autosaves every field through `save_draft` with pattern ids `{"type": "dd-field", "name": …}` and marks steps green or red from `build_admin.changed_settings` and `draft_problems`. `app/build_runs.py` queues runs server-wide, one at a time, and they are cancellable between stages. The strip under the header (`build_menu.strip`) shows stage, seconds against the 24 s/99 s estimate and a bar, then offers "Open it in this tab" or "Open the draft". Make lightweight Snapshot is a run of kind `lighten`. Tests: an edit survives a reload and Review lists it, a run completes and becomes latest, a failing (causal word) run keeps the draft, a second run waits for the first.

Each run is its own process (`multiprocessing`, spawn). The queue's worker thread starts it and relays its stages, and passes Cancel to it as an event that `build_draft` checks between stages. The result comes back as a message. Any failure, not only `BuildFailed`, is saved on the draft. Test: a run builds even though this process's `build` is monkeypatched to fail, which proves the run happens in its own process.

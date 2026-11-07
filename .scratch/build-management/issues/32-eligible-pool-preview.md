# 32: Eligible Pool preview

**What to build:** a live, debounced preview of each dataset's Eligible Pool against its List Size, the would-be Overall ranks of excluded games, and the games entering and leaving Overall. It runs in the app process on the Build's own exclusion and ranking code, over source tables loaded once. Review gates **Build** on a preview that matches the current settings.

**Blocked by:** 23, 25, 30

**Status:** ready-for-agent

Spec: [Build management spec](../spec.md): "The Build menu" ("The Eligible Pool preview"), "Resolved while writing this spec" (entering and leaving Overall, the Import preview). Decision tickets: [Eligible Pool preview](18-eligible-pool-preview.md), [Eligible Pool timing](17-eligible-pool-timing.md); reference: [prototypes/17-eligible-pool-timing/measure.py](../prototypes/17-eligible-pool-timing/measure.py).

- [ ] A Dash-free `preview(records, settings) -> PoolPreview` covers manual-list validation, Manual Metadata, every rule, Content Flags, the datasets ranked and sliced, would-be Overall ranks, and the comparison Build's Overall list. It calls the same functions as the Build stage, with no second implementation.
- [ ] A source cache holds at most one loaded source per process: a Snapshot's lightweight tables (issue 23) or an Import's normalised tables (issue 25). It is loaded when a draft dialog first opens for that source (shown as "Loading Snapshot…" or "Loading Import…"), swapped when a dialog for another source opens, and dropped when the source changes (repair, new lighten, extract version).
- [ ] Recompute about 0.5 s after the last edit on the Top-N and Curation steps, and on entering Review. A newer edit supersedes a recompute in flight. While computing, the last numbers stay dimmed with a spinner.
- [ ] Cannot compute (invalid rule, override on an unknown rule, unknown attribute, missing Snapshot or Import): each number reads "—" with the reason, linking to the red step. A pool smaller than its List Size is a red problem ("Overall: 87 eligible, List Size 100").
- [ ] Raw-only Snapshot: no preview. The numbers read "Not previewed: this Snapshot has no lightweight form", Review says so, and Build stays on.
- [ ] Review's preview is keyed by a hash of the settings plus the source id and extract version (Imports: `import_sha256`). Build is off until Review shows a preview for the current key.
- [ ] Entering and leaving Overall compare with the draft's source Build, else the source's `latest`, else the line is left out.
- [ ] The Curation step's Override shortcut uses the would-be ranks.
- [ ] bg entries for every string.
- [ ] Tests:
  - On the fixture, the preview's pools, Top-N lists and ties equal the Build's for default settings and for three edited drafts (a rule's tags, Tag Depth, List Size).
  - Build stays off while the key is stale.
  - A raw-only Snapshot shows "Not previewed".
  - An invalid rule shows "—" with the reason.

## Comments

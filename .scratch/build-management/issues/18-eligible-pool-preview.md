# When does the Build menu show each dataset's Eligible Pool: live, on demand, or only at Review?
Type: grilling
Status: resolved
Blocked by: 17

## Question

Using the times from [the Eligible Pool timing task](17-eligible-pool-timing.md), decide:
- when the pool sizes (and the games entering the Overall list) are recomputed while a draft is edited: after every change, debounced, on a button, or only at Review;
- where the work runs (in the app process or as a server job like the Build run), and what the menu shows while it runs or when the draft cannot be computed (an invalid rule, a missing Snapshot);
- whether the preview is guaranteed to match the Build, and what Review says if it is stale.

## Answer

Grilled with the researcher, 2026-11-07, from [the Eligible Pool timing task](17-eligible-pool-timing.md) (load 2.8 s; warm preview 0.34 s Steam, 1.3 s largest Import; exact match with the raw records).

1. **When:** live and debounced, about 0.5 s after the last edit on the Top-N and Curation steps, and always again on entering Review. The Top-N step shows each dataset's Eligible Pool against its List Size; the Curation step's would-be Overall ranks (the Override shortcut) are live too.
2. **Where:** in the app process, as a plain callback, never a server job (the Build run queue would delay it). The lightweight tables are loaded once, the first time a draft dialog opens for that Snapshot or Import ("Loading Snapshot…", about 2.8 s). At most one loaded source per process: swapped when a dialog for another source opens, dropped when the source changes (repair, new lighten). The preview calls the Build's own exclusion and ranking code on those records; there is no second implementation. Memory use is unmeasured and is an implementation check.
3. **No lightweight form:** no live preview. The numbers read "Not previewed: this Snapshot has no lightweight form", and the Start step offers **Make lightweight Snapshot** as a server job. The draft can still be built from raw (about 99 s); the List Size check then happens in the Build.
4. **While computing:** the last numbers stay, dimmed, with a small spinner; a newer edit supersedes a recompute in flight, so the latest settings win. **Cannot compute** (invalid rule, Override on an unknown rule, unknown attribute, missing Snapshot or Import): each number reads "—" with the reason, linking to the step marked red. A pool smaller than its List Size is not a compute failure but a red problem on the Top-N step and in Review ("Overall: 87 eligible, List Size 100").
5. **Matching the Build:** guaranteed by construction (same code, same records) and by a test (preview against Build on the fixture, plus `verify-light`). Review's preview is keyed by a hash of the settings and the source's `snapshot_id` and extract version, and **Build** stays off until Review shows a preview for the current key, so a stale preview is never on screen at Build. The Build run recomputes everything and is the authority; a difference would be a bug, not a user-visible state. Without a lightweight form, Build stays on and Review says the pools are not previewed.
6. **No incremental reuse:** every recompute is a full preview. Ranking is kept separate from slicing, so a List Size edit is a re-slice for free. Reuse can be added later without breaking anything.

Glossary: no new terms (the preview is UI, not domain). ADR: none (easily reversed).

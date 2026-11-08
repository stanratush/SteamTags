# 36: User Guide chapters 7 and 8 and help anchors

**What to build:** `07-making-builds.md` and `08-imported-data.md`, in English and Bulgarian, with a help anchor per draft step wired to each step's `?`, and hover help on settings opening their chapter-3 entries.

**Blocked by:** 32, 33, 35

**Status:** done

Spec: [Build management spec](../spec.md): "Documentation", "The Build menu", "Imports". Decision ticket: [User Guide outline](15-user-guide-outline.md) ([outline](../prototypes/15-user-guide-outline/OUTLINE.md)).

- [x] Chapter 7 is procedural, with no **In short** blocks. Sections: the Build tree, Start a draft, one section per draft step (Start, Changes the Top-N, Curation, Reports and analysis, Network defaults, Review), A running Build, Manage and delete Builds, Raw and lightweight Snapshots. The Review section says Build stays off until the preview matches the current settings, and explains "Not previewed".
- [x] Chapter 8:
  - the reading note;
  - What an Import is;
  - The Import file, with a five-row example;
  - Making an Import (CLI and menu);
  - When an Import is refused: a code → meaning → what to do table covering every error and warning code from issue 25 (a test checks the table against the code list);
  - What changes in an Import Build.
- [x] Each step's `?` opens its chapter-7 anchor. Each anchor has a `test_guide` case. Hover help on a setting opens its chapter-3 entry.
- [x] Both chapters are translated into bg using `bg-terms.md`.
- [x] Tests: the guide, bg guide and parity tests pass; every draft step has a resolvable anchor; the refusal table covers every code.

## Comments

## Implementation note

- Chapter 7 is procedural, with the six `draft-*` anchors. Chapter 8 opens with the reading note. Its refusal table (24 codes and 5 warnings) was generated from the Import code's messages, and the bg table uses the catalogue's translations. `test_guide` checks that every Import code has a row.
- The draft dialog has a `?` per step, wired through `PANEL_SECTIONS["draft-<step>"]` and `show_help`. `show_help` now ignores a pattern-matched trigger with no clicks, so a newly rendered `?` cannot open help by itself. The dialog's setting labels are hover terms (`help.DRAFT_HELP`) that open their chapter-3 entries.
- The exclusion rules are edited as `exclusions.toml` text, so chapter 7 describes the text editor rather than per-field controls.
- The app header now shows the Build's name (`layout.brand_build`), falling back to the `build_id` for older Builds. The delete dialog also says that exports from the Build stop opening.

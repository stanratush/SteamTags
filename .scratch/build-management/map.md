# Map: Build management

Label: wayfinder:map

## Destination

An **implementation-ready spec** (`.scratch/build-management/spec.md`) plus numbered `ready-for-agent` issues for three features. **Build Settings**: create Builds in the app, with every setting that changes the Top-N exposed. **Build Management**: create, duplicate, delete and switch Builds, each with its own configuration, results and caches. **Data Independence**: Steam becomes one source behind a seam, and imported item–attribute datasets can be analysed. Every design choice is locked, so implementation can start without further design questions. *(Charted with the researcher, 2026-11-05.)*

## Notes

- **Domain:** the Build stage and the Tag Network app. Glossary: [CONTEXT.md](../../CONTEXT.md). Use its terms: Build, Snapshot, Top-100 Dataset (becoming **Top-N Dataset**), Eligible Pool, Exclusion, Exclusion Override, Manual Metadata Entry, Content Flag, Genre Tag, Network State, App Bundle.
- **Skills:** grilling tickets use `grilling` + `domain-modeling`. UI uses `prototype` (in `prototypes/`). Code inventories and measurements are `task` tickets, with scripts in `prototypes/` and findings in `research/`.
- **Decided while charting** (don't re-ask; a ticket that reopens one says so explicitly):
  - One map for all three features. The generic dataset contract is decided before the settings that depend on it.
  - A **Build stays immutable**. Save = the Build is written. Duplicate = a new Build started from another Build's settings, then edited. Delete = its folder and cache are removed.
  - The **Build menu** exists only where the app runs from the repository, because creating a Build needs a Snapshot. App Bundles stay open-only (ADR 0001 and the App Bundle definition are unchanged). A **lightweight Snapshot** can be made so a Snapshot moves easily between machines.
  - The menu has sections: settings that change the Top-N, reports and analysis, and network defaults. That covers datasets, exclusion rules, rank limits, list size, Content Flags, Genre Tags, the genre-kind map, analysis settings, `resolution_sweep` and the Parameter Selection defaults.
  - **List size** is set per dataset, default 100. The term becomes **Top-N Dataset**.
  - **Tags per game** is a number the user enters. It is a setting of its own **beside** the exclusion rank limit (`global_rank_limit` stays for exclusions).
  - Exclusion tag rules become **generic named rules**: a name, a tag list and, for Steam, content descriptor ids. Adult content and Dating Sim stay **separate** default rules. Overrides target one named rule.
  - Manual Exclusions, Exclusion Overrides and Manual Metadata Entries are **editable in the menu**, with reason and evidence required and today's Build validation.
  - **Steam becomes one source** behind a seam: Collect, Snapshot, Exclusions and ranking are unchanged. Every existing Build still opens, and no Steam result changes.
  - An **imported dataset** has items (id and name), each with an ordered attribute list, an optional numeric score that ranks them, and optional numeric item fields to filter on. One attribute kind per dataset; no weights.
  - The app **stays a Steam tool that can also open imported data**. Steam wording is kept, with a note that Game means item and Tag means attribute.
- **Constraints:**
  - Every new string needs a bg catalogue entry (ADR 0003; parity test).
  - Layout stays downstream of analysis (ADR 0002).
  - A Build stays deterministic: same Snapshot and settings give the same bytes.
  - Nothing is implemented on this map.
- **Settings inventory:** [Build settings by layer](research/00-build-settings-inventory.md) lists every Build setting: fixed by the Snapshot, changes the Top-N, reports only, network defaults. Its two contested parts belong to [What do tags per game and list size apply to?](issues/05-tags-per-game-and-list-size.md) and [How do named exclusion rules work?](issues/06-named-exclusion-rules.md).

## Decisions so far

<!-- one line per resolved ticket -->
- [Can one app process switch Builds without a restart?](issues/03-switch-builds-in-one-process.md): yes. Callbacks already read the Build per request from `build-path`, and only the server, layout and Parameter Selection stores bind it at startup. One shared job store is fine, but it must move out of the Build folder (Windows blocks Delete). Options A–E go to grilling.
- [Where does the analysis assume Steam?](issues/01-steam-assumptions-downstream.md): the network and the app already read one seam, six `top100` columns plus the defining tag and Genre Tags. Steam-only fields (`is_free`, genres, Content Flags, the Eligible Pool) are read only by the Build-stage `analysis/`. No links out. Import blockers are the Snapshot-parent folder layout, the eight required config files and the strict header. Eight spots would change Steam bytes if generalised, the `min_months` key name first.

## Not yet specified

- **Export schema:** what the Top-N rename and imported datasets change in the export schema (`top100_<key>.csv`, `dataset` columns, `build_id` references, schema version). This depends on the generic dataset contract and on Build identity.
- **Wording:** User Guide sections for the Build menu and for imported data, and the glossary entries (Top-N Dataset, tags per game, named exclusion rules, lightweight Snapshot, imported dataset). They follow from the tickets that define them.
- **Bundles and in-app Builds:** how the bundle maker picks Builds made in the app, and whether a Build's lineage (its parent Build) is shown in a Bundle.

## Out of scope

- App Bundles creating Builds: the Build menu is repository-only (decided while charting).
- Weighted attributes, several attribute kinds on one item, and links between items.
- Rewriting the glossary, the User Guide and the reports in generic (non-Steam) terms.
- Collecting any non-Steam data: imports arrive as files.

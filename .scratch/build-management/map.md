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
- [What does a Build read from a Snapshot, and how long does it take?](issues/02-build-inputs-and-timings.md): only pool, parse and games read it: every pool app's Steam Charts page and every scored app's store data, whatever the settings. Those fields are 6.3 MB gzipped against 447 MB. A Build takes 99 s, 79% of it reading raw pages; the network stage takes 12%. The request-log outcomes, `build_id` and software versions are inputs too.
- [What is the generic dataset contract?](issues/04-generic-dataset-contract.md): an in-memory `Dataset` behind one reader, with a Steam adapter (today's `top100` file, unchanged) and an import adapter; no shared file (ADR 0005). Integer item ids; attribute ids supplied or numbered in name order; rank from the score, else file order; at most one filter field, fixed per dataset. The whole import is the Eligible Pool. Steam-only facts stay out of the contract.
- [What do tags per game and list size apply to?](issues/05-tags-per-game-and-list-size.md): tags per game (glossary: Tag Depth) redefines "has" everywhere: membership, pool, network, feature analysis. Exclusions and Content Flags still read the full list. One value per Build, ≥ 2 or `all`; Steam defaults to 20. Files keep full lists and the reader cuts. List size is ≥ 10, and a pool smaller than N fails the Build.
- [How do named exclusion rules work?](issues/06-named-exclusion-rules.md): ordered `[[rule]]` entries (code name, label, tags with optional per-tag limit, name-only, Steam descriptor ids and the Adult Only notice as settings) run between the fixed rules (app type, store data, no tags first; manual last). Defaults keep today's codes, so datasets and reports stay byte-identical; an old-shape config is converted on read. Overrides on an unknown rule fail. Content Flags stay a separate list of the same shape. Imports get attribute rules, manual Exclusions and Overrides. Glossary updated.
- [What is a lightweight Snapshot?](issues/08-lightweight-snapshot.md): a zip of the parsed tables a Build reads (all month rows, every lookup outcome), about 6.3 MB, with the same `snapshot_id`. It is the default Build source when present (about 24 s against 99 s) and byte-identical apart from `snapshot_form: raw | lightweight`, tested on the fixture and by `verify-light`. An extract version and the repair count guard staleness. It is made by `snapshot lighten` and automatically after collect closes or a repair. The forms are named raw and lightweight, since "full" already means not-test. Glossary updated.
- [What is a Build's identity and lifecycle?](issues/07-build-identity-and-lifecycle.md): a Build gets a required name (unique per Snapshot) and description (its changelog entry), fixed at save, plus a parent when duplicated, possibly onto another Snapshot. Unsaved settings are **Build Drafts**: full copies under `builds/<snapshot>/drafts/`, saved automatically. `config/` stays the hand-edited defaults. Identical settings are allowed with a warning. Delete moves `latest`, lists affected bundles and exports, has no protection, and is refused for the open Build. A failed run is not a Build: the failure shows on its draft.
- [How does a dataset get imported?](issues/09-dataset-import.md): an **Import** (glossary) is one wide UTF-8 CSV (`id,name,attributes` with `;`-separated names, optional `score`, a filter column named at import, other columns numeric) plus an optional `attributes.csv` covering every attribute. Validation is all-or-nothing, with `errors.csv` under `imports/failed/`. Stored fixed in `imports/<timestamp>-<slug>/`, with Builds under `builds/<import_id>/`. Made by `steamstudy import` or a menu button. Steam-only settings are hidden, an unknown attribute fails the Build, and a reduced config set is used.
- [How does switching Builds keep caches apart and avoid recalculation?](issues/10-switching-and-cache-separation.md): each tab names its Build in the URL (`/build/<snapshot>/<build_id>`, Dash Pages; ADR 0006), and a switch rebuilds the page. Language, mode and same-named dataset are kept; Network State settings reset. Caches stay per Build in `<build>/app_cache/`, with no cross-Build reuse. A switch confirms and cancels the tab's analysis jobs; a draft's Build run is server-wide and survives it. Parameter Selection runs on demand. The job store is a per-process temp folder. Delete is refused only for the tab's own Build; a gone Build shows a notice. Bundles get the switcher only.

## Not yet specified

- **Wording:** User Guide sections for the Build menu and for imported data, and the glossary entries (Top-N Dataset, tags per game; Exclusion Rule, Lightweight Snapshot and Import are written). They follow from the tickets that define them; the wording for Top-N Dataset, List Size, Tag Depth and "has" is drafted in [What do tags per game and list size apply to?](issues/05-tags-per-game-and-list-size.md).
- **Bundles and in-app Builds:** how the bundle maker picks Builds made in the app, and whether a Build's name and lineage (its parent Build, recorded since [Build identity](issues/07-build-identity-and-lifecycle.md)) are shown in a Bundle and its file name.

## Out of scope

- App Bundles creating Builds: the Build menu is repository-only (decided while charting).
- Weighted attributes, several attribute kinds on one item, and links between items.
- Rewriting the glossary, the User Guide and the reports in generic (non-Steam) terms.
- Collecting any non-Steam data: imports arrive as files.

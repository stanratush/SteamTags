# Spec: Workbench Seed Priority

Settled with the researcher on 2026-11-17 in one grilling round, with no map: nothing was left undecided. The facts come from [What would "Prefer the main seed" change?](prototypes/01-seed-priority-effect/results.md). Glossary: [CONTEXT.md](../../CONTEXT.md). Constraints: ADR 0003 (every string has a bg catalogue entry). Builds stay deterministic and immutable.

## Goal

A Build gains one setting, **Workbench Seed Priority**. It decides the order in which the Workbench γ/seed search (from [Apply-to-Workbench semantics](../auto-parameter-selection/issues/09-apply-to-workbench.md)) tries candidates when it looks for a setting that shows a pair's Selected Partition in the Workbench:

- **Closest γ to the midpoint** (`closest_gamma`, the default). This is today's behaviour, unchanged.
- **Prefer the main seed** (`main_seed`).

**What it never changes:** the 10-seed scan, CHAMP, the Stable and Selected Partition rules, the Selected Resolution, Neighbour Agreement, the chosen (g, s), validation, or the fallback and its flags. Both values show the *same* partition whenever it can be reproduced. They differ only in the Workbench γ (and seed) at which it is shown, and therefore in Q, the Connection Ratios, the Workbench Seed-Noise Floor and Removal Sensitivity.

## Facts this spec rests on

The facts come from Build `20261109T064256Z-493c5375` with the default Selection Settings: 667 pairs with a Selected Partition across five datasets ([results](prototypes/01-seed-priority-effect/results.md)).

- Both values reproduce the same 660 pairs. `main_seed` uses the main seed for 595 of them (`closest_gamma`: 503). It uses the γ nearest the midpoint for 546 (`closest_gamma`: 630).
- The values pick a different (γ, seed) for 92 pairs. On those, the `main_seed` γ sits a median 41% of the way from the midpoint to the domain's edge (maximum 98%). Q differs by −0.060 to +0.034. The Workbench Seed-Noise Floor has the same median (0.770 vs 0.771) but moves by −0.29 to +0.44 on single graphs. The gap to Parameter Selection's floor grows, from a median of 0.000 to 0.027.
- None of the five default chosen pairs changes.
- There is no scientific case for `main_seed`: every seed is an equivalent random draw, and the scan seeds are derived from the main seed in a fixed way. The setting is offered for presentation. The User Guide recommends the default and says why.

## Decisions

### Term

**Workbench Seed Priority** enters CONTEXT.md **with the implementation** (`tests/test_guide.py` requires each term to be in the User Guide). Gist: the Build setting that chooses the order in which the Workbench γ and seed are searched for a **Selected Partition**: nearest the **Selected Resolution** first, or the main seed first. It never changes which partition is selected or shown. _Avoid_: seed preference, seed mode, main-seed mode. `docs/i18n/bg-terms.md` gains a row: *приоритет на началното число в работния плот* (the translator confirms the wording against the existing Workbench and seed terms).

Labels: "Closest γ to the midpoint" (default) and "Prefer the main seed". Codes: `closest_gamma`, `main_seed`.

### Where it lives

- It is a key in `config/network.toml`, `[parameter_selection] workbench_seed_priority = "closest_gamma"`, with a comment naming both values. Like every `network.toml` key, it is edited in the Build menu's **Network defaults** step (TOML text) and fixed when the Build is saved.
- `steamstudy.config` reads it into `ParameterSelectionDefaults`. A missing key reads as `closest_gamma`, so older Builds open unchanged. Any other value is a `ConfigError` naming the two allowed values, and that error shows on the draft's Network defaults step.
- It is a field of `SelectionSettings` (set by `load_selection_settings`). Like `scan_seeds` and `gamma_step`, it is **not** editable in Parameter Selection mode: it is not one of the staged Selection Settings, and "Reset to defaults" and "Copy from Workbench" don't touch it.

### The search

Both orders use the same candidate list as today: `workbench_candidates(a, b, midpoint)` gives two-decimal γ ≥ 0.01 inside the Optimality Domain, nearest the midpoint first, with ties going to the lower γ. "Reproduces" means the same groups of Tags as the Selected Partition, whatever the labels, as today (`C.canonical` equality).

- `closest_gamma`: for each γ in order, try the main seed, then the scan seeds in stream order. The first match wins. This is byte-identical to today.
- `main_seed`: first, try the main seed at every γ in order. If none matches, go back to the nearest γ and, for each γ in order, try the scan seeds in stream order. The main seed is not tried again. The first match wins.
- Fallback (both values, unchanged): γ = max(0.01, round(midpoint, 2)) with the main seed, flag `not_reproduced` (candidates existed) or `not_representable` (none existed), and the ARI against the Selected Partition.
- The order is separated from Leiden: one pure function yields the (γ, seed, seed_kind) attempts for a priority, and `workbench_setting` takes the priority and runs Leiden on each attempt until one matches. The tests drive the order with a fake `reproduces(γ, seed)` check.

### Cache key

- `settings_key()` gains `"workbench_seed_priority": "main_seed"` **only when** the value is `main_seed`. With the default, the key and its hash are byte-identical to today. Existing caches, export zip names, and every default Build's Parameter Selection results remain valid, and nothing recomputes.
- `METHOD_VERSION` stays `parameter-selection-1`. `GraphTask` carries the priority to the worker. The validation key inherits it through `grid_key`, harmlessly: validation doesn't read the Workbench setting, and a Build only ever has one value.

### Exports

- `parameter_selection.json` gets a top-level `"workbench_seed_priority": "<code>"`, **always written**, default included. It also appears in `selection_settings` through `asdict`.
- A Workbench export's `applied_from` block (export.json) gains `workbench_seed_priority` next to `workbench_gamma` and `workbench_seed`.
- `SCHEMA_VERSION` goes from 6 to 7, once, with the reason added to the version comment in `steamstudy.export.schema`. If the JSON metadata fields are declared in the schema registry, the new field is declared there too. The per-pair tables (`workbench_gamma`, `workbench_seed`, `not_reproduced`) are unchanged.
- `selection_report.md`'s methods paragraph names the priority only when it is `main_seed`. Default reports stay byte-identical.

### What the app shows

- The Controls column of Parameter Selection mode, under the Fixed settings, always shows one line: "Workbench seed priority: Closest γ to the midpoint" or "… Prefer the main seed". It is read-only.
- The Pair Inspector's Workbench γ/seed line, the Apply behaviour and the Workbench's provenance line are unchanged.

### User Guide (en and bg)

- In `02-app-controls.md`, "Apply to Workbench" gets one paragraph. It says that the Build's Workbench Seed Priority sets the search order, and describes both orders. It **recommends the default**: it keeps γ nearest the CHAMP midpoint, where the Selected Partition is furthest from being overtaken. It says the seed has no meaning of its own. It gives the measured cost of `main_seed` on the reference Build (92 of 667 pairs at a less central γ, median 41% of the way to the domain's edge; no default chosen pair changed). The Seed-Noise Floor caution notes that `main_seed` doesn't make the two floors agree.
- In `07-making-builds.md`, "Network defaults" gets one sentence naming the key, its values and its default, with a link to that paragraph.
- Chapter 3 gets an entry for the term, as every glossary term has. `help.py` gets a `selection.workbench_seed_priority` key if the Fixed settings line has a help icon, as its neighbours do.

### Tests

- The order of the search, with a fake check: scan seed 2 reproduces at the nearest γ and the main seed reproduces 0.03 away. `closest_gamma` gives (nearest γ, scan seed 2, `scan`). `main_seed` gives (γ 0.03 away, main seed, `main`).
- The tie-break: two candidates equally far from the midpoint. Both orders try the lower γ first.
- `main_seed` with no main-seed match anywhere: the scan seeds start again at the nearest γ.
- No match in either order: the fallback, its flag and its ARI are the same for both orders.
- A real small graph (an existing `test_selection` fixture): `closest_gamma` gives exactly today's cached `WorkbenchSetting`. `settings_key()` is byte-identical without the key and differs with `main_seed`.
- Config: a missing key gives `closest_gamma`, and an unknown value raises `ConfigError`.
- Exports: `parameter_selection.json` always has the field. `applied_from` has it after Apply. `SCHEMA_VERSION == 7`.
- bg parity and `test_guide` term coverage pass.

## Out of scope

- Making the setting editable in Parameter Selection mode or per Network State.
- Changing the default, or a third order (for example, seed first across all seeds).
- Any change to the scan, CHAMP, Selected Partition, Selected Resolution, Neighbour Agreement or chosen-pair rules.
- Recomputing or migrating existing caches. Default Builds keep them; a `main_seed` Build gets its own key.

## Implementation issues

1. [The setting and the search](issues/01-setting-and-search.md)
2. [Exports record the priority](issues/02-exports.md) (blocked by 1)
3. [App line, User Guide and glossary](issues/03-app-guide-glossary.md) (blocked by 1)

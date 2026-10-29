# 30: G2 Bulgarian guide: 02 Control reference and Analytical controls

**What to build:** the Bulgarian translation of the `## Control reference` and `## Analytical controls explained` sections of `02-app-controls.md` (~3.9k words on 2026-10-28, plus the Interface language and Edge appearance entries added since), written into `docs/user-guide/bg/` by the agent.

**Blocked by:** 29

**Status:** done

Spec: [Bilingual Interface and Cluster Views spec](../spec.md): "Bulk translation and review" (Guide slice conventions). Term table: [docs/i18n/bg-terms.md](../../../docs/i18n/bg-terms.md).

- [x] Translate the English as it stands when this issue starts, following the spec's Guide slice conventions: same headings and order, a `{#<english-slug>}` on every heading, the English term once at each entry heading, links kept, code spans and formulas untouched, the Bulgarian In short labels and markers within the 60-word cap, and Bulgarian number format in prose.
- [x] Never translated: tag names, game titles, Genre values, `C1…`, dataset labels, column and file names.
- [x] Add `02-app-controls.md#control-reference`, `02-app-controls.md#analytical-controls-explained` (the done-list's section form) to `GUIDE_DONE` in `tests/i18n_done.py`.
- [x] Every term follows `bg-terms.md`. A term the table lacks is added to it, marked "proposed", and listed in this issue's Comments for the next review.
- [x] The parity tests and the superseded-word scan pass, with this slice's entries on the done-list.
- [x] In the app, in BG: the guide modal opens on a few of these anchors from their ⓘ buttons and shows the Bulgarian text. Tooltips for these entries show the Bulgarian In short block.

## Comments

**2026-10-29, agent: done.** `## Control reference` (with its table and the Interface language entry) and `## Analytical controls explained` (13 entries) are translated into `docs/user-guide/bg/02-app-controls.md`, from the English as it stood on 2026-10-29.
- **The file also carries the chapter title**, *Настройки на приложението*. So the app uses the Bulgarian title, and the untranslated `##` sections after it stay English until G3 (issue 31).
- **The Edge appearance entry is not in this slice.** It sits under `## Reading the graph`, which is issue 31's section.
- **Entry headings** give the English term once: `### Резолюция γ (Resolution γ) {#resolution-γ}`.
- **In short blocks** use the Bulgarian labels in the English order. Every block is 60 words or fewer, and none uses a banned quality word.
- **The app's labels** are as the catalogues render them: *Месеци ≥ 12*, *„91 от 100“*, *„7 игри, под 8“*, *„премахнат“*, *Покажи отново*, *Нулирай всичко*. The Interface language example keeps *Q 0.42* in English on purpose, to show the contrast with *0,42*.

**Two test changes:**
- **A new test:** every Bulgarian In short block on the done-list keeps the form and the 60-word cap (`test_the_bulgarian_in_short_blocks_on_the_done_list_keep_the_form_and_the_word_cap`). Until now only the English blocks were checked. The test failed first on two of this slice's blocks (62 words each), which were then shortened.
- **The structure test** now resolves a link through `guide.ALIASES`, as the app and the English guide test do. The English chapter links `#edge-thickness`, the old anchor of Edge appearance, and the Bulgarian keeps that link. Test: `test_a_link_to_a_renamed_headings_alias_resolves`.

**Terms coined in this slice**, added to `bg-terms.md` as "proposed" for R2:
- the section titles: *Справочник на настройките*, *Аналитичните настройки, обяснени*;
- toggle *превключвател*, a Genre Tag's chip *бутон* (*етикет* is a label), slider *плъзгач*, Fit (⤢) *Побиране*;
- what-if *хипотетичен сценарий*, cookie *бисквитка*, private window *поверителен прозорец*;
- the layout's clamp *ограничаването*, label spacing *разреждането на етикетите*.

**Checked in the app in BG:**
- **Tooltips:** the dotted labels of the Minimum Months Filter and the Clustering weight carry the Bulgarian In short lines in their `data-tip`.
- **The guide modal**, opened from the labels for Resolution γ, Seed and the language switch, shows *Резолюция γ (Resolution γ)*, *Начално число (Seed)* and *Език на интерфейса (Interface language)* with their Bulgarian In short blocks.
- **The `#edge-thickness` link** from Clustering weight opens the Edge appearance section, still English (G3), with *← Назад*.

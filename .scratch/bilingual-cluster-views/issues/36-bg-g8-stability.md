# 36: G8 Bulgarian guide: 03 Stability and Removal Sensitivity

**What to build:** the Bulgarian translation of `## Stability` and `## Removal Sensitivity` of `03-metric-reference.md` (~4.5k words on 2026-10-28), written into `docs/user-guide/bg/` by the agent.

**Blocked by:** 35

**Status:** done

Spec: [Bilingual Interface and Cluster Views spec](../spec.md): "Bulk translation and review" (Guide slice conventions). Term table: [docs/i18n/bg-terms.md](../../../docs/i18n/bg-terms.md).

- [x] Translate the English as it stands when this issue starts, following the spec's Guide slice conventions: same headings and order, a `{#<english-slug>}` on every heading, the English term once at each entry heading, links kept, code spans and formulas untouched, the Bulgarian In short labels and markers within the 60-word cap, and Bulgarian number format in prose.
- [x] Never translated: tag names, game titles, Genre values, `C1…`, dataset labels, column and file names.
- [x] Add these two sections to `GUIDE_DONE` in `tests/i18n_done.py`.
- [x] Every term follows `bg-terms.md`. A term the table lacks is added to it, marked "proposed", and listed in this issue's Comments for the next review.
- [x] The parity tests and the superseded-word scan pass, with this slice's entries on the done-list.
- [x] In the app, in BG: the guide modal opens on a few of these anchors from their ⓘ buttons and shows the Bulgarian text. Tooltips for these entries show the Bulgarian In short block.

## Comments

**2026-10-29, agent: done.** `## Stability` (its In short block, opening, the `####` Three kinds of stability and 6 entries) and `## Removal Sensitivity` (its opening and 10 entries) are translated into `docs/user-guide/bg/03-metric-reference.md`, from the English as it stood on 2026-10-29.
- **On `GUIDE_DONE`**, both sections. Every heading has its twin at the English level, the labels and markers match, and every In short block passes the form and 60-word test. That test caught Adjusted Rand index at 61 words and Reclustered ARI at 69, now shortened.
- **Quoted app text is the Bulgarian catalogue's:** *„Шум от началното число“*, *„SD на Q 0,004“* and *„многотагови клъстери 5–7“* from the Seed-Noise Floor line, *„0,21 → н/д“*, *„няма“*, the Inspector labels (*„Промяна в Q (при нова клъстеризация)“*, *„Над шума от началното число“*, …) and the flagged-count footer (*„Отбелязани тагове: 7 от 50; ако премахванията действаха само като още едно начално число, очакваният среден брой отбелязани би бил около 5“*).

**Choices for R2:**
- **The Resolution Sweep example** quotes a sentence of the feature-analysis report, which is a Build report and stays English. It is kept in English as the report prints it, followed by a Bulgarian paraphrase (*Тоест между γ 0,50 и 1,50 …*). R2 may prefer only one of the two.
- ***Reclustered* and *fixed partition*** follow the Inspector's labels: *при нова клъстеризация* and *при фиксирано разбиване* (the Inspector's *запазени клъстери* is used where its label is quoted).
- **Numbers:** as in G4–G7. Prose is Bulgarian (*ARI 0,95*, *от −0,5 до 1*, *0,5 … 0,05*). Formulas and Δ expressions keep the English form (*Δ = −0.02*, *(8 × 1.0 + 2 × 0.75) / 10 = 0.95*).
- **Quality words:** *стабилност* appears only in its glossary terms (стабилност на принадлежността, стабилност при подизвадки, Three kinds of stability). The *„stable / unstable“* label the app never shows is quoted as *„стабилно / нестабилно“*.

**Terms coined in this slice**, added to `bg-terms.md` as "proposed" for R2:
- the section and entry titles: *Стабилност*, *Три вида стабилност*, *Коригиран индекс на Rand* (the methods-paragraph term), *Разброс на модулярността и силуета по начални числа*, *Обхват на броя клъстери по начални числа*, *Ред на изпълнение и идентичност*, *Промяна в модулярността при нова клъстеризация*, *Силует при нова клъстеризация*, *Промяна в броя клъстери при нова клъстеризация*, *ARI при нова клъстеризация*, *Изгубени центрове*, *Промяна в модулярността при фиксирано разбиване*, *Силует при фиксирано разбиване*, *Отметка „над шума“*;
- the three kinds: *алгоритмична*, *по параметрите*, *по данните*;
- noise seed *начално число за шума*, main seed *главно начално число*, yardstick *мерило*, companion *спътник*;
- fixed partition *фиксирано разбиване*, reorganisation *преподреждане*, mechanical *механична*, bridge tag *свързващ таг*, run order *ред на изпълнение*, active strength *активна сила*.

**Checked in the app in BG** (after a restart):
- **Tooltips:** the Cluster quality tab's seed-noise metrics (Adjusted Rand index, Seed spread) and the Removal sensitivity table's Run order carry the Bulgarian In short blocks.
- **The modal** shows *Стабилност на принадлежността (Membership Stability)*, *Отметка „над шума“ (Beyond-noise flag)* and the `####` *Три вида стабилност (Three kinds of stability)* in Bulgarian.
- **The next section**, *Parameter Selection*, still shows in English, as the partial-chapter fallback should.

# 37: G9 Bulgarian guide: 03 Parameter Selection

**What to build:** the Bulgarian translation of `## Parameter Selection` of `03-metric-reference.md` (~4.4k words on 2026-10-28), written into `docs/user-guide/bg/` by the agent.

**Blocked by:** 36

**Status:** done

Spec: [Bilingual Interface and Cluster Views spec](../spec.md): "Bulk translation and review" (Guide slice conventions). Term table: [docs/i18n/bg-terms.md](../../../docs/i18n/bg-terms.md).

- [x] Translate the English as it stands when this issue starts, following the spec's Guide slice conventions: same headings and order, a `{#<english-slug>}` on every heading, the English term once at each entry heading, links kept, code spans and formulas untouched, the Bulgarian In short labels and markers within the 60-word cap, and Bulgarian number format in prose.
- [x] Never translated: tag names, game titles, Genre values, `C1…`, dataset labels, column and file names.
- [x] Add `03-metric-reference.md` as a whole file (replacing G4–G8's section entries) to `GUIDE_DONE` in `tests/i18n_done.py`.
- [x] Every term follows `bg-terms.md`. A term the table lacks is added to it, marked "proposed", and listed in this issue's Comments for the next review.
- [x] The parity tests and the superseded-word scan pass, with this slice's entries on the done-list.
- [x] In the app, in BG: the guide modal opens on a few of these anchors from their ⓘ buttons and shows the Bulgarian text. Tooltips for these entries show the Bulgarian In short block.

## Comments

**2026-10-29, agent: done.** `## Parameter Selection` (its In short block, the `####` How Automatic Parameter Selection works and 12 entries) is translated into `docs/user-guide/bg/03-metric-reference.md`, from the English as it stood on 2026-10-29. With it, every section of chapter 3 is Bulgarian.
- **On `GUIDE_DONE`.** Every heading has its twin at the English level, the labels and markers match, and every In short block passes the form and 60-word test. That test caught Threshold Pair and Parameter Grid at 62 words and Neighbour Agreement at 61, now shortened.
- **Quoted app text is the Bulgarian catalogue's:** *„Приложи в работното място“*, *„Персонализирани ограничения“*, *„Q не е над нулевия модел“*, *„Разпаднат“*, and the Null Comparison and Subsample Stability examples rendered as `selection_text` prints them (*„Q при резолюция 1,151 е 0,067; никоя разбъркана мрежа не го достига (от −0,021 до −0,012).“*, *„При нов избор: медиана на ARI 0,69 (0,57–0,86) при 99 от 100 подизвадки“*).
- ***Двойка* alone** is the Threshold Pair throughout this section, as the term table says; the γ̂ conditions' *groups* (`one_group`, `no_cross_weight`) are *клъстери*, since *група* is the Cluster's Avoid word.

**Choices for R2:**
- **Numbers next to operators:** constraint values that the app shows on its pills are written as on screen, in Bulgarian (*≥ 0,50*, *≤ 0,10*, *≥ 0,90*, *≤ 0,5*), matching the catalogue's own *„среден индекс на Jaccard ≤ 0,5“*. Formulas, worked arithmetic and intervals keep the English form (*γ_max(31) = 5.14*, *γ̂ = 0.80*, *[1.046, 1.138]*, *m = ⌊0.8·n⌋*). Prose numbers are Bulgarian (*1040 изпълнения на Leiden*, *от 3,80 до 17,75*, *избраната резолюция е 1,092*). This refines the G4–G8 rule ("an expression with *=* keeps the English form"): R2 may want G5's *q ≤ 0.05* and G7's *при γ = 1.00* brought in line one way or the other.
- **Dataset keys** in the chosen-pairs example (*overall*, *puzzle*, *rpg*, …) stay as written, lowercase.
- **neighbour link** is *сравнение със съсед* in prose, following the Pair Inspector's *Сравнения със съседите*, because *връзка* is Connections and *ребро* is an edge.

**Terms coined in this slice**, added to `bg-terms.md` as "proposed" for R2:
- the entry titles: *Как работи автоматичният избор на параметри*, *Двойка прагове и решетка на параметрите*, *Допустимо разбиване и област на оптималност*, *Оценка на резолюцията и стабилно разбиване*, *Избрано разбиване и избрана резолюция*, *Дял на изолираните тагове и дял на LCC*, *Ограничения за двойката, квалифицирана двойка и правилото за избор*;
- resolution estimate *оценка на резолюцията*, fixed-point test *тест за неподвижна точка*, map target *целево разбиване*, CHAMP plot *графиката на CHAMP*, pass loop *цикъл от проходи*, canonical membership *канонично членство*;
- degree-corrected planted-partition model *модел с вградено разбиване с корекция за степента*, multigraph *мултиграф*, likelihood *правдоподобие*, assortative *асортативно*, connected component *свързана компонента*;
- neighbour link *сравнение със съсед*, compared tags *сравнявани тагове*, perturbation *смущение*, tag–game assignment *назначение таг–игра*, degenerate *изродена*, retention share *дял на запазване*, without replacement *без връщане*.

**Checked in the app in BG** (after a restart):
- **Tooltips:** in the Parameter Selection mode, the How it works, Admissible Partition, Resolution estimate, Selected Partition, Neighbour Agreement, Edge Overlap, Information Retention, Isolated share, Pair Constraints, Null Comparison and Subsample Stability tooltips carry the Bulgarian In short blocks.
- **The modal:** clicking a Neighbour Agreement value opens *Съгласие със съседите (Neighbour Agreement)* in Bulgarian.

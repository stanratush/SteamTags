# 22: Bulgarian terms for the new features, and the superseded-word scan

**What to build:** before any Bulgarian is written, the term table covers the words that features 2–4 introduced, agreed with the researcher. A **Superseded words** section and a test that scans for those words are added. The bulk slices then all start from the same table.

**Blocked by:** 14, 16, 18, 19, 20, 21

**Status:** done

Spec: [Bilingual Interface and Cluster Views spec](../spec.md): "Bulgarian terms and numbers", "Corrections flow through the term table", "Resolved while writing this spec". Term table: [docs/i18n/bg-terms.md](../../../docs/i18n/bg-terms.md).

This is a HITL session. The agent drafts; the researcher decides every row.

- [x] **The agent drafts rows** with a recommended Bulgarian word and an Avoid cell, from the English that features 2–4 shipped:
  - Domain terms: Connection Ratio, Connection Share, Edge Appearance.
  - Panels and UI names: Connections matrix, Cluster map, pair view, Connections (Inspector section), Games (Inspector section), Edges card, Hide links below, Links between Clusters, Matched, "of its tags", Show all, Ratio | Share, Matrix | Table.
  - Edge Appearance words: width, scaling (linear, square root, log), colour modes (one colour, By Cluster, within vs between, by value), strength.
- [x] **The researcher accepts or changes each row.** The agent writes the agreed rows into `bg-terms.md`, in the right sections.
- [x] **Superseded words**: a new section in `bg-terms.md` with a short explanation and a two-column table: stem, and allowed phrases. It starts with *Жакар*, *Лайден*, *сийд* and *билд*, plus anything the researcher adds now.
- [x] **Scan test** (`tests/test_i18n.py`):
  - It parses the Superseded table and scans every string in `src/steamstudy/i18n/bg/` and every file under `docs/user-guide/bg/`.
  - Each stem is matched at the start of a word, case-insensitively (`\b<stem>\w*`), skipping the occurrences inside an allowed phrase.
  - It fails on a hit, naming the file and the word.
  - It passes on today's (empty) Bulgarian, and fails on a fixture string containing *сийда*.
- [x] The `bg-terms.md` intro says how a review correction flows: change the row, move the old word to Avoid and to Superseded, then sweep.

## Draft (agent, 2026-10-28)

From the English the features shipped (`layout.edge_words`, `ui_words["map"]`, `view.py` connections, pair and games views, `02-app-controls.md` Edge appearance). ⚑ marks a row with a real choice.

| English | Recommended Bulgarian | Avoid | Note |
|---|---|---|---|
| ⚑ link (UI word for an edge) | връзка | — | *ребро* stays for the formal term (edge weight, definitions). Shapes: *Скрий връзките под*, *Връзки между клъстерите*. |
| ⚑ Connection Ratio | отношение на свързаност | коефициент на свързаност, сила на връзката, афинитет, плътност | *отношение* is the exact word for a ratio; *коефициент* suggests a fitted parameter. |
| ⚑ Connection Share | дял на свързаност | процент, пропорция, вероятност | *дял* is in the partition row's Avoid cell, but only as a word for *partition*; here it is the natural word for a share. |
| Edge Appearance | вид на ребрата | стил, изглед, тема | *изглед* is avoided for the Network State; kept out here too. |
| Connections matrix | матрица на връзките | — | |
| Cluster map | карта на клъстерите | — | |
| pair view / Cluster pair (Inspector heading) | изглед на двойка / Двойка клъстери | — | *двойка* already means Threshold Pair in Parameter Selection; *двойка клъстери* is always qualified. |
| Connections (Inspector section) | Връзки | — | |
| Games (Inspector section) | Игри | — | |
| Edges (the legend button and the Edges tab) | Ребра | — | |
| pool (of One-Tag Clusters) | пул на еднотаговите клъстери (short: пул) | група, остатък | Same *пул* as the Candidate and Eligible Pools. |
| Hide links below | Скрий връзките под | Филтър (that is Minimum shared games) | |
| Links between Clusters | Връзки между клъстерите | — | |
| Matched | Съвпадащи | Съвпадения, Мачнати | "7 / 26" stays as it is. |
| "of its tags" | от таговете ѝ | — | *ѝ*: the game (*играта*) is feminine. |
| Show all {n} | Покажи всички {n} | — | |
| Ratio \| Share | Отношение \| Дял | — | |
| Matrix \| Table | Матрица \| Таблица | — | |
| Width (and edge thickness) | Дебелина (дебелина на ребрата) | ширина | One word for both, as the legend's key and the control mean the same thing. |
| Scaling: linear, √, log | Мащаб: линеен, √, log (prose: корен квадратен, логаритмичен) | скалиране | √ and log stay symbols, as in English. |
| Colour: one colour, By Cluster, within vs between, by value | Цвят: един цвят, по клъстер, вътре / между, по стойност | оцветяване | |
| ⚑ Strength (link opacity) | Наситеност | сила (that is the metric *Strength (weighted degree)*), плътност (graph density), непрозрачност | The English word collides with the metric; Bulgarian can separate them. |
| Less \| More | По-малко \| Повече | — | |

## Resolution

Agreed with the researcher on 2026-10-28 and written into [bg-terms.md](../../../docs/i18n/bg-terms.md): the domain rows under Domain terms, the panel, section and toggle names under the app's panels, and the card's controls, the link labels, Matched and Show all under Short UI words. Those two tables have no Avoid column, so their Avoid words are written inline as "(avoid …)", as the Analysis Report mode row already did.

- **Changed by the researcher:** *link* is **ребро** everywhere, as for *edge*, not the drafted *връзка*: *Скрий ребрата под*, *Ребра между клъстерите*, *Ребра между тях*. *връзка* is therefore left to **Connections** (between Clusters: *Връзки*, *матрица на връзките*) and goes into the link row's Avoid cell.
- **Chosen among the flagged options:** Connection Ratio *отношение на свързаност*, Connection Share *дял на свързаност* (toggle *Отношение | Дял*); Strength (link opacity) *Наситеност*.
- **Accepted as drafted:** every other row of the Draft table.
- **Superseded words:** the four starting stems, *Жакар*, *Лайден*, *сийд*, *билд*; the researcher added none.
- **Scan:** `i18n_parity.superseded`, `bulgarian_texts` and `superseded_hits`, tested in `tests/test_i18n.py`. Allowed phrases are `;`-separated in the table's second cell.

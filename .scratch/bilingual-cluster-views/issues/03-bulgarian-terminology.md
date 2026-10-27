# Bulgarian terminology
Type: grilling
Status: resolved
Blocked by: none

## Question

Which Bulgarian term stands for each domain term and metric name, and how are numbers written in Bulgarian? This is a HITL grilling with the researcher (`grilling` + `domain-modeling`). The result is a term table that every translation follows.

- Every term in [CONTEXT.md](../../../CONTEXT.md): Cluster, Multi-Tag/One-Tag Cluster, Cluster Center, Tag, Genre, Genre Tag, Tag Network, Clustering Weight, Lift, Network State, Seed-Noise Floor, Membership Stability, Removal Sensitivity, Threshold Pair, Neighbour Agreement, Selected Partition, Mean Monthly Players, Observation Window, and the rest. For each: translate it, transliterate it, or keep it in English, and list the Bulgarian forms to avoid, as the glossary does.
- Metric and method names: Modularity Q, Silhouette, Coverage, conductance, ARI, Jaccard, Leiden/Louvain, resolution γ, curveball null.
- Dataset labels from `config/datasets.toml` (`Overall`, `Puzzle`, `RPG`, `Strategy`, `Simulation`). They are config data, but they read as words and also appear in exports.
- The guide's fixed labels, which [Translation mechanism](02-translation-mechanism.md) made per language (one label set each, parsed and checked by `in_short()`): `In short.`, `Higher →`, `Lower →`, `Raising it →`, `Here:`, `Caution:`, `Now:`, `Column(s):`, `Why it matters here`, `Exact definition`, `Example`, `Bounds`, `Compare with`, `Shown in the app as`. Also the banned quality words (`good`, `strong`, `stable`, …) that In short blocks must avoid in Bulgarian, as guidance for the translator and the review only: content tests stay English-only (Translation mechanism). Inventory: [research/01-string-inventory.md](../research/01-string-inventory.md).
- Number format on screen: the decimal comma (0,42) with a space as the thousands separator, or dots everywhere, so screen values match exports and the paper. [Translation mechanism](02-translation-mechanism.md) made it one rule per language, owned by `tx.num()` and mirrored in the grids (`d3.formatLocale`), Plotly `separators` and the pills, so this ticket sets only the rule. Exports stay unchanged either way (map Notes).
- Short UI words the client shows: `n/a`, `yes`, `no`, the app name in the tab title (`Tag Network`), and the ag-grid filter-menu words.
- Where the table lives: a Bulgarian column or section in CONTEXT.md, or a separate glossary file.

## Answer

Settled with the researcher on 2026-10-27, in two grilling rounds. The researcher accepted every recommendation and changed one term: Monthly Avg. Players is *среден брой играчи на месец*. The record is [docs/i18n/bg-terms.md](../../../docs/i18n/bg-terms.md), and the **Interface Language** entry in [CONTEXT.md](../../../CONTEXT.md) points to it.

- **Policy**: translate by default. Proper names and abbreviations stay in Latin script (Leiden, Jaccard, ARI, γ). Export columns and files appear in English, in backticks. Each Bulgarian guide entry heading gives the English term once, e.g. `### Лифт (Lift) {#lift}`. The guide uses polite lowercase *вие*, and buttons use the short imperative.
- **Core terms**:
  - таг (*етикет* is kept for the cluster labels `C1…`)
  - клъстер; многотагов / еднотагов клъстер; център на клъстера
  - мрежа от тагове (also the BG tab title); състояние на мрежата
  - разбиване (допустимо / стабилно / избрано); резолюция γ
  - начално число (seed)
  - моментна снимка; компилация; лифт
  - решетка на параметрите; пул на годните игри; квалифицирана двойка (these avoid the clashes with *мрежа* and *допустим*)
- **Modes**: Работно място; режим „Аналитичен доклад“; Избор на параметри. **Layouts**: Общо / По клъстери.
- **Dataset labels** stay English, on screen too. Four of the five are Tag names, and translating only Overall would leave it out of step with the exports.
- **Numbers on screen (BG)**: decimal comma, no thousands separator (as English today), `%` attached. Exports are unchanged.
- **Guide labels, banned quality words, n/a / yes / no and the ag-grid words**: all in the table.
- **Where the table lives**: `docs/i18n/bg-terms.md`, outside `docs/user-guide/`, so the guide parser and the parity tests never read it. CONTEXT.md stays English-only.

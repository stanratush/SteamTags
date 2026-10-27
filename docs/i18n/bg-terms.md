# Bulgarian term table

Every Bulgarian text in the Tag Network app and the Bulgarian User Guide (`docs/user-guide/bg/`) follows this table. The English domain terms are defined in [CONTEXT.md](../../CONTEXT.md). This file only says how each one is written in Bulgarian. Agreed with the researcher on 2026-10-27 ([Bulgarian terminology](../../.scratch/bilingual-cluster-views/issues/03-bulgarian-terminology.md)).

This file sits outside `docs/user-guide/`, so the guide parser and the parity tests never read it.

## Policy

- **Translate by default** into an established Bulgarian scientific word.
- **Proper names and abbreviations stay in Latin script**: Leiden, Louvain, CHAMP, Jaccard, Hennig, ARI, NMI, γ. Write *индекс на Jaccard* and *алгоритъм Leiden*, never *Жакар* or *Лайден*.
- **Exports stay English**: column names and file names appear in English, in backticks (`cluster_connections.csv`, `edge_count`).
- **Never translated**: Steam tag names, game titles, Steam Genre values, cluster labels `C1…` and the five dataset labels (`Overall`, `Puzzle`, `RPG`, `Strategy`, `Simulation`). Prose may say *наборът Overall*.
- **English once at each guide entry heading**: every glossary entry heading in the Bulgarian guide gives the English term in parentheses, before its anchor, e.g. `### Лифт (Lift) {#lift}`.
- **Register**: the guide addresses the reader with polite plural *вие*, in lowercase. Buttons and actions use the short imperative: *Отвори*, *Нулирай*, *Изтегли*.

## Numbers on screen

- **Decimal comma**: 0,42.
- **No thousands separator**, the same as English on screen today: 12345.
- **Percent sign attached**: 42%.
- **Exports never change.** For the grids this means `d3.formatLocale({decimal: ",", thousands: ""})`; Plotly `separators` is `","` with an empty thousands value.

## Domain terms

| English | Bulgarian | Avoid |
|---|---|---|
| Tag | таг (pl. тагове, count form 3 тага) | етикет (that word is the cluster label `C1…`), маркер, ключова дума |
| cluster label `C1…` | етикет на клъстера | — |
| Cluster | клъстер | общност (except *откриване на общности* when citing methods), група, тема, категория |
| Multi-Tag Cluster | многотагов клъстер | клъстер с няколко тага |
| One-Tag Cluster | еднотагов клъстер | сингълтон, некластериран таг, шум |
| Cluster Center | център на клъстера | хъб, ядро, представител |
| Tag Network | мрежа от тагове | тагова мрежа, граф на таговете (in prose) |
| Network State | състояние на мрежата | състояние (unqualified), изглед, сесия, конфигурация |
| partition | разбиване | дял, разделяне, разпределение |
| Admissible Partition | допустимо разбиване | оптимално разбиване (unqualified) |
| Optimality Domain | област на оптималност | — |
| Stable Partition | стабилно разбиване (in the Gibson & Mucha sense) | устойчиво разбиване, консенсусно разбиване |
| Selected Partition | избрано разбиване | най-добро разбиване, окончателна клъстеризация |
| Selected Resolution | избрана резолюция | — |
| resolution γ | резолюция γ | разделителна способност |
| seed | начално число (with *seed* in parentheses at the guide heading and on the control's tooltip) | семе, сийд |
| Seed-Noise Floor | праг на шума от началното число | доверителен интервал, грешка, стабилност на seed |
| Mean Monthly Players | средномесечен брой играчи | средни играчи, популярност, успех (unqualified) |
| Monthly Avg. Players | среден брой играчи на месец | месечни играчи, MAU |
| Observation Window | период на наблюдение | прозорец |
| Missing Month | липсващ месец | нулев месец |
| Placeholder Row | запълващ ред | нулев месец, празен месец |
| Release Month | месец на излизане | дата на издаване |
| Months Observed | наблюдавани месеци | — |
| Genre | жанр | жанров таг (when meaning the store field) |
| Genre Tag | жанров таг | — |
| edge / node | ребро / възел | — |
| edge weight | тегло на реброто (= брой общи игри) | — |
| Clustering Weight | тегло за клъстеризация | тегло на реброто (when meaning the Lift mode), нормализирано тегло |
| minimum games per tag | минимум игри на таг | — |
| minimum shared games | минимум общи игри | — |
| hidden / removed Tags | скрити / премахнати тагове | — |
| Lift | лифт (m., лифтът) | сила на асоциацията (except when citing van Eck & Waltman), афинитет, повдигане |
| Removal Sensitivity | чувствителност към премахване | влияние, важност |
| Membership Stability | стабилност на принадлежността | увереност, сигурност, устойчивост |
| Resolution Sweep | обхождане на резолюцията | тест за стабилност на γ, проверка за устойчивост |
| Threshold Pair | двойка прагове | конфигурация, клетка (except for the heatmap), набор параметри |
| Parameter Grid | решетка на параметрите | мрежа (that word is the network), пространство на търсене |
| Automatic Parameter Selection | автоматичен избор на параметри | оптимизация, оптимални параметри, автонастройка |
| Neighbour Agreement | съгласие със съседите | стабилност на решетката, устойчивост, гладкост |
| Edge Overlap | припокриване на ребрата | стабилност на ребрата, сходство на графите |
| Subsample Stability | стабилност при подизвадки | bootstrap доверие, устойчивост |
| Null Comparison | сравнение с нулев модел | тест за значимост, p-стойност, валидиране |
| curveball null | нулев модел curveball | — |
| Information Retention | запазване на информацията | покритие (that is the partition metric), загуба на данни |
| Fragmentation | фрагментация | разреденост, свързаност |
| Pair Constraint | ограничение за двойката | критерий за допустимост, филтър |
| Selection Settings | настройки на избора | фиксирани настройки, конфигурация, параметри |
| Qualifying Pair | квалифицирана двойка | допустима двойка, валидна двойка |
| Minimum Months Filter | филтър за минимум месеци | — |
| Interface Language | език на интерфейса | локал, режим на превод |
| App Bundle | пакет на приложението | самостоятелно приложение, преносима версия, офлайн пакет |
| Free-to-Play Game | безплатна игра (Free-to-Play) | — |
| Candidate Pool | пул от кандидати | топ-N игри, изтеглени игри |
| Eligible Pool | пул на годните игри | допустим (that word is Admissible), популация, всички игри |
| Top-100 Dataset | набор Топ-100 | — |
| Tag-Specific Dataset | набор по таг | — |
| Exclusion | изключване | — |
| Exclusion Override | отмяна на изключване | бял списък, ръчно включване |
| Content Flag | флаг за съдържание | меко изключване, предупреждение |
| Source Substitution | заместване на източник | — |
| Manual Metadata Entry | ръчно въведени метаданни | ръчна корекция, ръчно попълнени данни |
| Snapshot | моментна снимка | пускане, скрейп, обхождане |
| Build | компилация (pl. компилации), defined at its guide heading as a data derivation | пускане, аналитично пускане, билд |

## Metric and method names

| English | Bulgarian |
|---|---|
| Modularity Q | модулярност Q |
| Silhouette | силует |
| Coverage | покритие |
| conductance | проводимост |
| ARI, NMI | unchanged |
| Jaccard | индекс на Jaccard, разстояние на Jaccard |
| Leiden, Louvain, CHAMP, Hennig | unchanged, in Latin script |

## The app's modes, layouts and panels

| English | Bulgarian |
|---|---|
| Tag Network (browser tab title) | Мрежа от тагове |
| Workbench | Работно място |
| Analysis Report mode | режим „Аналитичен доклад“ (avoid *доклад* on its own) |
| Parameter Selection | Избор на параметри |
| Global / Cluster-separated | Общо / По клъстери |
| Controls / Inspector / Tables | Настройки / Инспектор / Таблици |

## Guide labels

The label set that `in_short()` reads for Bulgarian.

| English | Bulgarian |
|---|---|
| In short. | Накратко. |
| Higher → | По-високо → |
| Lower → | По-ниско → |
| Raising it → | При повишаване → |
| Here: | Тук: |
| Caution: | Внимание: |
| Now: | Сега: |
| Column: / Columns: | Колона: / Колони: |
| Why it matters here | Защо има значение тук |
| Exact definition | Точна дефиниция |
| Example | Пример |
| Bounds | Граници |
| Compare with | Сравнете с |
| Shown in the app as | В приложението се показва като |

**Quality words to avoid in Bulgarian In short blocks.** This is guidance for translating and reviewing; it has no test. Avoid: добър, лош, силен/силно, слаб, стабилен, устойчив, важен, значим/значителен, надежден, отличен. Glossary terms such as *стабилно разбиване* are exempt.

## Short UI words

| English | Bulgarian |
|---|---|
| n/a / yes / no | н/д / да / не |
| ag-grid: Contains · Not contains · Equals · Not equal · Starts with · Ends with | Съдържа · Не съдържа · Равно на · Различно от · Започва с · Завършва с |
| ag-grid: Less than · Greater than · In range · Blank · Not blank | По-малко от · По-голямо от · В интервала · Празно · Непразно |
| ag-grid: AND / OR · Filter... · No Rows To Show | И / ИЛИ · Филтър… · Няма редове |

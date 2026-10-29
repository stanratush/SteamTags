# Bulgarian term table

Every Bulgarian text in the Tag Network app and the Bulgarian User Guide (`docs/user-guide/bg/`) follows this table. The English domain terms are defined in [CONTEXT.md](../../CONTEXT.md). This file only says how each one is written in Bulgarian. Agreed with the researcher on 2026-10-27 ([Bulgarian terminology](../../.scratch/bilingual-cluster-views/issues/03-bulgarian-terminology.md)); the terms of the Edge appearance card, the Connections views and the Games section on 2026-10-28 ([issue 22](../../.scratch/bilingual-cluster-views/issues/22-new-terms-and-superseded-scan.md)); every term proposed by the slices A1–A4 and G1 accepted in the calibration review on 2026-10-29 ([issue 28](../../.scratch/bilingual-cluster-views/issues/28-r1-calibration-review.md)).

This file sits outside `docs/user-guide/`, so the guide parser never reads it. Two tests do: the superseded-word scan reads the table at the end, and a guide test checks `guide.LABELS` and `guide.MARKERS` against the Guide labels.

**How a correction flows.** A term change, from a review or any other source, edits this file first: change the row, move the old word into its **Avoid** cell and into [Superseded words](#superseded-words), then sweep the Bulgarian text. A test (`tests/test_i18n.py`) fails on any superseded word left in `src/steamstudy/i18n/bg/` or `docs/user-guide/bg/`, so the sweep cannot be skipped.

## Policy

- **Translate by default** into an established Bulgarian scientific word.
- **Proper names and abbreviations stay in Latin script**: Leiden, Louvain, CHAMP, Jaccard, Hennig, ARI, NMI, γ. Write *индекс на Jaccard* and *алгоритъм Leiden*, never *Жакар* or *Лайден*.
- **Exports stay English**: column names and file names appear in English, in backticks (`cluster_connections.csv`, `edge_count`).
- **Never translated**: Steam tag names, game titles, Steam Genre values, cluster labels `C1…` and the five dataset labels (`Overall`, `Puzzle`, `RPG`, `Strategy`, `Simulation`). Prose may say *наборът Overall*.
- **English once at each guide entry heading**: every glossary entry heading in the Bulgarian guide gives the English term in parentheses, before its anchor, e.g. `### Лифт (Lift) {#lift}`.
- **Register**: the guide addresses the reader with polite plural *вие*, in lowercase. Buttons and actions use the short imperative: *Отвори*, *Нулирай*, *Изтегли*. A tooltip that names a control's action uses the same short imperative (*Побери целия граф на екрана*); a tooltip that tells the reader what to do with the mouse uses *вие* (*Щракнете…*, *Плъзнете…*).

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
| Cluster pair | двойка клъстери (always qualified: *двойка* alone is the Threshold Pair) | — |
| pool of One-Tag Clusters | пул на еднотаговите клъстери (short: пул, as in the Candidate and Eligible Pools) | група, остатък |
| Connection Ratio | отношение на свързаност | коефициент на свързаност, сила на връзката, афинитет, плътност |
| Connection Share | дял на свързаност (*дял* is avoided only as a word for partition) | процент, пропорция, вероятност |
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
| link (the UI word for an edge) | ребро, as for edge: *Скрий ребрата под*, *Ребра между клъстерите* | връзка (that word is Connections, between Clusters) |
| Edge Appearance | вид на ребрата | стил, изглед, тема |
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
| User Guide · guide entry | ръководство за потребителя (short: ръководството) · статия | — |
| defining tag (of a Tag-Specific Dataset) | определящ таг | — |
| replicate (null model, seed noise) | повторение | реплика |
| source / target tag (of an edge) | изходен / целеви таг | — |
| tag id | идентификатор на таг | ID, номер |
| null-model excess · null mean · shuffled networks | превишение над нулевия модел · средно за нулевия модел · разбъркани мрежи | излишък |
| game-set distance (Jaccard distance between game sets) | разстояние по игри; in full разстояние на Jaccard между множествата игри | — |
| reclustered · clusters kept (Removal Sensitivity) | при нова клъстеризация · запазени клъстери | — |
| screening flag · flagged | отметка за проверка · отбелязан | флаг (that word is the Content Flag) |
| member (of a Cluster) · partner (in Connections) | член · партньор | — |
| SD | SD, in Latin script like ARI | СО |
| isolated share · LCC share (Pair Constraints) | дял на изолираните тагове · дял на LCC, LCC in Latin script | — |
| comparable neighbours · near-best · tolerance | сравними съседи · почти най-добри · допуск | — |
| NA (the heatmap's short Neighbour Agreement) | NA, in Latin script | — |
| scan · scan seed · scan range · hits · envelope (CHAMP) | сканиране · начално число от сканирането · обхват на сканирането · попадения · обвивка | — |
| Validation · Validate this pair | валидиране · Валидирай тази двойка (Null Comparison keeps its own name) | — |
| arm · re-selected · at resolution (Subsample Stability) | вариант · при нов избор · при резолюцията | рамо |
| dissolved (a Cluster under subsampling) | разпаднат | разтворен |
| Neighbour links (the Pair Inspector section) | сравнения със съседите | връзки, ребра (those are Connections and edges) |
| qualifies (a Threshold Pair) | квалифицира се | — |
| Default / Custom constraints · Default / Custom settings | Ограничения по подразбиране / Персонализирани ограничения · Настройки по подразбиране / Персонализирани настройки | — |
| robustness (of the Clusters) · a coarser split | робастност · по-едро разбиване | устойчивост, разделяне |
| subset · random 80% subsets of the games | подмножество · случайни подмножества от 80% от игрите | — |
| methods paragraph: adjusted Rand index · self-consistent resolution · upper envelope · curveball trades · scaled by floor · mean best-match Jaccard | коригиран индекс на Rand · самосъгласувана резолюция · горна обвивка · размени curveball · мащабирани със закръгляне надолу · среден индекс на Jaccard за най-добро съвпадение | — |
| rule of thumb · band · cut-off · reference point (Appendix A) | емпирично правило · гранична зона · гранична стойност · отправна точка | праг (that word is the thresholds g and s) |
| pipeline · repository · parse errors | конвейер · хранилище · грешки при разбора | — |
| feature analysis (the Build's report) | анализ на характеристиките | — |
| consensus partition (what the study does not compute) | консенсусно разбиване, only in that literal sense | — |
| delisted · region-locked | премахнат от магазина · с регионални ограничения | — |
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
| Inspector plain names | Сума на общите игри · Сума на лифта · Изпъкване в своя клъстер (z) · Разпръснатост между клъстерите · Съответствие със своя клъстер (силует) · Пресичане на границата (проводимост) · Най-свързан член |

## The app's modes, layouts and panels

| English | Bulgarian |
|---|---|
| Tag Network (browser tab title) | Мрежа от тагове |
| Workbench | Работно място |
| Analysis Report mode | режим „Аналитичен доклад“ (avoid *доклад* on its own) |
| Parameter Selection | Избор на параметри |
| Global / Cluster-separated | Общо / По клъстери |
| Controls / Inspector / Tables | Настройки / Инспектор / Таблици |
| Connections matrix · Cluster map | матрица на връзките · карта на клъстерите |
| Connections · Games (Inspector sections) | Връзки · Игри |
| pair view | изглед на двойка (its heading: Двойка клъстери) |
| Edges (the legend button and the Edges tab) | Ребра |
| Dataset (control and block) | Набор от данни (prose keeps *набор*) |
| Export (block, noun) · Export this state (button) | Експорт · Експортирай състоянието на мрежата |
| app cache | кеш на приложението |
| Key (the legend's first label) | Легенда |
| Ratio \| Share · Matrix \| Table | Отношение \| Дял · Матрица \| Таблица |
| summary row · dotted label · pill bar · floating card · bottom sheet | ред с обобщението · пунктиран етикет · лента с бутони · плаваща карта · долен панел |
| the chapter titles (the guide's Contents) | Три правила · Първи стъпки · Настройки на приложението · Справочник на метриките · Какво има във всеки файл · Цитиране и възпроизвеждане на състояние на мрежата · Известни ограничения · Приложения A–C |
| the section titles of chapter 2 · Control reference · Analytical controls explained | Справочник на настройките · Аналитичните настройки, обяснени (proposed) |
| toggle · chip (a Genre Tag's button) · slider · Fit (⤢) | превключвател · бутон (not *етикет*, which is a label) · плъзгач · Побиране (proposed) |
| what-if · cookie · private window | хипотетичен сценарий · бисквитка · поверителен прозорец (proposed) |
| the layout's clamp · label spacing | ограничаването · разреждането на етикетите (proposed) |
| Reading the graph · Find a tag · Window width and the three forms · Task recipes | Как се чете графът · Намерете таг · Ширина на прозореца и трите форми · Рецепти за задачи (proposed) |
| heatmap · reason letters · dataset strip · near-best set | топлинна карта · букви за причини · лента с наборите · множеството на почти най-добрите (proposed) |
| bubble (Cluster map) · histogram · handle | мехур · хистограма · дръжка (proposed) |
| badge · verdict (Pair Inspector) · provenance line · loading panel | значка · извод · ред за произхода · панел за зареждане (proposed) |
| hub (in the Position entry, a tag linked to almost every other) | хъб, only there: never for the Cluster Center (proposed) |
| chapter 3's opening sections · Ranking and data | Как да четете тази глава · Настройки, които променят числата · Ранжиране и данни (proposed) |
| would-be rank · near miss · impact report · completeness counts · depth check | хипотетичен ранг · близък пропуск · доклад за въздействието · бройки за пълнота · проверка на дълбочината (proposed) |
| listing pass · listing rank · declined (a game) | преминаване през списъка · позиция в списъка · отслабнала (proposed) |
| concurrent players · idle game · Peak Players | едновременни играчи · игра с изчакване · Peak Players, the Steam Charts column name (proposed) |
| tie · tie-break | равенство · разрешаване на равенството (proposed) |
| tag vocabulary · parse errors' parsers · SteamDB batch · reviewer | речник на таговете · програми за разбор · партида от SteamDB · рецензент (proposed) |
| Feature analysis entries: Tag count and share · Median tag position · Eligible Pool baseline · Share ratio · Archived tag category · Genre frequency · Combination support · Combination lift · Confidence · Pair counts · Pair lift | Брой и дял на тага · Медианна позиция на тага · Базово ниво в пула на годните игри · Отношение на дяловете · Архивна категория на тага · Честота на жанровете · Подкрепа на комбинацията · Лифт на комбинацията · Достоверност · Бройки за двойка тагове · Лифт на двойка тагове (proposed) |
| combination (itemset) · support · confidence · association rule · itemset sizes (pairs, triples) | комбинация · подкрепа · достоверност · асоциативно правило · двойки и тройки тагове (a tag pair is *двойка тагове*, since *двойка* alone is the Threshold Pair; the bare word is kept only for the pairs inside a combination, or again in the sentence right after a qualified mention) (proposed) |
| co-occurrence · independence · interest (Brin et al.) · association table | съвместно срещане · независимост · интерес · таблица на асоциациите (proposed) |
| Phi coefficient · Fisher exact p · Benjamini-Hochberg q · Loevinger's H · false discovery rate | коефициент phi · стойност p от точния тест на Fisher (short: p на Fisher) · q на Benjamini-Hochberg · H на Loevinger · очакван дял на фалшивите открития (proposed) |
| screen (BH, Fisher) · chance finding · over- / under-represented | отсяване · случайна находка · свръхпредставен / недостатъчно представен (proposed) |
| generic tag · medoid score · business label (`kind`) · gameplay genre | широк таг (not *общ*, which is *shared*) · оценка на медоида · търговски етикет · жанр на геймплея (proposed) |
| The Tag Network entries: Edge weight (shared games) · Edge lift · Tag game count · Degree and isolated tags · Strength (weighted degree) · Per-tag silhouette · Medoid score · Top-strength tag · Within-cluster strength z-score · Participation coefficient · Layout positions · Tags not in the network | Тегло на реброто (общи игри) · Лифт на реброто · Брой игри на тага · Степен и изолирани тагове · Сила (претеглена степен) · Силует на тага · Оценка на медоида · Таг с най-голяма сила · z-оценка на силата в клъстера · Коефициент на участие · Позиции в изгледа · Тагове извън мрежата (proposed) |
| game set · medoid · within-module degree · population SD · edge inspector | множество игри · медоид · степен в модула · SD на съвкупността · инспектор на ребрата (proposed) |
| layout (Global, Cluster-separated) · loose layout · spring layout · gravity · main component | изглед (изгледът „Общо“, „По клъстери“) · свободно разположение · пружинно разположение · гравитация · основен компонент (proposed) |
| hub dissuasion (ForceAtlas2) | потискане на хъбовете: the same sense of *хъб* as in the Position entry, a tag linked to almost every other (proposed) |
| label-aware pass · box (node plus label) · graph area · zoom · zoomed out · packed (regions) · canvas · reference canvas | преминаване, съобразено с етикетите · кутия · областта на графа · приближение · отдалечен · подредени плътно · платно · еталонно платно (proposed) |
| Clusters and partition quality entries: the section · Cluster labels and counts · Network size · Null-model baseline · Excess modularity and z-score · Coverage and inter-cluster weight share · Disconnected clusters · Mean silhouette · Internal edges, weight and densities · Cut weight and conductance · Cluster connections · Games within a Cluster | Клъстери и качество на разбиването · Етикети и брой на клъстерите · Размер на мрежата · Отправна стойност от нулевия модел · Превишение на модулярността и z-оценка · Покритие и дял на теглото между клъстерите · Несвързани клъстери · Среден силует · Вътрешни ребра, тегло и плътности · Тегло на среза и проводимост · Връзки между клъстерите · Игри в клъстера (proposed) |
| group (of tags or characteristics, when not the Cluster itself) · grouping, structure | съвкупност (never *група*, the Cluster's Avoid word) · структура (proposed) |
| resolution limit · objective (Q) · finding · pass mark | граница на резолюцията · целева функция · находка · праг за преминаване (proposed) |
| cut weight · volume · edge density · weighted density · induced subgraph | тегло на среза · обем · плътност на ребрата · претеглена плътност · индуциран подграф (proposed) |
| permutation test · sample SD | пермутационен тест · SD на извадката (proposed) |
| Stability and Removal Sensitivity entries: Stability · Three kinds of stability · Adjusted Rand index · Seed spread of modularity and silhouette · Seed range of cluster counts · Run order and identity · Reclustered change in modularity · Reclustered silhouette · Reclustered change in cluster counts · Reclustered ARI · Centers lost · Fixed-partition change in modularity · Fixed-partition silhouette · Beyond-noise flag | Стабилност · Три вида стабилност · Коригиран индекс на Rand · Разброс на модулярността и силуета по начални числа · Обхват на броя клъстери по начални числа · Ред на изпълнение и идентичност · Промяна в модулярността при нова клъстеризация · Силует при нова клъстеризация · Промяна в броя клъстери при нова клъстеризация · ARI при нова клъстеризация · Изгубени центрове · Промяна в модулярността при фиксирано разбиване · Силует при фиксирано разбиване · Отметка „над шума“ (proposed) |
| algorithmic · parameter · data (the three kinds of stability) | алгоритмична · по параметрите · по данните (proposed) |
| noise seed · main seed · yardstick · companion (in a cluster) | начално число за шума · главно начално число · мерило · спътник (proposed) |
| fixed partition (`fp_`) · reorganisation · mechanical (change) · bridge tag · run order · active strength | фиксирано разбиване · преподреждане · механична · свързващ таг · ред на изпълнение · активна сила (proposed) |
| Parameter Selection entries: How Automatic Parameter Selection works · Threshold Pair and Parameter Grid · Admissible Partition and Optimality Domain · Resolution estimate and Stable Partition · Selected Partition and Selected Resolution · Isolated share and LCC share · Pair Constraints, Qualifying Pair and the selection rule | Как работи автоматичният избор на параметри · Двойка прагове и решетка на параметрите · Допустимо разбиване и област на оптималност · Оценка на резолюцията и стабилно разбиване · Избрано разбиване и избрана резолюция · Дял на изолираните тагове и дял на LCC · Ограничения за двойката, квалифицирана двойка и правилото за избор (proposed) |
| resolution estimate γ̂ · fixed-point test · map target · CHAMP plot · pass loop · canonical membership | оценка на резолюцията · тест за неподвижна точка · целево разбиване · графиката на CHAMP · цикъл от проходи · канонично членство (proposed) |
| degree-corrected planted-partition model · multigraph · likelihood · assortative · connected component | модел с вградено разбиване с корекция за степента · мултиграф · правдоподобие · асортативно · свързана компонента (proposed) |
| neighbour link (in prose) · compared tags · perturbation · tag–game assignment · degenerate (subsample) · retention share · without replacement | сравнение със съсед · сравнявани тагове · смущение · назначение таг–игра · изродена · дял на запазване · без връщане (proposed) |

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
| Field: (the Network State table's tooltip) | Поле: |
| Why it matters here | Защо има значение тук |
| Exact definition | Точна дефиниция |
| Example | Пример |
| Bounds | Граници |
| Compare with | Сравнете с |
| Shown in the app as | В приложението се показва като |

**References (Appendix C).** The bibliographic entries stay as published. Only the guide's own locators are Bulgarian: резюме, табл., ур., фиг., с., теорема, лема, следствие, твърдение, деф. The methods paragraph uses the same locators. Quotations from the literature (Appendix A) are translated, in „…“, with the Bulgarian number format.

**Quality words to avoid in Bulgarian In short blocks.** This is guidance for translating and reviewing; it has no test. Avoid: добър, лош, силен/силно, слаб, стабилен, устойчив, важен, значим/значителен, надежден, отличен. Glossary terms such as *стабилно разбиване* are exempt.

## Short UI words

| English | Bulgarian |
|---|---|
| n/a / yes / no | н/д / да / не |
| ag-grid: Contains · Not contains · Equals · Not equal · Starts with · Ends with | Съдържа · Не съдържа · Равно на · Различно от · Започва с · Завършва с |
| ag-grid: Less than · Greater than · In range · Blank · Not blank | По-малко от · По-голямо от · В интервала · Празно · Непразно |
| ag-grid: AND / OR · Filter... · No Rows To Show | И / ИЛИ · Филтър… · Няма редове |
| ag-grid: Less than or equal to · Greater than or equal to | По-малко или равно на · По-голямо или равно на |
| Width (and the legend's edge thickness) | Дебелина, дебелина на ребрата (avoid *ширина*) |
| Scaling: linear · √ · log | Мащаб: линеен · √ · log; in prose корен квадратен, логаритмичен (avoid *скалиране*) |
| Colour: one colour · By Cluster · within vs between · by value | Цвят: един цвят · по клъстер · вътре / между · по стойност (avoid *оцветяване*) |
| Strength (link opacity) | Наситеност (avoid *сила*, the metric Strength (weighted degree); *плътност*, graph density; *непрозрачност*) |
| Less · More | По-малко · Повече |
| Hide links below · Links between Clusters · Links between them | Скрий ребрата под (avoid *филтър*: that is Minimum shared games) · Ребра между клъстерите · Ребра между тях |
| Matched · "of its tags" | Съвпадащи (avoid *съвпадения*, *мачнати*) · от таговете ѝ (the game, *играта*, is feminine) |
| Show all {n} | Покажи всички {n} |
| Run · Cancel · Restore · Reset · Reset all · Close | Изпълни · Отказ · Възстанови · Нулирай · Нулирай всичко · Затвори (*Отказ* is the usual Bulgarian Cancel, a noun, the one exception to the imperative) |
| Unhide · Show JSON · copied | Покажи отново · Покажи JSON · копирано |
| Language · Search · Clear search · Graph only | Език · Търсене · Изчисти търсенето · Само графът |
| Tidy (the graph's relayout) | Подреди |
| Min games · Min shared · Months ≥ (short labels) | Мин. игри · Мин. общи · Месеци ≥ |
| the drawing (what Edge appearance changes) | изображението |
| job (a background run) | задача |
| min · s (the ETA and elapsed time) | min · s, SI symbols in Latin script, as `ms` and `s` in the estimate |
| Pair Inspector · Apply to Workbench · Copy from Workbench | Инспектор на двойката · Приложи в работното място · Копирай от работното място |
| Reset to defaults · Confirm · Use these settings | Върни стойностите по подразбиране · Потвърди · Използвай тези настройки |
| default · custom (the pills' values, and the strip's marker) | по подразбиране · персонализирани, agreeing with *ограничения* and *настройки* |

## Superseded words

Words the Bulgarian text must never use. Each is a stem, matched case-insensitively at the start of a word, so *сийд* also catches *сийда* and *сийдове*. An occurrence inside one of the row's allowed phrases is not a hit. Separate allowed phrases with `;`.

This list is short and deliberate, unlike the **Avoid** column: an Avoid word such as *филтър* or *мрежа* is correct in another term, so it cannot be scanned for. A word goes here when it is never right, or when a review replaces it.

| Stem | Allowed phrases |
|---|---|
| Жакар | — |
| Лайден | — |
| сийд | — |
| билд | — |

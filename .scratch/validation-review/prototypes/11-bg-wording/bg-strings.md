# bg wording: validation card and the Inspector's Validation section

Decided in [What is the bg wording of the validation card and the Inspector's Validation section?](../../issues/11-bg-wording-card-and-inspector.md).
These are the catalogue entries the spec cites (ADR 0003: keyed by the English text, two plural forms). The English keys are the
ones fixed by tickets 02, 04 and 06. Where an existing key already covers a string, the existing entry is reused as is. The
fit was checked in [the 06 prototype](../06-validation-layout/PROTOTYPE-validation-layout.html), whose `BG` table matches this file.

## Terms

| English | Prose | Short (headers, chips) |
|---|---|---|
| Hennig's Jaccard | `индекс на Jaccard по Hennig` | `Jaccard (Hennig)` |
| Whole-Cluster Jaccard | `индекс на Jaccard за целия клъстер` | `Jaccard (цял клъстер)` |
| Dissolved in most subsamples | `Разпаднат в повечето подизвадки` (one Cluster) / `Разпаднати в повечето подизвадки` (a list or count) | the same |
| borderline | `на границата` | the same |
| Not assessable | `Не може да се оцени` | the same (never `Неоценим`, which reads as *invaluable*) |
| rarely assessable | `рядко оценим` | the same |
| Q not above the null | `Q не е над нулевия модел` *(existing)* | the same |
| per-pair procedure | `процедурата за една двойка` | — |
| 10th–90th percentile | `персентили 10–90` | `перс. 10–90` |
| s.e. | `стандартна грешка` | `ст. гр.` |
| Wilson interval | `интервал на Wilson` (`95% интервал на Wilson`) | `95% Wilson` |
| domain (width) | `ширина на областта на оптималност` *(existing "domain")* | — |

Existing terms used unchanged: `разбъркани мрежи`, `при нов избор`, `при резолюцията`, `Сравнение с нулев модел`,
`Стабилност при подизвадки`, `Вариант` (Arm), `многотагови клъстери`, `избрано разбиване`, `подизвадка`.
Personal names stay in Latin script (Jaccard, Hennig, Wilson), as with `Cauchy–Schwarz` and `Weir et al.`

## Conventions

- **Plurals.** `tx.n` inflects only on `{n}`. When a count is not `{n}`, or sits in a parenthesis or list, the string takes
  the catalogue's **colon form** (`разбъркани мрежи: {r}`, `без ребра: {n}`). The only true plural pair is the dissolved-list
  lead (below). After a numeral, masculine nouns take the counted form (`15 многотагови клъстера`, not `клъстери`).
- **Numbers.** Use the decimal comma everywhere, through `tx.num` / `tx.fixed` / `tx.pct`, labels included (`≤ 0,5`, `> 0,75`).
  Prose ranges are `от 0,45 до 0,65` (the existing `"{lo} to {hi}"` entry). Compact ranges use an en dash with no spaces
  (`0,45–0,65`), and percent ranges attach the sign (`42–62%`). `½` and the minus sign `−` stay as they are. Compact ranges only
  carry Jaccard spreads and Wilson bounds (≥ 0). ARI, which can be negative, always uses `от … до`.
- **R / A** on the Cluster list and the Inspector strips stay Latin letters, glossed in the legend.

## Card

| English key | Bulgarian |
|---|---|
| `Validation of g = {g}, s = {s}` | *existing* `Валидиране на g = {g}, s = {s}` |
| `Validation ran for g = {g}, s = {s}, the pair chosen under the default constraints.` | *existing* |
| `No pair qualifies under your constraints, so this is the validation of g = {g}, s = {s}, the pair chosen under the default constraints.` | `При вашите ограничения не се квалифицира нито една двойка, затова това е валидирането на g = {g}, s = {s}: двойката, избрана при ограниченията по подразбиране.` |
| `({r} shuffled networks, per-pair procedure at g = {g}, s = {s})` | `(разбъркани мрежи: {r}; процедурата за една двойка при g = {g}, s = {s})` |
| `Q at resolution {res} is {q};` | `Q при резолюция {res} е {q};` |
| `none of the {d} shuffled networks with a Q reaches it (range over {d} shuffled networks: {lo} to {hi})` | `никоя разбъркана мрежа с Q не го достига (разбъркани мрежи с Q: {d}; обхват от {lo} до {hi})` |
| `{k} of {d} shuffled networks with a Q reach it: Q not above the null` | `разбъркани мрежи с Q, които го достигат: {k} от {d}; Q не е над нулевия модел` |
| `no shuffled network has edges, so Q cannot be compared.` | `никоя разбъркана мрежа няма ребра, затова Q не може да се сравни.` |
| `{n} had no edges` | *existing* `без ребра: {n}` (both forms) |
| `{n} lay beyond their γ scan` | `извън своето сканиране по γ: {n}` (both forms) |
| `Most shuffled networks have no Q ({u} of {r}), so this comparison is weak.` | `Повечето разбъркани мрежи нямат Q ({u} от {r}), затова това сравнение е слабо.` |
| `Multi-Tag Clusters: observed {o}, median {m} (range over {k} shuffled networks with a Selected Partition: {lo} to {hi}).` | `Многотагови клъстери: наблюдавани {o}, медиана {m} (разбъркани мрежи с избрано разбиване: {k}; обхват от {lo} до {hi}).` |
| `None of the {r} shuffled networks has a Selected Partition.` | `Нито една от {r} разбъркани мрежи няма избрано разбиване.` |
| `Median domain width {m} vs observed {o}; observed wider than {n} of {k}.` | `Ширина на областта на оптималност: медиана {m} срещу наблюдавана {o}; наблюдаваната е по-широка от {n} от {k}.` |
| `Widths are upper bounds, conditional on the partitions the γ scan finds.` | `Ширините са горни граници и зависят от разбиванията, които сканирането по γ намира.` |
| `This shows only that the network is not random, not that its Clusters are real.` | `Това показва само, че мрежата не е случайна, а не че клъстерите ѝ са реални.` |
| `({t} random 80% subsets of the games, g′ = {g}, s′ = {s}).` | *existing* (placeholder `{total}` there) |
| `Re-selected: median ARI {m} (10th–90th percentile: {lo} to {hi}) over {n} of {t} subsamples, on {e} of the tags.` | `При нов избор: медиана на ARI {m} (персентили 10–90: от {lo} до {hi}) при {n} от {t} подизвадки, върху {e} от таговете.` |
| `At resolution {res}: median ARI {m} (10th–90th percentile: {lo} to {hi}).` | `При резолюция {res}: медиана на ARI {m} (персентили 10–90: от {lo} до {hi}).` |
| `Dissolved in most subsamples (Hennig's Jaccard ≤ 0.5 in more than half; the majority is this study's rule):` **(one key: bold lead + parenthesis; the template bolds the text before the first " (")** | `Разпаднати в повечето подизвадки (индекс на Jaccard по Hennig ≤ 0,5 в повече от половината; правилото на мнозинството е избор на това изследване):` |
| `{k} of {n} Multi-Tag Clusters in both arms` (`tx.n` on `{n}`; English one: `{k} of {n} Multi-Tag Cluster in both arms`) | one: `{k} от {n} многотагов клъстер в двата варианта` · other: `{k} от {n} многотагови клъстера в двата варианта` |
| `re-selected only` · `at resolution only` | `само при нов избор` · `само при резолюцията` |
| `Borderline (the 95% Wilson interval contains ½):` | `На границата (95% интервал на Wilson съдържа ½):` |
| `in both arms` | `в двата варианта` |
| `No Multi-Tag Cluster is dissolved in most subsamples in either arm.` | `В нито един вариант няма многотагов клъстер, разпаднат в повечето подизвадки.` |
| `Not assessable (fewer than 2 of its tags survive in every subsample):` | `Не може да се оцени (във всяка подизвадка оцеляват по-малко от 2 негови тага):` |
| `This measures how much the clustering depends on which games are in the dataset. It does not show that a Cluster is right.` | `Това измерва доколко клъстеризацията зависи от това кои игри са в набора. Не показва, че даден клъстер е верен.` |
| `The pair was chosen on the same data, so Subsample Stability may be slightly optimistic. Q played no part in the choice, so the Null Comparison is barely affected.` | `Двойката е избрана върху същите данни, затова стабилността при подизвадки може да е леко оптимистична. Q не участва в избора, така че сравнението с нулев модел почти не е засегнато.` |
| `Three kinds of stability` · `Null Comparison` · `Subsample Stability` | *existing* |

## Cluster list (interval plot) and its expanded rows

| English key | Bulgarian |
|---|---|
| `Share of subsamples with Hennig's Jaccard ≤ 0.5, with its 95% Wilson interval. R = re-selected, A = at resolution.` | `Дял на подизвадките с индекс на Jaccard по Hennig ≤ 0,5, с неговия 95% интервал на Wilson. R = при нов избор, A = при резолюцията.` |
| `Click a row for every figure.` | `Щракнете върху ред, за да видите всички стойности.` |
| `Cluster` · `Size` · `Status` | `Клъстер` · `Размер` · `Статус` |
| `≤ 0.5: 0 — ½ — 1` (plot axis header; becomes a key) | `≤ 0,5: 0 — ½ — 1` |
| `Arm` · `re-selected` · `at resolution` | *existing* `Вариант` · `при нов избор` · `при резолюцията` |
| `Hennig's J` / `mean ± s.e.; 10th–90th pct` | `Jaccard (Hennig)` / `средно ± ст. гр.; перс. 10–90` |
| `≤ 0.5 in` / `> 0.75 in` / `k of B*; 95% Wilson` | `≤ 0,5 в` / `> 0,75 в` / `k от B*; 95% Wilson` |
| `Whole-Cluster J` / `mean ± s.e.` | `Jaccard (цял клъстер)` / `средно ± ст. гр.` |
| `{k} of {n}` | `{k} от {n}` |
| `Dissolved in most subsamples` (chip) | `Разпаднат в повечето подизвадки` |
| `borderline` (chip) | `на границата` |
| `Not assessable` (chip, and in the plot) | `Не може да се оцени` |
| `rarely assessable ({b} of {s})` | `рядко оценим ({b} от {s})` |

**Layout amendment to 06:** the Size column is **44 px** in both the wide and narrow-fit grids (was 34 / 30 px): `Размер` is
39 px. With 44 px nothing overflows or overlaps in either language at wide 1280 / 1600, medium 1100 and narrow 800. The
expanded-row headers wrap to three lines in bg at wide 1280 (two in English), with no overflow.

## Inspector's Validation section

| English key | Bulgarian |
|---|---|
| `Validation` · `Not validated` · `Validate this pair` | *existing* |
| `About 3 min on 12 workers.` | `Около 3 мин с 12 процеса.` |
| `Q above all {d} shuffled networks` | `Q е над всички {d} разбъркани мрежи` |
| `Q not above the null ({k} of {d})` | `Q не е над нулевия модел ({k} от {d})` |
| `Null Q undefined` | `Q на нулевия модел е неопределено` |
| `Dissolved in most subsamples (re-selected): {n}` | `Разпаднати в повечето подизвадки (при нов избор): {n}` |
| `median ARI re-selected {a}, at resolution {b}` | *existing* (placeholders `{reselected}`, `{at}` there) |
| `Open the validation card` | `Отвори картата за валидиране` |

The draft's `Инспектор на двойки` is dropped: the existing `Pair Inspector` entry, `Инспектор на двойката`, stands.

## Retired keys

The changed English retires these existing entries (ADR 0003: the parity test fails until they are removed):
`Dissolved`, `Dissolved: {n}`, `mean Jaccard`, `≤ 0.5 in k of B*`, `retention share`, `absent`, the three
`… is dissolved … (mean Jaccard ≤ 0.5)` sentences, `Q above all null replicates`, and any of `ps_view` / `selection_text`'s
validation sentences whose English tickets 02 and 04 replaced. The spec lists the exact set against the final English.

Strings used only by the losing layouts A and B (`Observed`, `Shuffled networks`, `Domain width`, `not at resolution`, …) are
in the prototype's `BG` table so it still renders, but they don't ship and aren't catalogue entries.

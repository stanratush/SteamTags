"""Bulgarian: selection_text. Keyed by the English text (see `steamstudy.i18n`); filled by the bulk translation."""

MESSAGES: dict[str, str | dict[str, str]] = {
    # The settings and constraints labels (network/selection.py)
    "hidden Genre Tags {n} (default {default})": "скрити жанрови тагове: {n} (по подразбиране {default})",
    "hidden": "скрит",
    "shown": "показан",
    "defining tag {now} (default {default})": "определящ таг: {now} (по подразбиране {default})",
    "Minimum Months {n} (default {default})": "минимум месеци: {n} (по подразбиране {default})",
    "Clustering Weight {now} (default {default})": "тегло за клъстеризация: {now} (по подразбиране {default})",
    "minimum Multi-Tag Clusters {n} (default {default})":
        "минимум многотагови клъстери: {n} (по подразбиране {default})",
    "{n} removed tag ({tags})": {"one": "{n} премахнат таг ({tags})", "other": "{n} премахнати тага ({tags})"},
    "Custom settings: {changes}": "Персонализирани настройки: {changes}",
    "Default settings": "Настройки по подразбиране",
    "tolerance {value} (default {default})": "допуск {value} (по подразбиране {default})",
    "Information Retention ≥ {value} (default {default})":
        "запазване на информацията ≥ {value} (по подразбиране {default})",
    "isolated share ≤ {value} (default {default})": "дял на изолираните тагове ≤ {value} (по подразбиране {default})",
    "LCC share ≥ {value} (default {default})": "дял на LCC ≥ {value} (по подразбиране {default})",
    "comparable neighbours ≥ {value} (default {default})": "сравними съседи ≥ {value} (по подразбиране {default})",
    "Multi-Tag Clusters ≤ {value} (default {default})": "многотагови клъстери ≤ {value} (по подразбиране {default})",
    "Custom constraints: {changes}": "Персонализирани ограничения: {changes}",
    "Default constraints": "Ограничения по подразбиране",
    # The constraints in words
    "retention": "запазване на информацията",
    "isolated-share": "дял на изолираните тагове",
    "LCC": "LCC",
    "neighbour": "сравними съседи",
    "Information Retention ≥ {value}": "запазване на информацията ≥ {value}",
    "isolated tags ≤ {value}": "изолирани тагове ≤ {value}",
    "largest component ≥ {value} of the tags with an edge": "най-голяма компонента ≥ {value} от таговете с ребро",
    "≥ {n} neighbours with a different graph": "съседи с различен граф ≥ {n}",
    "at most {n} Multi-Tag Clusters": "многотагови клъстери: най-много {n}",
    "the default constraints": "ограниченията по подразбиране",
    "the custom constraints": "персонализираните ограничения",
    # "Why this pair"
    "(cannot be entered as a two-decimal value)": "(не може да се въведе като стойност с два знака след запетаята)",
    "(Workbench {gamma})": "(в работното място {gamma})",
    "Selected: g = {g}, s = {s}": "Избрана: g = {g}, s = {s}",
    "Inspected: g = {g}, s = {s}": "Разгледана: g = {g}, s = {s}",
    "It does not qualify: {reasons}.": "Не се квалифицира: {reasons}.",
    "It qualifies and is within {tolerance} of the highest Neighbour Agreement among the qualifying pairs, {na} "
    "(g = {g}, s = {s}); of these near-best pairs the one with the smallest g, then the smallest s, is selected.":
        "Квалифицира се и е в рамките на {tolerance} от най-високото съгласие със съседите сред квалифицираните "
        "двойки, {na} (g = {g}, s = {s}); от тези почти най-добри двойки се избира тази с най-малко g, после с "
        "най-малко s.",
    "It qualifies, but its Neighbour Agreement is more than {tolerance} below the highest among the qualifying "
    "pairs, {na} (g = {g}, s = {s}).":
        "Квалифицира се, но съгласието ѝ със съседите е с повече от {tolerance} под най-високото сред "
        "квалифицираните двойки, {na} (g = {g}, s = {s}).",
    "The selected pair is g = {g}, s = {s}.": "Избраната двойка е g = {g}, s = {s}.",
    "No pair qualifies under {under}.": "Нито една двойка не се квалифицира при {under}.",
    ", resolution {resolution} {where}.": ", резолюция {resolution} {where}.",
    "Workbench {gamma} with the main seed shows a different partition.":
        "Стойността {gamma} в работното място с основното начално число дава различно разбиване.",
    "{selected} of {pairs} pairs have a Selected Partition.": "Двойки с избрано разбиване: {selected} от {pairs}.",
    "{n} qualify under {under}: {constraints}.": "Квалифицирани при {under}: {n} ({constraints}).",
    "The {names} constraint excluded no pair.": {
        "one": "Ограничение, което не изключи нито една двойка: {names}.",
        "other": "Ограничения, които не изключиха нито една двойка: {names}."},
    "The highest Neighbour Agreement among them is {na} (g = {g}, s = {s}).":
        "Най-високото съгласие със съседите сред тях е {na} (g = {g}, s = {s}).",
    "{n} pair is within {tolerance} of it, and of these the one with the smallest g, then the smallest s, is "
    "selected.": {
        "one": "{n} двойка е в рамките на {tolerance} от него; от двойките в този допуск се избира тази с най-малко g, "
               "после с най-малко s.",
        "other": "{n} двойки са в рамките на {tolerance} от него; от тях се избира тази с най-малко g, после с "
                 "най-малко s."},
    "Its Neighbour Agreement is {na} over {n} neighbour with a different graph.": {
        "one": "Съгласието ѝ със съседите е {na} при {n} съсед с различен граф.",
        "other": "Съгласието ѝ със съседите е {na} при {n} съседа с различен граф."},
    "{n} more neighbour has an identical graph and is not counted.": {
        "one": "Още {n} съсед има идентичен граф и не се брои.",
        "other": "Още {n} съседа имат идентичен граф и не се броят."},
    "Its Selected Partition has the minimum {k} Multi-Tag Clusters; a coarser split was not allowed.":
        "Избраното ѝ разбиване има минималния брой многотагови клъстери ({k}); по-едро разбиване не е позволено.",
    "The Seed-Noise Floor at this resolution is {floor}: the clustering also depends noticeably on the seed.":
        "Прагът на шума от началното число при тази резолюция е {floor}: клъстеризацията зависи осезаемо и от "
        "началното число.",
    "{phrase}: {alone} ({cumulative})": "{phrase}: {alone} ({cumulative})",
    "No pair qualifies": "Нито една двойка не се квалифицира",
    "under {under}. {selected} of {pairs} pairs have a Selected Partition. Excluded by each constraint, alone "
    "(cumulative): {excluded}. Loosen a constraint, or inspect any pair in the grid and apply it by hand.":
        "при {under}. Двойки с избрано разбиване: {selected} от {pairs}. Изключени от всяко ограничение, "
        "самостоятелно (натрупано): {excluded}. Разхлабете някое ограничение или разгледайте която и да е двойка в "
        "решетката и я приложете ръчно.",
    # Validation: the Null Comparison and Subsample Stability sentences
    "{n} had no edges": {"one": "без ребра: {n}", "other": "без ребра: {n}"},
    "{n} lay beyond their γ scan": {"one": "извън своето сканиране по γ: {n}",
                                    "other": "извън своето сканиране по γ: {n}"},
    "{n} had no Selected Partition": {"one": "без избрано разбиване: {n}", "other": "без избрано разбиване: {n}"},
    "({r} shuffled networks, per-pair procedure at g = {g}, s = {s})":
        "(разбъркани мрежи: {r}; процедурата за една двойка при g = {g}, s = {s})",
    "Q at resolution {resolution} is {q};": "Q при резолюция {resolution} е {q};",
    "none of the {d} shuffled networks with a Q reaches it (range over {d} shuffled networks: {lo} to {hi})":
        "никоя разбъркана мрежа с Q не го достига (разбъркани мрежи с Q: {d}; обхват от {lo} до {hi})",
    "{k} of {d} shuffled networks with a Q reach it: Q not above the null":
        "разбъркани мрежи с Q, които го достигат: {k} от {d}; Q не е над нулевия модел",
    "no shuffled network has edges, so Q cannot be compared.":
        "никоя разбъркана мрежа няма ребра, затова Q не може да се сравни.",
    "no shuffled network has a Q ({reasons}), so Q cannot be compared.":
        "никоя разбъркана мрежа няма Q ({reasons}), затова Q не може да се сравни.",
    "The runs at γ_obs found a Q of {q} on the observed network, above its Selected Partition's {q0}; the comparison "
    "uses {q}.":
        "Изпълненията при γ_obs намериха Q {q} за наблюдаваната мрежа, над {q0} на избраното ѝ разбиване; сравнението "
        "използва {q}.",
    "Most shuffled networks have no Q ({u} of {r}), so this comparison is weak.":
        "Повечето разбъркани мрежи нямат Q ({u} от {r}), затова това сравнение е слабо.",
    "Multi-Tag Clusters: observed {observed}, median {median} (range over {k} shuffled networks with a Selected "
    "Partition: {lo} to {hi}).":
        "Многотагови клъстери: наблюдавани {observed}, медиана {median} (разбъркани мрежи с избрано разбиване: {k}; "
        "обхват от {lo} до {hi}).",
    "None of the {r} shuffled networks has a Selected Partition.":
        "Нито една от {r} разбъркани мрежи няма избрано разбиване.",
    "Median domain width {median} vs observed {observed}; observed wider than {n} of {k}.":
        "Ширина на областта на оптималност: медиана {median} срещу наблюдавана {observed}; наблюдаваната е по-широка "
        "от {n} от {k}.",
    "Median domain width {median} vs observed {observed}; observed wider than {n}, equal to {t}, of {k}.":
        "Ширина на областта на оптималност: медиана {median} срещу наблюдавана {observed}; наблюдаваната е по-широка "
        "от {n} и равна на {t} от {k}.",
    "Widths are upper bounds, conditional on the partitions the γ scan finds.":
        "Ширините са горни граници и зависят от разбиванията, които сканирането по γ намира.",
    "({total} random 80% subsets of the games, g′ = {g}, s′ = {s}).":
        "(случайни подмножества от 80% от игрите: {total}, g′ = {g}, s′ = {s}).",
    "Re-selected: no subsample has a Selected Partition ({reasons}).":
        "При нов избор: никоя подизвадка няма избрано разбиване ({reasons}).",
    "Re-selected: median ARI {median} (10th–90th percentile: {p10} to {p90}) over {n} of {total} subsamples, on "
    "{share} of the tags":
        "При нов избор: медиана на ARI {median} (персентили 10–90: от {p10} до {p90}) при {n} от {total} подизвадки, "
        "върху {share} от таговете",
    "At resolution {resolution}: median ARI {median} (10th–90th percentile: {p10} to {p90})":
        "При резолюция {resolution}: медиана на ARI {median} (персентили 10–90: от {p10} до {p90})",
    "At resolution {resolution}: no subsample can be compared ({reasons}).":
        "При резолюция {resolution}: никоя подизвадка не може да се сравни ({reasons}).",
    "Dissolved in most subsamples (Hennig's Jaccard ≤ 0.5 in more than half; the majority is this study's rule):":
        "Разпаднати в повечето подизвадки (индекс на Jaccard по Hennig ≤ 0,5 в повече от половината; правилото на "
        "мнозинството е избор на това изследване):",
    "{k} of {n} Multi-Tag Cluster in both arms": {"one": "{k} от {n} многотагов клъстер в двата варианта",
                                                  "other": "{k} от {n} многотагови клъстера в двата варианта"},
    "re-selected only": "само при нов избор",
    "at resolution only": "само при резолюцията",
    "in both arms": "в двата варианта",
    "Borderline (the 95% Wilson interval contains ½):": "На границата (95% интервал на Wilson съдържа ½):",
    "Not assessable (fewer than 2 of its tags survive in every subsample):":
        "Не може да се оцени (във всяка подизвадка оцеляват по-малко от 2 негови тага):",
    "No Multi-Tag Cluster is dissolved in most subsamples in either arm.":
        "В нито един вариант няма многотагов клъстер, разпаднат в повечето подизвадки.",
    "Validation of g = {g}, s = {s}": "Валидиране на g = {g}, s = {s}",
    "Validation ran for g = {g}, s = {s}, the pair chosen under the default constraints.":
        "Валидирането е за g = {g}, s = {s}: двойката, избрана при ограниченията по подразбиране.",
    "No pair qualifies under your constraints, so this is the validation of g = {g}, s = {s}, the pair chosen under "
    "the default constraints.":
        "При вашите ограничения не се квалифицира нито една двойка, затова това е валидирането на g = {g}, s = {s}: "
        "двойката, избрана при ограниченията по подразбиране.",
    "Not validated.": "Не е валидирано.",
    # The methods paragraph
    "For each Top-100 Dataset we built the Tag Network at every Threshold Pair (g, s) of the Parameter Grid, "
    "{g_range} games per tag and {s_range} shared games with s ≤ g ({n_pairs} pairs), with {weight} as the "
    "Clustering Weight, a Minimum Months Filter of {min_months} and {hidden} hidden. On each distinct graph we ran "
    "Leiden (RBConfiguration, at most 1,000 passes) with {scan_seeds} seeds at every γ from 0 to Gibson and "
    "Mucha's γ_max(K), K being the number of tags with an edge, in steps of {gamma_step} (Gibson & Mucha 2022, "
    "SI §J); the derivation in SI §J.2 uses only the Cauchy–Schwarz inequality and assortativity, so the bound "
    "also holds for Clusters of unequal size and for weighted graphs. The unique partitions found were reduced to "
    "the upper envelope of their lines Q(γ) = Â − γP̂, giving the Admissible Partitions and their Optimality "
    "Domains (CHAMP; Weir et al. 2017, §2, eqs. 1–4). For each we evaluated once the self-consistent resolution "
    "γ̂ = (ω_in − ω_out)/(ln ω_in − ln ω_out) (Newman 2016, §III.A, eqs. 15–18) and called the partition stable "
    "when γ̂ lies in its own domain (Gibson & Mucha 2022, Fig. 1(d), SI §C.2–C.3). Among the Stable Partitions "
    "with at least {min_multi} Multi-Tag Clusters, the Selected Partition has the widest domain in plain γ "
    "units, and the Selected Resolution is the domain's midpoint; the sources give no rule for choosing among "
    "Stable Partitions, and we did not rescale the width to log γ or to Gibson and Mucha's γ-scaled area "
    "(SI §A.7), whose usefulness the authors leave open. Neighbour Agreement is the mean adjusted Rand index "
    "between a pair's Selected Partition and those of its grid neighbours (g ± 1, s ± 1) with a different graph, "
    "on the shared tags with an edge in either graph. The chosen pair is the one with the smallest g, then the "
    "smallest s, among the pairs whose Neighbour Agreement is within {tolerance} of the highest, among pairs with "
    "{constraints}. We compared each validated Threshold Pair with {replicates} networks whose game–tag table was "
    "shuffled by curveball trades (every tag and game keeps its count; Strona et al. 2014), each analysed by the "
    "identical procedure: the per-pair procedure at the same Threshold Pair (its own γ scan, CHAMP, γ̂ and the "
    "Selected Partition rule), not the Parameter Grid or the choice of pair (Karrer, Levina & Newman 2008, abstract, "
    "§III and §VI). Q at the observed Selected Resolution was taken as the best of each network's scan envelope and 10 "
    "Leiden runs at exactly that γ, on the observed network and every replicate alike; we report how many of the D "
    "shuffled networks with a defined Q reach the observed Q, and give no p-value, because the resolution and the pair "
    "were chosen on the observed data. We also compared the pair with {subsamples} random subsets of m = ⌊0.8·n⌋ of "
    "the n games, with the thresholds scaled by floor (g′ = ⌊g·m/n⌋, s′ = max(2, ⌊s·m/n⌋)), once re-selecting by the "
    "same per-pair procedure and once reading the partition at the observed resolution. For each Multi-Tag Cluster we "
    "report Hennig's (2007, §2) mean best-match Jaccard on its tags present in both networks, over the B* subsamples "
    "in which at least two of them survive, with its Monte Carlo standard error and the frequencies of values ≤ 0.5 "
    "and > 0.75 with 95% Wilson intervals (Wilson 1927), and a Whole-Cluster Jaccard that counts lost tags as not "
    "recovered. We call a Cluster dissolved in most subsamples when its Jaccard is 0.5 or less in more than half of "
    "the B* subsamples (the per-subsample cut is Hennig's, the majority our rule); the 0.6, 0.75 and 0.85 bands of the "
    "fpc package refer to the bootstrap and are not applied. The pair was chosen on the same data, so Subsample "
    "Stability may be slightly optimistic.":
        "За всеки набор Топ-100 изградихме мрежата от тагове при всяка двойка прагове (g, s) от решетката на "
        "параметрите, {g_range} игри на таг и {s_range} общи игри, с s ≤ g (двойки: {n_pairs}), с тегло за "
        "клъстеризация {weight}, филтър за минимум месеци {min_months} и скрити {hidden}. Върху всеки различен граф "
        "изпълнихме Leiden (RBConfiguration, най-много 1000 прохода) с начални числа: {scan_seeds}, при всяко γ от 0 "
        "до γ_max(K) на Gibson и Mucha, където K е броят на таговете с ребро, със стъпка {gamma_step} (Gibson & "
        "Mucha 2022, SI §J); изводът в SI §J.2 използва само неравенството на Cauchy–Schwarz и асортативността, "
        "затова границата важи и за клъстери с неравен размер, и за претеглени графи. Намерените уникални "
        "разбивания сведохме до горната обвивка на правите им Q(γ) = Â − γP̂, което дава допустимите разбивания и "
        "техните области на оптималност (CHAMP; Weir et al. 2017, §2, ур. 1–4). За всяко от тях еднократно "
        "пресметнахме самосъгласуваната резолюция γ̂ = (ω_in − ω_out)/(ln ω_in − ln ω_out) (Newman 2016, §III.A, "
        "ур. 15–18) и нарекохме разбиването стабилно, когато γ̂ лежи в собствената му област (Gibson & Mucha 2022, "
        "фиг. 1(d), SI §C.2–C.3). Сред стабилните разбивания с поне {min_multi} многотагови клъстера избраното "
        "разбиване е това с най-широка област в обикновени единици γ, а избраната резолюция е средата на областта; "
        "източниците не дават правило за избор между стабилни разбивания и ние не преизчислихме ширината спрямо "
        "log γ или спрямо γ-мащабираната площ на Gibson и Mucha (SI §A.7), чиято полезност авторите оставят "
        "открита. Съгласието със съседите е средният коригиран индекс на Rand между избраното разбиване на дадена "
        "двойка и тези на съседите ѝ в решетката (g ± 1, s ± 1) с различен граф, върху общите тагове с ребро в поне "
        "един от двата графа. Избраната двойка е тази с най-малко g, после с най-малко s, сред двойките, чието "
        "съгласие със съседите е в рамките на {tolerance} от най-високото, сред двойките със {constraints}. Сравнихме "
        "всяка валидирана двойка прагове с {replicates} мрежи, чиято таблица игри–тагове е разбъркана чрез размени "
        "curveball (всеки таг и всяка игра запазват броя си; Strona et al. 2014), всяка анализирана по същата "
        "процедура: процедурата за една двойка при същата двойка прагове (собствено сканиране по γ, CHAMP, γ̂ и "
        "правилото за избраното разбиване), а не решетката на параметрите или изборът на двойка (Karrer, Levina & "
        "Newman 2008, резюме, §III и §VI). Q при наблюдаваната избрана резолюция взехме като най-доброто от горната "
        "обвивка на сканирането на всяка мрежа и 10 изпълнения на Leiden точно при тази γ, еднакво за наблюдаваната "
        "мрежа и за всяко повторение; отчитаме колко от D-те разбъркани мрежи с определено Q достигат наблюдаваното Q "
        "и не даваме стойност p, защото резолюцията и двойката са избрани върху наблюдаваните данни. Сравнихме "
        "двойката и с {subsamples} случайни подмножества от m = ⌊0.8·n⌋ от n-те игри, с прагове, мащабирани със "
        "закръгляне надолу (g′ = ⌊g·m/n⌋, s′ = max(2, ⌊s·m/n⌋)), веднъж с нов избор по същата процедура за една двойка "
        "и веднъж с разбиването при наблюдаваната резолюция. За всеки многотагов клъстер отчитаме средния индекс на "
        "Jaccard за най-добро съвпадение на Hennig (2007, §2) върху таговете му, присъстващи и в двете мрежи, по B* "
        "подизвадките, в които оцеляват поне два от тях, със стандартната му грешка по Monte Carlo и честотите на "
        "стойностите ≤ 0,5 и > 0,75 с 95% интервали на Wilson (Wilson 1927), както и индекс на Jaccard за целия "
        "клъстер, който брои изгубените тагове като невъзстановени. Наричаме клъстер разпаднат в повечето подизвадки, "
        "когато индексът му е 0,5 или по-малко в повече от половината от B* подизвадки (границата за една подизвадка е "
        "на Hennig, мнозинството е наше правило); граничните зони 0,6, 0,75 и 0,85 на пакета fpc се отнасят за "
        "bootstrap и не се прилагат. Двойката е избрана върху същите данни, затова стабилността при подизвадки може да "
        "е леко оптимистична.",
    "{n} Genre Tags and each dataset's defining tag": "жанрови тагове ({n}) и определящия таг на всеки набор",
    "{n} Genre Tags": "жанрови тагове ({n})",
    # The declared sentences (selection_text.SENTENCES)
    "Neighbour Agreement measures how little the clustering changes when g or s moves by one. It does not show that "
    "the Clusters are real.":
        "Съгласието със съседите измерва колко малко се променя клъстеризацията, когато g или s се промени с "
        "единица. То не показва, че клъстерите са реални.",
    "Neighbour Agreement tends to be higher at large g because a one-step change in the thresholds, particularly s, "
    "generally produces a smaller change in the graph. This can increase agreement independently of the robustness "
    "of the Clusters. Choosing the smallest g among near-best pairs partially counterbalances this tendency.":
        "Съгласието със съседите обикновено е по-високо при голямо g, защото промяна на праговете с една стъпка, "
        "особено на s, по правило променя графа по-малко. Това може да повиши съгласието независимо от робастността "
        "на клъстерите. Изборът на най-малкото g сред почти най-добрите двойки отчасти уравновесява тази тенденция.",
    "Descriptive: not comparable across pairs": "Описателно: не е сравнимо между двойките",
    "Describes this pair's Selected Partition on its own network. Pairs differ in tags and edges, so a higher value "
    "at one pair does not make it a better choice.":
        "Описва избраното разбиване на тази двойка в собствената ѝ мрежа. Двойките се различават по тагове и ребра, "
        "затова по-висока стойност при една двойка не я прави по-добър избор.",
    "Each dataset is selected on its own, from its own games and tags. Different pairs in different datasets are "
    "expected and are not a disagreement: the same pair builds networks of different sizes in different datasets.":
        "Всеки набор се избира самостоятелно, от собствените си игри и тагове. Различни двойки в различните набори "
        "са очаквани и не са несъгласие: една и съща двойка изгражда мрежи с различен размер в различните набори.",
    "Leiden only: the scan and Apply's reproduction search are built on it":
        "Само Leiden: сканирането и търсенето за възпроизвеждане при „Приложи“ са изградени върху него",
    "No selection yet. {done} of {total} pairs are computed; the selection needs the whole grid.":
        "Все още няма избор. Изчислени двойки: {done} от {total}; изборът изисква цялата решетка.",
    "No results for these settings yet. Run computes them.":
        "Все още няма резултати за тези настройки. „Изпълни“ ги изчислява.",
    "This shows only that the network is not random, not that its Clusters are real.":
        "Това показва само, че мрежата не е случайна, а не че клъстерите ѝ са реални.",
    "This measures how much the clustering depends on which games are in the dataset. It does not show that the "
    "Clusters are real either.":
        "Това измерва доколко клъстеризацията зависи от това кои игри са в набора. И то не показва, че клъстерите са "
        "реални.",
    "The pair was chosen on the same data, so Subsample Stability may be slightly optimistic. Q played no part in the "
    "choice, so the Null Comparison is barely affected.":
        "Двойката е избрана върху същите данни, затова стабилността при подизвадки може да е леко оптимистична. Q не "
        "участва в избора, така че сравнението с нулев модел почти не е засегнато.",
}

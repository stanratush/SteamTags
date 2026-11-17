"""Bulgarian: comparison_text. Keyed by the English text (see `steamstudy.i18n`)."""

MESSAGES: dict[str, str | dict[str, str]] = {
    # The caution (network/comparison_text.py: CAUTION), as the spec gives it
    ("A Cluster Match says that two Clusters, each found at its dataset's settings, share Tags. It is not evidence "
     "that the Clusters are real or that the datasets share a genre structure. A match can appear, vanish or change "
     "its Match Jaccard with the seed, with g and s, and with the resolution. Read it against each dataset's "
     "Seed-Noise Floor and Neighbour Agreement."):
        ("Съвпадението на клъстери показва, че два клъстера, всеки намерен при настройките на своя набор, имат общи "
         "тагове. То не доказва, че клъстерите са реални или че наборите имат обща жанрова структура. Съвпадение "
         "може да се появи, да изчезне или да промени индекса си на Jaccard при друго начално число, при други g и s "
         "и при друга резолюция. Четете го спрямо прага на шума от началното число и съгласието със съседите на "
         "всеки набор."),
    # The readings (READINGS)
    ("Two Multi-Tag Clusters, one from each dataset, that share at least one Tag; it says they share Tags, not that "
     "they are the same group."):
        ("Два многотагови клъстера, по един от всеки набор, които имат поне един общ таг; казва, че имат общи тагове, "
         "а не че са една и съща група."),
    ("The shared Tags as a share of all Tags in either Cluster; 1 = the same Tags, 0 = none in common; a Tag missing "
     "from the other network counts against it."):
        ("Общите тагове като дял от всички тагове в двата клъстера; 1 = същите тагове, 0 = нито един общ; таг, който "
         "липсва в другата мрежа, го понижава."),
    ("The same overlap on the Comparable Tags only; never lower than Match Jaccard, and the gap shows how much of a "
     "low score comes from Tags missing from the other network; \"—\" when either Cluster has fewer than two "
     "Comparable Tags."):
        ("Същото припокриване само върху сравнимите тагове; никога не е по-ниско от индекса на Jaccard на "
         "съвпадението, а разликата показва каква част от ниската стойност идва от тагове, които липсват в другата "
         "мрежа; „—“, когато някой от клъстерите има по-малко от два сравними тага."),
    ("The share of one Cluster's Tags that the other also has; they differ when the sizes differ; 100% on one side "
     "means that Cluster lies wholly inside the other."):
        ("Делът от таговете на единия клъстер, които има и другият; двата дяла се различават, когато размерите се "
         "различават; 100% от едната страна означава, че този клъстер е изцяло в другия."),
    ("Shared Tags ÷ what two Clusters of these sizes would share if Tags were placed at random among the Comparable "
     "Tags; 1× = the sizes alone; descriptive, no p-value, since Clusters are not random draws."):
        ("Общите тагове ÷ колко биха имали общо два клъстера с тези размери, ако таговете бяха разпределени случайно "
         "сред сравнимите тагове; 1× = само размерите; описателно, без p-стойност, защото клъстерите не са случайни "
         "извадки."),
    ("How alike the two partitions are on the Comparable Tags with an edge in either network; 1 = identical, around "
     "0 = no more than chance."):
        ("Колко си приличат двете разбивания върху сравнимите тагове с ребро в поне една от мрежите; 1 = еднакви, "
         "около 0 = не повече от случайното."),
    ("How many Tags are in both networks and what share of each network that is; a low share means the pair is "
     "compared on only a small part of that network."):
        ("Колко тага има в двете мрежи и какъв дял от всяка мрежа са те; нисък дял означава, че двойката набори се "
         "сравнява само върху малка част от тази мрежа."),
    "The games ranked in both Top-N Datasets; shown, never scored.":
        "Игрите с ранг в двата набора Топ-N; показват се, никога не се оценяват.",
    # Fixed sentences
    "found among the partitions of {n} scan seeds; no seed of its own":
        "намерено сред разбиванията от {n} начални числа на сканирането; няма собствено начално число",
    "Include at least two datasets to compare": "Включете поне два набора, за да ги сравните",
    ("These two datasets have no Cluster Match: no Multi-Tag Cluster of one shares a Tag with one of the "
     "other."):
        ("Тези два набора нямат съвпадение на клъстери: нито един многотагов клъстер на единия няма общ таг с "
         "многотагов клъстер на другия."),
    "Click a curve in the diagram to see that Cluster Match.":
        "Щракнете върху крива в диаграмата, за да видите това съвпадение на клъстери.",
    "These two datasets have no games in common, so no game can be in both Clusters.":
        "Тези два набора нямат общи игри, затова нито една игра не може да е в двата клъстера.",
    ("The shared settings changed, so every dataset was resolved again on its pick (or with no run); values set by "
     "hand were dropped."):
        ("Общите настройки се промениха, затова всеки набор беше определен наново по избраната си двойка (или без "
         "изпълнение); ръчно зададените стойности отпаднаха."),
    "The Cluster Comparison uses other shared settings; this cell comes from a different run.":
        "Сравнението на клъстери използва други общи настройки; тази клетка е от друго изпълнение.",
    # Source lines
    "★ Selected Partition at g {g} · s {s} (chosen pair)": "★ Избрано разбиване при g {g} · s {s} (избраната двойка)",
    "Selected Partition at g {g} · s {s}": "Избрано разбиване при g {g} · s {s}",
    "Set by hand: one {algorithm} run, main seed": "Зададено ръчно: едно изпълнение на {algorithm}, основно начално число",
    ("The selected cell's Automatic Parameter Selection run is gone: network defaults, one {algorithm} run, main "
     "seed"):
        ("Изпълнението на автоматичния избор на параметри за избраната клетка вече го няма: стойности по "
         "подразбиране на мрежата, едно изпълнение на {algorithm}, основно начално число"),
    "No qualifying pair in the Automatic Parameter Selection run: network defaults, one {algorithm} run, main seed":
        ("Няма квалифицирана двойка в изпълнението на автоматичния избор на параметри: стойности по подразбиране на "
         "мрежата, едно изпълнение на {algorithm}, основно начално число"),
    "No Automatic Parameter Selection run: network defaults, one {algorithm} run, main seed":
        ("Няма изпълнение на автоматичния избор на параметри: стойности по подразбиране на мрежата, едно изпълнение "
         "на {algorithm}, основно начално число"),
    "Open Parameter Selection": "Отвори избора на параметри",
    "Seed-Noise Floor {floor} · NA {na}": "Праг на шума {floor} · NA {na}",
    # Flags and Tag groups
    "No match: outside {dataset}'s network": "Няма съвпадение: извън мрежата на {dataset}",
    "No match: only One-Tag Clusters in {dataset}": "Няма съвпадение: само еднотагови клъстери в {dataset}",
    "No match above {minimum}": "Няма съвпадение над {minimum}",
    "{n} Tag in One-Tag Clusters of {dataset}": {"one": "{n} таг в еднотагови клъстери на {dataset}",
                                                 "other": "{n} тага в еднотагови клъстери на {dataset}"},
    "{n} not in its network": {"one": "{n} не е в мрежата му", "other": "{n} не са в мрежата му"},
    "in {cluster}": "в {cluster}",
    "One-Tag Cluster in {dataset}": "еднотагов клъстер в {dataset}",
    "not in {dataset}'s network ({n} game, minimum {minimum})": {
        "one": "не е в мрежата на {dataset} ({n} игра, минимум {minimum})",
        "other": "не е в мрежата на {dataset} ({n} игри, минимум {minimum})"},
    "hidden in {dataset} (its defining Tag)": "скрит в {dataset} (определящият му таг)",
    "One-Tag Clusters are not matched: {a} has {n_a}, {b} has {n_b}.":
        "Еднотаговите клъстери не се съпоставят: {a} има {n_a}, {b} има {n_b}.",
    # The match detail
    "{n} shared Tag: {ratio}× the {expected} expected from the Cluster sizes (N = {total} Comparable Tags)": {
        "one": "{n} общ таг: {ratio}× очакваните {expected} според размерите на клъстерите (N = {total} сравними тага)",
        "other": ("{n} общи тага: {ratio}× очакваните {expected} според размерите на клъстерите (N = {total} сравними "
                  "тага)")},
    "Of": "От",
    "games in both datasets:": "игри в двата набора:",
    "in both Clusters,": "в двата клъстера,",
    "only in {a},": "само в {a},",
    "only in {b},": "само в {b},",
    "in neither.": "в нито един.",
    "None of the": "Нито една от",
    "games in both datasets is in both Clusters.": "игри в двата набора не е в двата клъстера.",
    "Show all {n}": "Покажи всички {n}",
}

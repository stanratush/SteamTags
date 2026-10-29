"""Bulgarian: view. Keyed by the English text (see `steamstudy.i18n`); filled by the bulk translation."""

MESSAGES: dict[str, str | dict[str, str]] = {
    # The quality lines and the Removal Sensitivity footer
    "n/a ({status})": "н/д ({status})",
    "Q (γ = {gamma}) n/a: no edges": "Q (γ = {gamma}) н/д: няма ребра",
    "Q (γ = {gamma}) {q} vs null {mean} ± {sd} (excess {excess}, z {z}; null networks average {null_edges} edges vs "
    "{edges})":
        "Q (γ = {gamma}) {q} срещу нулевия модел {mean} ± {sd} (превишение {excess}, z {z}; средният брой ребра в "
        "мрежите на нулевия модел е {null_edges} срещу {edges})",
    "coverage {value}": "покритие {value}",
    "{multi} multi-tag + {one} one-tag": "многотагови: {multi} + еднотагови: {one}",
    "silhouette (Jaccard game-set distance), descriptive diagnostic, not a selection criterion {value}":
        "силует (разстояние на Jaccard между множествата игри), описателна диагностика, не е критерий за избор {value}",
    "{n} disconnected cluster: try Leiden": {"one": "{n} несвързан клъстер: опитайте Leiden",
                                             "other": "{n} несвързани клъстера: опитайте Leiden"},
    "Seed-noise floor (K = {k}): ARI vs. main min {min}, mean {mean} · multi-tag clusters {lo}–{hi} · SD Q {sd_q} · "
    "SD silhouette {sd_sil}":
        "Праг на шума от началното число (K = {k}): ARI спрямо основното разбиване мин. {min}, средно {mean} · "
        "многотагови клъстери {lo}–{hi} · SD на Q {sd_q} · SD на силуета {sd_sil}",
    "{flagged} of {n} tags flagged; if removals acted only like another seed, about {expected} would be flagged on "
    "average (n / (K + 1)). Screening flag, not a significance test.":
        "Отбелязани тагове: {flagged} от {n}; ако премахванията действаха само като още едно начално число, "
        "очакваният среден брой отбелязани би бил около {expected} (n / (K + 1)). Отметка за проверка, не тест за "
        "значимост.",
    "screening flag, not a significance test": "отметка за проверка, не тест за значимост",
    # The summary row and the quality boxes
    "{q} · excess {excess}": "{q} · превишение {excess}",
    "γ = {gamma}; no links, so no Q.": "γ = {gamma}; няма ребра, затова няма Q.",
    "γ = {gamma}; null mean {mean} ± {sd} from R = {r} shuffled networks; excess = Q − null mean.":
        "γ = {gamma}; средно за нулевия модел {mean} ± {sd} от R = {r} разбъркани мрежи; превишение = Q − средното "
        "за нулевия модел.",
    "all other seeds give {n} multi-tag cluster.": {
        "one": "всички други начални числа дават {n} многотагов клъстер.",
        "other": "всички други начални числа дават {n} многотагови клъстера."},
    "other seeds give {lo}–{hi} multi-tag clusters.": "другите начални числа дават {lo}–{hi} многотагови клъстера.",
    "{n} of the dataset's {total} games pass the Minimum Months Filter.":
        "Филтърът за минимум месеци пропуска {n} от {total} игри в набора.",
    "shuffled networks average {n} links.": "средният брой ребра в разбърканите мрежи е {n}.",
    "multi-tag + one-tag": "многотагови + еднотагови",
    "Silhouette": "Силует",
    "{value} · descriptive": "{value} · описателен",
    "SD across seeds {sd}.": "SD между началните числа {sd}.",
    "null mean {mean} ± {sd} from R = {r} shuffled networks":
        "средно за нулевия модел {mean} ± {sd} от R = {r} разбъркани мрежи",
    "no edges": "няма ребра",
    "z {z} · null {mean} ± {sd} · excess over the null mean":
        "z {z} · нулев модел {mean} ± {sd} · превишение над средното за нулевия модел",
    "γ = {gamma}; {null}.": "γ = {gamma}; {null}.",
    "Q {q} − {null}; z {z}.": "Q {q} − {null}; z {z}.",
    "Null-model excess": "Превишение над нулевия модел",
    "Coverage": "Покритие",
    "link weight inside clusters": "тегло на ребрата вътре в клъстерите",
    "SD across the K = {k} seeds {sd}.": "SD между K = {k} начални числа {sd}.",
    "Seed noise": "Шум от началното число",
    "ARI min · mean {mean}": "ARI мин. · средно {mean}",
    "each of the K = {k} extra seeds against the clusters shown; min is the seed that differed most.":
        "всяко от K = {k} допълнителни начални числа спрямо показаните клъстери; мин. е числото, което се различава "
        "най-много.",
    # The tag view
    "Rank": "Ранг",
    "AppID": "AppID",
    "Name": "Име",
    "Show all {n}": "Покажи всички {n}",
    "Tag": "Таг",
    "Select this link": "Избери това ребро",
    "used for clustering": "използва се за клъстеризацията",
    "max {cap} in a {size}-tag cluster; not comparable across cluster sizes":
        "макс. {cap} в клъстер с {size} тага; не е сравнимо между клъстери с различен размер",
    "descriptive": "описателен",
    "Cluster Center": "Център на клъстера",
    "Tag {tag_id} · {cluster} ({n} tag)": {"one": "Таг {tag_id} · {cluster} ({n} таг)",
                                           "other": "Таг {tag_id} · {cluster} ({n} тага)"},
    "{n} game in the network has this tag": {"one": "{n} игра в мрежата има този таг",
                                             "other": "{n} игри в мрежата имат този таг"},
    "Connected tags": "Свързани тагове",
    "{n}, by shared games": "{n}, по общи игри",
    "Metrics": "Метрики",
    "Removal Sensitivity (stale: other settings)": "Чувствителност към премахване (остаряла: други настройки)",
    "Removal Sensitivity": "Чувствителност към премахване",
    "none": "няма",
    "Δ {delta} (after {after})": "Δ {delta} (след {after})",
    # The Inspector's plain names (INSPECTOR_LABELS)
    "Cluster": "Клъстер",
    "Total shared games": "Сума на общите игри",
    "Total lift": "Сума на лифта",
    "Shared games in own cluster": "Общи игри в своя клъстер",
    "Lift in own cluster": "Лифт в своя клъстер",
    "Links · in own cluster": "Ребра · в своя клъстер",
    "Membership Stability": "Стабилност на принадлежността",
    "Prominence in own cluster (z)": "Изпъкване в своя клъстер (z)",
    "Spread across clusters": "Разпръснатост между клъстерите",
    "Fit to own cluster (silhouette)": "Съответствие със своя клъстер (силует)",
    "Mean game-set distance to members": "Средно разстояние по игри до членовете",
    "Center's game-set distance": "Разстояние по игри на центъра",
    "Most-linked member": "Най-свързан член",
    "Center is the most-linked member": "Центърът е най-свързаният член",
    "Mean Membership Stability": "Средна стабилност на принадлежността",
    "Boundary crossing (conductance)": "Пресичане на границата (проводимост)",
    "Agreement after removal (ARI, reclustered)": "Съгласие след премахване (ARI, при нова клъстеризация)",
    "Beyond seed noise": "Над шума от началното число",
    "Change in Q (reclustered)": "Промяна в Q (при нова клъстеризация)",
    "Silhouette after removal (reclustered)": "Силует след премахване (при нова клъстеризация)",
    "Change in multi-tag · one-tag clusters": "Промяна в многотаговите · еднотаговите клъстери",
    "Cluster Centers lost": "Изгубени центрове на клъстери",
    "Change in Q (clusters kept)": "Промяна в Q (запазени клъстери)",
    "Silhouette after removal (clusters kept)": "Силует след премахване (запазени клъстери)",
    # The link view
    "show this pair": "покажи двойката клъстери",
    "Inside {cluster}": "В {cluster}",
    "Between {a} and {b}": "Между {a} и {b}",
    "Games having both tags": "Игри с двата тага",
    # The Cluster view, its Games and its Members
    "Matched": "Съвпадащи",
    "of its tags": "от таговете ѝ",
    "Tags": "Тагове",
    "{matched} / {size}": "{matched} / {size}",
    "{n} game has its tag": {"one": "{n} игра има неговия таг", "other": "{n} игри имат неговия таг"},
    "{n} of {total} games has at least one of its {size} tags": {
        "one": "{n} от {total} игри има поне един от неговите {size} тага",
        "other": "{n} от {total} игри имат поне един от неговите {size} тага"},
    "Games": "Игри",
    "{cluster} · {n} tag": {"one": "{cluster} · {n} таг", "other": "{cluster} · {n} тага"},
    "Multi-Tag Cluster": "Многотагов клъстер",
    "One-Tag Cluster": "Еднотагов клъстер",
    "This Louvain cluster is not a connected group of tags (never split). The Leiden mode avoids such clusters.":
        "Този клъстер на Louvain не е свързана група от тагове (приложението не го разделя). Режимът Leiden избягва "
        "такива клъстери.",
    "none ({status})": "няма ({status})",
    "Members": "Членове",
    "by game-set distance to the others": "по разстояние по игри до останалите",
    # Connections, the pair view and the Connections matrix
    "pool of one-tag clusters": "пул на еднотаговите клъстери",
    "Ratio: 1 = as their total link weight predicts; γ = {gamma} is the most it can reach.":
        "Отношение: 1 = колкото предвижда общото им тегло на ребрата; γ = {gamma} е най-високото, до което може да "
        "стигне.",
    "Partner": "Партньор",
    "Ratio": "Отношение",
    "Links": "Ребра",
    "Total": "Сума",
    "Share": "Дял",
    "Shared games · ratio": "Общи игри · отношение",
    "Select this pair": "Избери тази двойка клъстери",
    "Connections": "Връзки",
    "by Connection Ratio": "по отношението на свързаност",
    "Shared games · ratio: not tied to the clustering; can exceed γ.":
        "Общи игри · отношение: не е обвързано с клъстеризацията; може да надхвърли γ.",
    "Empty: the pool holds isolated tags only, so no link weight is expected.":
        "Празно: пулът съдържа само изолирани тагове, затова не се очаква тегло на ребрата.",
    "Empty: fewer than two pool tags have links, so no link weight is expected between them.":
        "Празно: по-малко от два тага от пула имат ребра, затова между тях не се очаква тегло на ребрата.",
    "Empty: no link weight is expected.": "Празно: не се очаква тегло на ребрата.",
    "of γ = {gamma}": "от γ = {gamma}",
    "Connection Ratio": "Отношение на свързаност",
    "Connection Share of {group}": "Дял на свързаност: {group}",
    "Shared-game total": "Сума на общите игри",
    "Shared-game ratio (not tied to the clustering; can exceed γ)":
        "Отношение по общи игри (не е обвързано с клъстеризацията; може да надхвърли γ)",
    "Tag in {group}": "Таг ({group})",
    "Cluster pair": "Двойка клъстери",
    "Links between them": "Ребра между тях",
    "Connection Ratio {ratio} (γ = {gamma})": "Отношение на свързаност {ratio} (γ = {gamma})",
    "Share {a} → {b}: {share}": "Дял {a} → {b}: {share}",
    "Total {total} · {n} links": "Сума {total} · ребра: {n}",
    "Shared games {total} · ratio {ratio} (not tied to the clustering; can exceed γ)":
        "Общи игри {total} · отношение {ratio} (не е обвързано с клъстеризацията; може да надхвърли γ)",
    "Ratio empty: no link weight is expected (a pool of isolated tags only, or fewer than two linked pool tags).":
        "Отношението е празно: не се очаква тегло на ребрата (пул само от изолирани тагове или по-малко от два "
        "свързани тага в пула).",
    "1 = as their total link weight predicts; γ is the most a ratio can reach.":
        "1 = колкото предвижда общото им тегло на ребрата; γ е най-високото, до което може да стигне отношението.",
    "γ = {gamma}": "γ = {gamma}",
    "Share: each row adds up to 100%.": "Дял: всеки ред дава общо 100%.",
    "Share (row → column)": "Дял (ред → колона)",
    "Matrix": "Матрица",
    "Table": "Таблица",
    "Connections matrix": "Матрица на връзките",
    # Tag search and missing tags
    "{n} game, below {min}": {"one": "{n} игра, под {min}", "other": "{n} игри, под {min}"},
    "removed": "премахнат",
    "defining tag hidden": "скрит определящ таг",
    "Genre Tag hidden": "скрит жанров таг",
    "In the network · {n}": "В мрежата · {n}",
    "{cluster} · {n} game": {"one": "{cluster} · {n} игра", "other": "{cluster} · {n} игри"},
    "Not in the network · {n}": "Извън мрежата · {n}",
    "Tag {tag_id} · not in the network": "Таг {tag_id} · извън мрежата",
    "{n} game of the dataset has this tag.": {"one": "{n} игра от набора има този таг.",
                                              "other": "{n} игри от набора имат този таг."},
    "Unhide": "Покажи отново",
    "Pressing it changes the Network State.": "Натискането променя състоянието на мрежата.",
    "No single control brings this tag back; change the settings listed above.":
        "Нито една отделна настройка не връща този таг; променете настройките, изброени по-горе.",
    # The Network State sentence
    "copied": "копирано",
    "no Genre Tag hidden": "няма скрит жанров таг",
    "Genre Tag {tags} hidden": {"one": "скрит жанров таг {tags}", "other": "скрити жанрови тагове {tags}"},
    "{n} Genre Tag hidden": {"one": "{n} скрит жанров таг", "other": "{n} скрити жанрови тага"},
    "{hidden}, defining tag {tag} hidden": "{hidden}, скрит определящ таг {tag}",
    "removed: {tags}": "премахнати: {tags}",
    "no tag removed": "няма премахнат таг",
    "{dataset} Top {rows}, games with ≥ {months} months observed; tags on ≥ {g} games, links of ≥ {s} shared games; "
    "{hidden}; {removed}; {algorithm} on {weight}, γ {gamma}, seed {seed} · ":
        "{dataset} Топ-{rows}, игри с наблюдавани месеци ≥ {months}; тагове в ≥ {g} игри, ребра с ≥ {s} общи игри; "
        "{hidden}; {removed}; {algorithm} по {weight}, γ {gamma}, начално число {seed} · ",
    "Network State id: click to copy": "Идентификатор на състоянието на мрежата: щракнете, за да го копирате",
    # The Network State table (Analysis Report §1)
    "State key field: {field}": "Поле на ключа на състоянието на мрежата: {field}",
    "tag {tag_id}": "таг {tag_id}",
    "Dataset and Build": "Набор от данни и компилация",
    "{dataset} · Build {build_id}": "{dataset} · компилация {build_id}",
    "Games after the Minimum Months Filter": "Игри след филтъра за минимум месеци",
    "≥ {n} months observed": "наблюдавани месеци ≥ {n}",
    "Hidden tags": "Скрити тагове",
    "Clustering Weight": "Тегло за клъстеризация",
    "Algorithm": "Алгоритъм",
    "Null-model replicates R": "Повторения на нулевия модел R",
    "Noise seeds K": "Начални числа за шума K",
    "Method version": "Версия на метода",
    "derived from dataset and min_months": "изведено от dataset и min_months",
    "Network State": "Състояние на мрежата",
    "Click to copy": "Щракнете, за да копирате",
    "— quote it with every network number.": "— цитирайте го с всяко число за мрежата.",
    "Show JSON": "Покажи JSON",
}

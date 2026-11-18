"""Bulgarian: ps_view. Keyed by the English text (see `steamstudy.i18n`); filled by the bulk translation."""

MESSAGES: dict[str, str | dict[str, str]] = {
    # The metric picker and the reason letters
    "Neighbour Agreement": "Съгласие със съседите",
    "Information Retention": "Запазване на информацията",
    "isolated share": "дял на изолираните тагове",
    "Multi-Tag Clusters": "Многотагови клъстери",
    "Seed-Noise Floor": "Праг на шума от началното число",
    "no Selected Partition": "няма избрано разбиване",
    "no Neighbour Agreement": "няма съгласие със съседите",
    "too few comparable neighbours": "твърде малко сравними съседи",
    "Information Retention below the minimum": "запазване на информацията под минимума",
    "isolated share above the maximum": "дял на изолираните тагове над максимума",
    "LCC share below the minimum": "дял на LCC под минимума",
    "too many Multi-Tag Clusters": "твърде много многотагови клъстери",
    # Pair Constraints
    "Minimum Information Retention": "Минимално запазване на информацията",
    "Maximum isolated share": "Максимален дял на изолираните тагове",
    "Minimum LCC share": "Минимален дял на LCC",
    "Minimum comparable neighbours (different graph)": "Минимум сравними съседи (с различен граф)",
    "Maximum Multi-Tag Clusters (empty = off)": "Максимум многотагови клъстери (празно = изключено)",
    "Tolerance (near-best)": "Допуск (почти най-добри)",
    "default {value}": "по подразбиране {value}",
    "off": "изключено",
    "Pair Constraints": "Ограничения за двойката",
    "Retention ≥": "Запазване ≥",
    "Isolated share ≤": "Дял изолирани ≤",
    "LCC share ≥": "Дял на LCC ≥",
    "Comparable neighbours ≥": "Сравними съседи ≥",
    "Multi-Tag Clusters ≤": "Многотагови клъстери ≤",
    "Tolerance": "Допуск",
    "All five datasets": "Всичките пет набора",
    "this dataset only": "само този набор",
    "Confirm": "Потвърди",
    "Reset to defaults": "Върни стойностите по подразбиране",
    # Provenance
    "{lib} {old} (installed {new})": "{lib} {old} (инсталирано: {new})",
    "These Parameter Selection results were computed with {names}; the numbers may differ here. Clear app cache and "
    "Run to recompute here.":
        "Тези резултати от избора на параметри са изчислени с {names}; тук числата може да се различават. Изчистете "
        "кеша на приложението и натиснете „Изпълни“, за да ги изчислите отново тук.",
    "Computed when this bundle was made: Python {python}, {system} {machine}, {day}":
        "Изчислено при създаването на този пакет: Python {python}, {system} {machine}, {day}",
    # Run and the pills
    "running": "изпълнява се",
    "{n} of {total} done": "готови {n} от {total}",
    "not run": "не е изпълнено",
    "custom": "персонализирани",
    "default": "по подразбиране",
    "Run all datasets": "Изпълни за всички набори",
    "Export tables": "Експортирай таблиците",
    "validation {done} of {total} replicates": "валидиране: повторения {done} от {total}",
    "grid {done} of {total} pairs": "решетка: двойки {done} от {total}",
    "grid done, validated": "решетката е готова, валидирано",
    "grid done, not validated": "решетката е готова, не е валидирано",
    # Selection settings
    "hide each dataset's defining tag ({tags})": "скрий определящия таг на всеки набор ({tags})",
    "hide each dataset's defining tag": "скрий определящия таг на всеки набор",
    "Selection settings": "Настройки на избора",
    "no removed tags": "няма премахнати тагове",
    "Minimum Multi-Tag Clusters": "Минимум многотагови клъстери",
    "Use these settings": "Използвай тези настройки",
    "Copy from Workbench": "Копирай от работното място",
    "Parameter Grid: g {g_lo}–{g_hi}, s {s_lo}–{s_hi}, s ≤ g ({n} pairs)":
        "Решетка на параметрите: g {g_lo}–{g_hi}, s {s_lo}–{s_hi}, s ≤ g (двойки прагове: {n})",
    "γ from 0 to γ_max(n_e) in steps of {step}; {seeds} scan seeds":
        "γ от 0 до γ_max(n_e) със стъпка {step}; начални числа за сканирането: {seeds}",
    "Null Comparison R = {r}; Subsample Stability S = {s}":
        "Сравнение с нулев модел R = {r}; стабилност при подизвадки S = {s}",
    # The dataset strip and the loading panel
    "no qualifying pair": "няма квалифицирана двойка",
    "★ {g}·{s} NA {na}": "★ {g}·{s} NA {na}",
    "grid {done} of {total}": "решетка: {done} от {total}",
    "up to several hundred": "до няколкостотин",
    "Searching {pairs} Threshold Pairs × {scan} resolutions × {seeds} seeds for each dataset, then checking the "
    "chosen pair against {replicates} shuffled networks and {subsamples} subsamples.":
        "За всеки набор се търси в двойки прагове ({pairs}) × резолюции ({scan}) × начални числа ({seeds}), после "
        "избраната двойка се проверява срещу разбъркани мрежи ({replicates}) и подизвадки ({subsamples}).",
    "Starting…": "Стартиране…",
    "Dataset {index} of {n} ({dataset}): grid {done} of {total} pairs.":
        "Набор {index} от {n} ({dataset}): решетка, двойки {done} от {total}.",
    "Dataset {index} of {n} ({dataset}): validation {done} of {total} replicates.":
        "Набор {index} от {n} ({dataset}): валидиране, повторения {done} от {total}.",
    "A one-off: results are cached. Cancel keeps the finished pairs and Continue resumes; a cancelled validation "
    "restarts from the beginning.":
        "Еднократно: резултатите се кешират. „Отказ“ запазва готовите двойки, а „Продължи“ продължава оттам; "
        "прекъснато валидиране започва отначало.",
    "Computing Parameter Selection": "Изчисляване на избора на параметри",
    "How Automatic Parameter Selection works": "Как работи автоматичният избор на параметри",
    "Loading Parameter Selection…": "Зареждане на избора на параметри…",
    # The heatmap
    "g={g}, s={s}: pending": "g={g}, s={s}: предстои",
    "✓ qualifies": "✓ квалифицира се",
    "selection after the whole grid": "изборът е след цялата решетка",
    "g={g}, s={s}<br>{metric}: {value}<br>NA: {na}<br>tags: {tags}<br>Multi-Tag Clusters: {clusters}<br>{verdict}":
        "g={g}, s={s}<br>{metric}: {value}<br>NA: {na}<br>тагове: {tags}<br>многотагови клъстери: "
        "{clusters}<br>{verdict}",
    "s (minimum shared games)": "s (минимум общи игри)",
    "g (minimum games per tag)": "g (минимум игри на таг)",
    "★ chosen · orange outline: near-best · dark outline: inspected · ":
        "★ избрана · оранжева рамка: почти най-добра · тъмна рамка: разглеждана · ",
    # "Why this pair" and the validation card
    "Constraint": "Ограничение",
    "alone": "самостоятелно",
    "cumulative": "натрупано",
    "Why this pair": "Защо тази двойка",
    "Arm": "Вариант",
    "re-selected": "при нов избор",
    "at resolution": "при резолюцията",
    "Not validated. Validate this pair in the Pair Inspector runs its validation.":
        "Не е валидирано. „Валидирай тази двойка“ в инспектора на двойката стартира валидирането.",
    "This pair has no Selected Partition, so it cannot be validated.":
        "Тази двойка няма избрано разбиване, затова не може да бъде валидирана.",
    "This is the pair you selected; the pair chosen under the default constraints is g = {g}, s = {s}.":
        "Това е избраната от вас двойка; двойката, избрана при ограниченията по подразбиране, е g = {g}, s = {s}.",
    # The validation card's Cluster list (interval plot) and its expanded rows
    "Share of subsamples with Hennig's Jaccard ≤ 0.5, with its 95% Wilson interval. R = re-selected, A = at "
    "resolution.":
        "Дял на подизвадките с индекс на Jaccard по Hennig ≤ 0,5, с неговия 95% интервал на Wilson. R = при нов "
        "избор, A = при резолюцията.",
    "Click a row for every figure.": "Щракнете върху ред, за да видите всички стойности.",
    "Cluster": "Клъстер",
    "Size": "Размер",
    "Status": "Статус",
    "≤ 0.5: 0 — ½ — 1": "≤ 0,5: 0 — ½ — 1",
    "Clusters of 2–3 tags can take only a few Jaccard values, and they drop sharply when they lose or move one tag.":
        "Клъстерите от 2–3 тага могат да приемат само няколко стойности на индекса и рязко падат, когато загубят или "
        "преместят един таг.",
    "Hennig's J": "Jaccard (Hennig)",
    "mean ± s.e.; 10th–90th pct": "средно ± ст. гр.; перс. 10–90",
    "≤ 0.5 in": "≤ 0,5 в",
    "> 0.75 in": "> 0,75 в",
    "k of B*; 95% Wilson": "k от B*; 95% Wilson",
    "Whole-Cluster J": "Jaccard (цял клъстер)",
    "mean ± s.e.": "средно ± ст. гр.",
    "{k} of {n}": "{k} от {n}",
    "Dissolved in most subsamples": "Разпаднат в повечето подизвадки",
    "borderline": "на границата",
    "Not assessable": "Не може да се оцени",
    "rarely assessable ({b} of {s})": "рядко оценим ({b} от {s})",
    "No pair qualifies under the default constraints, so nothing was validated automatically. Validate this pair is "
    "offered on any inspected pair.":
        "При ограниченията по подразбиране не се квалифицира нито една двойка, затова нищо не е валидирано "
        "автоматично. „Валидирай тази двойка“ се предлага за всяка разглеждана двойка.",
    "Three kinds of stability": "Три вида стабилност",
    "Null Comparison": "Сравнение с нулев модел",
    "Subsample Stability": "Стабилност при подизвадки",
    # The Pair Inspector
    "No edges: no scan": "Няма ребра: няма сканиране",
    "envelope": "обвивка",
    "status": "статус",
    "tag overlap": "припокриване на таговете",
    "Edge Overlap": "Припокриване на ребрата",
    "identical graph": "идентичен граф",
    "No Selected Partition: {reason}": "Няма избрано разбиване: {reason}",
    "main seed": "основното начално число",
    "scan seed {seed}": "начално число от сканирането {seed}",
    "Workbench γ {gamma}, {seed}: reproduces the Selected Partition ✓":
        "γ {gamma} в работното място, {seed}: възпроизвежда избраното разбиване ✓",
    "Workbench γ {gamma}, main seed: {flag}, shows a different partition (ARI {ari})":
        "γ {gamma} в работното място, основното начално число: {flag}, показва различно разбиване (ARI {ari})",
    "Click a computed cell to inspect its pair.": "Щракнете върху изчислена клетка, за да разгледате двойката ѝ.",
    "{value} over {n} different-graph neighbour; {identical} identical, {missing} missing": {
        "one": "{value} при {n} съсед с различен граф; идентични: {identical}, липсващи: {missing}",
        "other": "{value} при {n} съседа с различен граф; идентични: {identical}, липсващи: {missing}"},
    "LCC share": "дял на LCC",
    "Multi-Tag / One-Tag Clusters": "Многотагови / еднотагови клъстери",
    "{multi} / {isolated} isolated + {connected} connected": "{multi} / изолирани: {isolated} + свързани: {connected}",
    "min {floor}, mean {mean}, exact {exact} of {runs}": "мин. {floor}, средно {mean}, точно: {exact} от {runs}",
    "hits": "попадения",
    "{hits} of {runs} runs": "{hits} от {runs} изпълнения",
    "domain": "област на оптималност",
    "Selected Resolution": "Избрана резолюция",
    "scan range": "обхват на сканирането",
    "no scan": "няма сканиране",
    "0 to {end} (n_e = {n_e}, {n} values)": "от 0 до {end} (n_e = {n_e}, стойности: {n})",
    "Remove (stage in Selection settings)": "Премахни (отбелязва се в настройките на избора)",
    "Not validated": "Не е валидирано",
    "Q not above the null ({k} of {d})": "Q не е над нулевия модел ({k} от {d})",
    "Q above all {d} shuffled networks": "Q е над всички {d} разбъркани мрежи",
    "Null Q undefined": "Q на нулевия модел е неопределено",
    "Dissolved in most subsamples (re-selected): {n}": "Разпаднати в повечето подизвадки (при нов избор): {n}",
    "Open the validation card": "Отвори картата за валидиране",
    "median ARI re-selected {reselected}, at resolution {at}":
        "медиана на ARI при нов избор {reselected}, при резолюцията {at}",
    "{dataset}: g = {g}, s = {s}": "{dataset}: g = {g}, s = {s}",
    "Neighbour links": "Сравнения със съседите",
    "Validation": "Валидиране",
    "Pair Inspector": "Инспектор на двойката",
    "Apply to Workbench": "Приложи в работното място",
    "Validate this pair": "Валидирай тази двойка",
    "Use in Cluster Comparison": "Използвай в сравнението на клъстери",
}

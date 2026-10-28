"""Bulgarian: callbacks. Keyed by the English text (see `steamstudy.i18n`); filled by the bulk translation."""

MESSAGES: dict[str, str | dict[str, str]] = {
    # The legend, the banners and the state text
    "Key": "Легенда",
    "Select this cluster": "Избери този клъстер",
    "{n} one-tag": {"one": "{n} еднотагов", "other": "{n} еднотагови"},
    "mode: test — this Build comes from a test Snapshot; never publish it.":
        "mode: test — тази компилация идва от тестова моментна снимка; никога не я публикувайте.",
    "{lib} {then} (Build) vs {now} (installed)": "{lib} {then} (компилация) срещу {now} (инсталирана)",
    "Library versions differ from the ones this Build was made with, so numbers may differ from the Build's: {drift}.":
        "Версиите на библиотеките се различават от тези, с които е направена компилацията, затова числата може да се "
        "различават от нейните: {drift}.",
    "parse_errors_allowed — this Build was made with --allow-parse-errors ({n} errors); never publish it.":
        "parse_errors_allowed — тази компилация е направена с --allow-parse-errors (грешки: {n}); никога не я "
        "публикувайте.",
    "Minimum games per tag {g}, minimum shared games {s}, Minimum Months Filter {m}.":
        "Минимум игри на таг {g}, минимум общи игри {s}, филтър за минимум месеци {m}.",
    "{n} tag of the dataset is not in the network; it is listed below with all its reasons.": {
        "one": "{n} таг от набора не е в мрежата; той е изброен по-долу с всичките си причини.",
        "other": "{n} тага от набора не са в мрежата; всеки от тях е изброен по-долу с всичките си причини."},
    "Estimate: {n} tags × {ms} ms (one clustering) ≈ {s} s, plus about 4 s job start-up":
        "Оценка: {n} тага × {ms} ms (една клъстеризация) ≈ {s} s, плюс около 4 s за стартиране на задачата",
    "Export": "Експорт",
    ": steamstudy_{dataset}_{state_id}_<UTC timestamp>.zip, with every table above, export.json with the full state "
    "key and provenance, and Removal Sensitivity results for this exact state if any.":
        ": steamstudy_{dataset}_{state_id}_<UTC timestamp>.zip, с всяка таблица по-горе, export.json с пълния ключ на "
        "състоянието на мрежата и произхода му и резултатите от чувствителността към премахване за точно това "
        "състояние на мрежата, ако има такива.",
    "Opened state {expected}: recomputed state_id {state_id} {mark}":
        "Отворено състояние на мрежата {expected}: преизчислен state_id {state_id} {mark}",
    "Applied from Parameter Selection: {dataset}, g={g}, s={s} — Selected Partition reproduced ✓":
        "Приложено от „Избор на параметри“: {dataset}, g={g}, s={s} — избраното разбиване е възпроизведено ✓",
    "Applied from Parameter Selection: {dataset}, g={g}, s={s} — shows a different partition from the Selected "
    "Partition: ARI {ari}":
        "Приложено от „Избор на параметри“: {dataset}, g={g}, s={s} — показва разбиване, различно от избраното: "
        "ARI {ari}",
    # The Inspector
    "Click a node, an edge or a cluster (legend or Clusters table) to inspect it.":
        "Щракнете върху възел, ребро или клъстер (в легендата или в таблицата „Клъстери“), за да го разгледате.",
    "This tag is not in the current network.": "Този таг не е в текущата мрежа.",
    "This edge is not in the current network.": "Това ребро не е в текущата мрежа.",
    "This pair is not in the current partition.": "Тази двойка клъстери не е в текущото разбиване.",
    "This cluster is not in the current partition.": "Този клъстер не е в текущото разбиване.",
    # Removal Sensitivity
    "starting…": "стартиране…",
    "{done} of {total}": "{done} от {total}",
    "Compare each agreement after removal with the Seed-Noise Floor: ARI min {ari} over K = {k} noise seeds (all its "
    "numbers are in Cluster quality).":
        "Сравнете всяко съгласие след премахване с прага на шума от началното число: ARI мин. {ari} при K = {k} "
        "начални числа за шума (всичките му числа са в „Качество на клъстерите“).",
    "Stale: these results belong to other settings. Run again for the current state.":
        "Остарели: тези резултати са за други настройки. Изпълнете отново за текущото състояние на мрежата.",
    "Loaded from export (not rerun).": "Заредени от експорт (не са изпълнени отново).",
    "Partial result: {done} of {total} tags.": "Частичен резултат: тагове {done} от {total}.",
    "Not run for this state.": "Не е изпълнено за това състояние на мрежата.",
    "Continue ({done} of {total} done)": "Продължи (готови {done} от {total})",
    # Open Network State and the app cache
    "Refused: {reason}.": "Отказано: {reason}.",
    "Refused: {reason}": "Отказано: {reason}",
    "Opened {filename}: Build {build_id}, state {state_id} (schema_version {version}).":
        "Отворен е {filename}: компилация {build_id}, състояние на мрежата {state_id} (schema_version {version}).",
    "Cleared {rs} and {ps}.": "Изчистени: {rs} и {ps}.",
    "{n} cached Removal Sensitivity result": {
        "one": "{n} кеширан резултат от чувствителност към премахване",
        "other": "{n} кеширани резултата от чувствителност към премахване"},
    "{n} Parameter Selection result": {"one": "{n} резултат от избор на параметри",
                                       "other": "{n} резултата от избор на параметри"},
    # Parameter Selection
    "Results from the app cache: Build {build_id}, settings key {key}, method v{version}":
        "Резултати от кеша на приложението: компилация {build_id}, ключ на настройките на избора {key}, метод v{version}",
    "No results for these settings on this computer yet.": "Все още няма резултати за тези настройки на този компютър.",
    "Continue ({done} of {total} pairs)": "Продължи (двойки прагове: {done} от {total})",
    "Run {dataset}": "Изпълни {dataset}",
    "changed": "променено",
    "Unconfirmed changes": "Непотвърдени промени",
}

"""Bulgarian: the Build menu, the draft dialog, the Eligible Pool preview and Import data… (issues 28-33).

Terms (docs/i18n/bg-terms.md): Build = компилация, Snapshot = моментна снимка, Build Draft = чернова на компилация,
Import = импорт, List Size = размер на списъка, Tag Depth = дълбочина на таговете, raw / lightweight Snapshot =
сурова / олекотена моментна снимка.
"""

MESSAGES: dict[str, str | dict[str, str]] = {
    # the menu and its tree
    "Builds: switch, make and manage": "Компилации: превключване, създаване и управление",
    "✓ open in this tab": "✓ отворена в този раздел",
    "latest": "последна",
    "test": "тестова",
    "from a deleted Build": "от изтрита компилация",
    "from {name} (not in this Bundle)": "от {name} (не е в този пакет)",
    "Duplicate": "Дублирай",
    "Delete": "Изтрий",
    "Discard": "Откажи",
    "{size} (app cache {cache})": "{size} (кеш на приложението {cache})",
    "running {pct}%": "изпълнява се {pct}%",
    "waiting": "чака",
    "failed": "неуспешна",
    "draft": "чернова",
    "last saved {when}": "последно запазена {when}",
    "Import": "Импорт",
    "Snapshot": "Моментна снимка",
    "raw": "сурова",
    "lightweight": "олекотена",
    "Import defaults": "Стойности по подразбиране за импорт",
    "start a draft from the defaults": "започни чернова от стойностите по подразбиране",
    "Duplicate the open Build": "Дублирай отворената компилация",
    "Import data…": "Импортирай данни…",
    "Manage Builds…": "Управление на компилациите…",
    "Duplicate {name}": "Дублиране на {name}",
    "The new draft starts from this Build's settings, with this Build as its parent.":
        "Новата чернова започва от настройките на тази компилация, която става неин родител.",
    "Snapshot or Import to build from": "Моментна снимка или импорт, от които да се компилира",
    "This tab shows this Build: switch to another Build first.":
        "Този раздел показва тази компилация: първо превключете към друга компилация.",
    "the {where} latest pointer moves to {to}": "указателят latest на {where} се премества към {to}",
    "root": "корена",
    "nothing (it is removed)": "нищо (премахва се)",
    "{n} Builds and {m} drafts lose their parent and move to the root":
        "{n} компилации и {m} чернови губят родителя си и се преместват в корена",
    "Bundles naming it: {names}": "Пакети, които я назовават: {names}",
    "Delete {name}?": "Да се изтрие ли {name}?",
    "This deletes the Build folder {ref} ({size}, of which app cache {cache}). It cannot be undone.":
        "Това изтрива папката на компилацията {ref} ({size}, от които кеш на приложението {cache}). "
        "Действието е необратимо.",
    "Other tabs on this Build will show that it no longer exists.":
        "Другите раздели с тази компилация ще покажат, че тя вече не съществува.",
    "Delete the Build": "Изтрий компилацията",
    "Manage Builds": "Управление на компилациите",
    "Every Build with its folder size and app-cache size.":
        "Всяка компилация с размера на папката и на кеша на приложението.",
    # Import data…
    "Import data": "Импортиране на данни",
    "One wide UTF-8 CSV: id, name, attributes (separated by ;), optional score, any numeric columns. Making an "
    "Import is separate from making its first Build.":
        "Един широк CSV файл в UTF-8: id, name, attributes (разделени с ;), по избор score и числови колони. "
        "Създаването на импорт е отделно от създаването на първата му компилация.",
    "Choose the CSV file…": "Изберете CSV файла…",
    "Optional: attributes.csv (id, name)…": "По избор: attributes.csv (id, name)…",
    "Filter column": "Колона за филтриране",
    "Refused: the same file is already Import {import_id}.": "Отказано: същият файл вече е импорт {import_id}.",
    "File": "Файл",
    "Row": "Ред",
    "Column": "Колона",
    "Code": "Код",
    "Value": "Стойност",
    "Message": "Съобщение",
    "Refused: {n} problems. Every one is listed in {path}.": "Отказано: {n} проблема. Всички са изброени в {path}.",
    "Made Import {import_id}. Its Import defaults row in the tree starts a draft.":
        "Създаден е импорт {import_id}. Редът му със стойности по подразбиране в дървото започва чернова.",
    # the Build run strip
    "Building {name}: {stage}, {s} s of about {est} s": "Компилира се {name}: {stage}, {s} s от около {est} s",
    "starting": "стартиране",
    "{name} waits for the Build before it": "{name} чака предходната компилация",
    "Built {name}.": "{name} е компилирана.",
    "Open it in this tab": "Отвори я в този раздел",
    "The Build of {name} failed: {error}": "Компилирането на {name} е неуспешно: {error}",
    "The Build of {name} was cancelled.": "Компилирането на {name} е отменено.",
    "Open the draft": "Отвори черновата",
    # the draft dialog
    "Start": "Начало",
    "Changes the Top-N": "Промени в Топ-N",
    "Curation": "Курация",
    "Reports and analysis": "Отчети и анализ",
    "Network defaults": "Мрежа по подразбиране",
    "Review": "Преглед",
    "The draft needs a name": "Черновата се нуждае от име",
    "The draft needs a description (it becomes its changelog entry)":
        "Черновата се нуждае от описание (то става записът ѝ в дневника на промените)",
    "The Parameter Grid has no pairs: s starts above the largest g":
        "Мрежата от параметри няма двойки: s започва над най-голямото g",
    "Manual Exclusions": "Ръчни изключвания",
    "App types": "Типове приложения",
    "No tags": "Без тагове",
    "Exclusion Overrides": "Отмени на изключвания",
    "the defaults": "стойностите по подразбиране",
    "a deleted Build ({ref})": "изтрита компилация ({ref})",
    "Import {id}": "Импорт {id}",
    "Snapshot {id}": "Моментна снимка {id}",
    "Description (required: it becomes the Build's changelog entry)":
        "Описание (задължително: става записът на компилацията в дневника на промените)",
    "Started from": "Започната от",
    "Builds from": "Компилира се от",
    "This Snapshot has only its raw form: the Eligible Pool is not previewed and a Build takes about 99 s. A "
    "lightweight form makes both fast.":
        "Тази моментна снимка има само сурова форма: допустимият набор не се преглежда предварително и "
        "компилирането отнема около 99 s. Олекотената форма ускорява и двете.",
    "Make lightweight Snapshot": "Създай олекотена моментна снимка",
    "The last Build run failed: {n} pages did not parse; they are listed in {path}.":
        "Последното компилиране е неуспешно: {n} страници не бяха разчетени; изброени са в {path}.",
    "The last Build run failed: {error}": "Последното компилиране е неуспешно: {error}",
    "(none)": "(няма)",
    "an attribute": "атрибут",
    "a Steam tag": "таг в Steam",
    "Remove this dataset": "Премахни този набор",
    "Dataset key": "Ключ на набора",
    "Label": "Етикет",
    "Defining tag": "Определящ таг",
    "List Size": "Размер на списъка",
    "Eligible Pool": "Допустим набор",
    "Datasets": "Набори от данни",
    "Add a dataset": "Добави набор",
    "Tags per game (Tag Depth)": "Тагове на игра (дълбочина на таговете)",
    "all": "всички",
    "Global rank limit": "Общ лимит на ранга",
    "Exclusion rules": "Правила за изключване",
    "The fixed rules run first ({before}), then the named rules below in order, then {after}. Edit the named rules "
    "([[rule]]) and Content Flags ([[content_flag]]) here.":
        "Първо се прилагат фиксираните правила ({before}), след това поименните правила по-долу по ред, а накрая "
        "{after}. Тук се редактират поименните правила ([[rule]]) и флаговете за съдържание ([[content_flag]]).",
    "Each entry needs a reason and evidence, as in config/. The would-be Overall ranks of excluded games are on "
    "Review.":
        "Всеки запис изисква причина и доказателство, както в config/. Рангът в Overall, който изключените игри "
        "биха имали, е в Преглед.",
    "Build Draft: {name}": "Чернова на компилация: {name}",
    "Saved automatically; Close keeps the draft.": "Запазва се автоматично; Затвори запазва черновата.",
    "Previewing…": "Предварителен преглед…",
    "Close": "Затвори",
    "{file}.toml does not parse; its last saved value is kept":
        "{file}.toml не може да се разчете; запазва се последната записана стойност",
    "(removed)": "(премахнато)",
    "Top-N": "Топ-N",
    "Changed settings": "Променени настройки",
    "No setting changed.": "Няма променени настройки.",
    " (made with other software versions)": " (създадена с други версии на софтуера)",
    "Identical settings to the Build {name}{note}. Building again is allowed.":
        "Настройките са идентични с компилацията {name}{note}. Повторното компилиране е разрешено.",
    "Problems to fix": "Проблеми за отстраняване",
    "Go to {step}": "Към {step}",
    "Build": "Компилирай",
    "Building…": "Компилира се…",
    # the Eligible Pool preview and the grid warnings
    "Not previewed": "Без предварителен преглед",
    "{n} eligible": "{n} допустими",
    "Eligible Pools": "Допустими набори",
    "Not previewed: this Snapshot has no lightweight form. The Build checks each List Size itself (about 99 s from "
    "raw).":
        "Без предварителен преглед: тази моментна снимка няма олекотена форма. Компилацията сама проверява всеки "
        "размер на списъка (около 99 s от суровата форма).",
    "— Cannot preview: {reason}": "— Не може да се прегледа предварително: {reason}",
    "{key}: {n} eligible, List Size {size}": "{key}: {n} допустими, размер на списъка {size}",
    "Compared with {name}: {a} games enter Overall and {b} leave it.":
        "Спрямо {name}: {a} игри влизат в Overall и {b} излизат от него.",
    "Enter: ": "Влизат: ",
    "Leave: ": "Излизат: ",
    "Excluded games that would rank in Overall": "Изключени игри, които биха се класирали в Overall",
    "Rule": "Правило",
    "To keep one, add an Exclusion Override for its rule on Curation.":
        "За да запазите някоя, добавете отмяна на изключване за правилото ѝ в Курация.",
    "{dataset} (N = {n}): the Parameter Grid's largest g ({g}) is above N.":
        "{dataset} (N = {n}): най-голямото g в мрежата от параметри ({g}) е над N.",
    "{dataset} (N = {n}): the default {name} ({value}) is above N.":
        "{dataset} (N = {n}): стойността по подразбиране на {name} ({value}) е над N.",
    "{dataset} (N = {n}): min_support ({value}) is above N.": "{dataset} (N = {n}): min_support ({value}) е над N.",
    # Import error and warning codes (imports.ERROR_CODES, WARNING_CODES)
    "The file is not UTF-8 text: save it as CSV UTF-8.": "Файлът не е текст в UTF-8: запишете го като CSV UTF-8.",
    "The columns are not separated by commas: save it as CSV UTF-8.":
        "Колоните не са разделени със запетаи: запишете файла като CSV UTF-8.",
    "The file is not valid CSV (a quote is not closed, or a stray quote).":
        "Файлът не е валиден CSV (незатворени или излишни кавички).",
    "The file has no header row.": "Файлът няма заглавен ред.",
    "A required column is missing.": "Липсва задължителна колона.",
    "A column name appears twice in the header.": "Име на колона се среща два пъти в заглавния ред.",
    "The filter column is not a numeric column of the file.": "Колоната за филтриране не е числова колона на файла.",
    "The row has a different number of cells from the header.": "Редът има различен брой клетки от заглавния ред.",
    "The id is not a positive whole number.": "Идентификаторът не е положително цяло число.",
    "Another item already has this id.": "Друг елемент вече има този идентификатор.",
    "The name is empty.": "Името е празно.",
    "The item has no attributes.": "Елементът няма атрибути.",
    "An attribute between two ';' is empty.": "Атрибут между два знака ';' е празен.",
    "The item lists the same attribute twice.": "Елементът изброява един и същ атрибут два пъти.",
    "The score is empty or not a finite number.": "Резултатът (score) е празен или не е крайно число.",
    "The filter value is empty or not a finite number.": "Стойността за филтриране е празна или не е крайно число.",
    "The value is not a finite number (leave the cell empty for none).":
        "Стойността не е крайно число (оставете клетката празна, ако няма стойност).",
    "attributes.csv must have exactly the columns id,name.": "attributes.csv трябва да има точно колоните id,name.",
    "The attribute id is not a positive whole number.": "Идентификаторът на атрибута не е положително цяло число.",
    "Another attribute already has this id.": "Друг атрибут вече има този идентификатор.",
    "Another attribute already has this name.": "Друг атрибут вече има това име.",
    "The attribute name is empty.": "Името на атрибута е празно.",
    "An attribute used by the items is not in attributes.csv.": "Атрибут, използван от елементите, липсва в attributes.csv.",
    "An Import needs at least 10 items.": "Импортът изисква поне 10 елемента.",
    "Attribute names that differ only by case are different attributes.":
        "Имена на атрибути, които се различават само по главни и малки букви, са различни атрибути.",
    "Two items have the same name.": "Два елемента имат едно и също име.",
    "A row of attributes.csv is not used by any item; it is dropped.":
        "Ред от attributes.csv не се използва от нито един елемент; пропуска се.",
    "More than 50,000 items: Builds will be slow.": "Повече от 50 000 елемента: компилациите ще са бавни.",
    "More than 5,000 distinct attributes: Builds will be slow.":
        "Повече от 5000 различни атрибута: компилациите ще са бавни.",
}

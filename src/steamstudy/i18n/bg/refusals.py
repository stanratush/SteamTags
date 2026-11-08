"""Bulgarian: refusals. Keyed by the English text (see `steamstudy.i18n`); filled by the bulk translation."""

MESSAGES: dict[str, str | dict[str, str]] = {
    "not a readable zip: {error}": "не е четим zip файл: {error}",
    "the zip has no export.json": "zip файлът няма export.json",
    "neither an export zip nor an export.json": "нито експортен zip файл, нито export.json",
    "the Build {build_id} at {path} differs from the one this Network State was exported from (its build.json "
    "changed)":
        "компилацията {build_id} в {path} се различава от тази, от която е експортирано това състояние на мрежата "
        "(нейният build.json е променен)",
    "export.json lacks {field}": "в export.json липсва {field}",
    "key_version {found} differs from this software's {expected}: the methods changed, so the state cannot be "
    "reproduced exactly":
        "key_version {found} се различава от {expected} на този софтуер: методите са променени, затова състоянието на "
        "мрежата не може да се възпроизведе точно",
    "the state key cannot be read: {error}": "ключът на състоянието на мрежата не може да се прочете: {error}",
    "this Network State needs Build {build_id} (Snapshot {snapshot_id}), which is not among the Builds in {root}; "
    "copy that Build folder there and open again":
        "това състояние на мрежата изисква компилация {build_id} (моментна снимка {snapshot_id}), която не е сред "
        "компилациите в {root}; копирайте папката на тази компилация там и отворете отново",
    "this Network State needs Build {build_id} (Import {import_id}), which is not among the Builds in {root}; "
    "copy that Build folder there and open again":
        "това състояние на мрежата изисква компилация {build_id} (импорт {import_id}), която не е сред "
        "компилациите в {root}; копирайте папката на тази компилация там и отворете отново",
}

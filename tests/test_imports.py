"""Issue 25: Imports, one wide UTF-8 CSV validated all-or-nothing and stored fixed in imports/<import_id>/."""

from __future__ import annotations

import csv
import datetime as dt
import io
import json
from pathlib import Path

import pytest

from steamstudy import imports as I

NOW = dt.datetime(2026, 11, 8, 9, 30, 0, tzinfo=dt.UTC)
LATER = dt.datetime(2026, 11, 8, 9, 31, 0, tzinfo=dt.UTC)


def _rows(n: int = 12, *, score: bool = True, extra: str = "") -> str:
    head = "id,name,attributes" + (",score" if score else "") + (f",{extra}" if extra else "")
    lines = [head]
    for i in range(1, n + 1):
        cells = [str(i), f"Item {i}", "Zeta;alpha;Beta" if i % 2 else "alpha;Gamma"]
        if score:
            cells.append(str(100 - i * (1 if i != 3 else 0)))  # item 3 scores 100, tying nobody
        if extra:
            cells.append(str(i * 1.5))
        lines.append(",".join(cells))
    return "\n".join(lines) + "\n"


def _write(tmp_path: Path, text: str | bytes, name: str = "games.csv") -> Path:
    path = tmp_path / name
    path.write_bytes(text.encode("utf-8") if isinstance(text, str) else text)
    return path


def _codes(result: I.Validation) -> tuple[set[str], set[str]]:
    return {e.code for e in result.errors}, {w.code for w in result.warnings}


# ----------------------------------------------------------------------------- one case per code

BASE = _rows()
_HEAD = "id,name,attributes,score\n"
_TEN = "".join(f"{i},Item {i},a;b,{i}\n" for i in range(2, 12))  # ten good rows after the case's own

ERROR_CASES = {
    "not_csv_utf8": "id,name,attributes\n1,Caf\xe9,a\n".encode("latin-1"),
    "not_comma_delimited": "id;name;attributes\n" + "".join(f"{i};Item {i};a\n" for i in range(1, 12)),
    "bad_csv": _HEAD + '1,"Item 1,a,1\n' + _TEN,
    "missing_column": "id,name,score\n" + "".join(f"{i},Item {i},{i}\n" for i in range(1, 12)),
    "duplicate_column": "id,name,attributes,score,score\n" + "".join(f"{i},Item {i},a,{i},{i}\n" for i in range(1, 12)),
    "row_length": _HEAD + "1,Item 1,a\n" + _TEN,
    "bad_id": _HEAD + "x1,Item 1,a,1\n" + _TEN,
    "duplicate_id": _HEAD + "2,Item 1,a,1\n" + _TEN,
    "empty_name": _HEAD + "1, ,a,1\n" + _TEN,
    "empty_attributes": _HEAD + "1,Item 1,,1\n" + _TEN,
    "empty_attribute": _HEAD + "1,Item 1,a;;b,1\n" + _TEN,
    "repeated_attribute": _HEAD + "1,Item 1,a;b;a,1\n" + _TEN,
    "bad_score": _HEAD + "1,Item 1,a,nan\n" + _TEN,
    "bad_field_value": "id,name,attributes,score,price\n1,Item 1,a,1,cheap\n"
                       + "".join(f"{i},Item {i},a;b,{i},\n" for i in range(2, 12)),
    "too_few_items": _HEAD + "1,Item 1,a,1\n",
}

WARNING_CASES = {
    "case_clash": _HEAD + "1,Item 1,Puzzle;puzzle,1\n" + _TEN,
    "duplicate_item_name": _HEAD + "1,Item 2,a,1\n" + _TEN,
}


@pytest.mark.parametrize("code", sorted(ERROR_CASES))
def test_each_error_code_refuses_the_file(tmp_path, code):
    result = I.validate_import(_write(tmp_path, ERROR_CASES[code]))
    errors, _ = _codes(result)
    assert code in errors, [e.message for e in result.errors]


@pytest.mark.parametrize("code", sorted(WARNING_CASES))
def test_each_warning_code_is_kept_and_the_file_is_accepted(tmp_path, code):
    result = I.validate_import(_write(tmp_path, WARNING_CASES[code]))
    errors, warnings = _codes(result)
    assert errors == set() and code in warnings


def test_the_filter_column_must_exist_and_be_filled(tmp_path):
    text = "id,name,attributes,months\n1,Item 1,a,\n" + "".join(f"{i},Item {i},a,{i}\n" for i in range(2, 12))
    assert "bad_filter_value" in _codes(I.validate_import(_write(tmp_path, text), filter_field="months"))[0]
    assert "unknown_filter_column" in _codes(I.validate_import(_write(tmp_path, text), filter_field="weeks"))[0]
    assert "unknown_filter_column" in _codes(I.validate_import(_write(tmp_path, text), filter_field="name"))[0]


def test_attributes_csv_problems_are_errors_and_unused_rows_warn(tmp_path):
    main = _write(tmp_path, _HEAD + "".join(f"{i},Item {i},a;b,{i}\n" for i in range(1, 12)))
    cases = {
        "attributes_bad_header": "code,label\n1,a\n2,b\n",
        "attributes_bad_id": "id,name\n0,a\n2,b\n",
        "attributes_duplicate_id": "id,name\n1,a\n1,b\n",
        "attributes_duplicate_name": "id,name\n1,a\n2,a\n3,b\n",
        "attributes_empty_name": "id,name\n1,a\n2,b\n3,\n",
        "attributes_missing": "id,name\n1,a\n",
    }
    for code, text in cases.items():
        attrs = _write(tmp_path, text, "attributes.csv")
        assert code in _codes(I.validate_import(main, attributes_file=attrs))[0], code
    attrs = _write(tmp_path, "id,name\n7,a\n9,b\n12,unused\n", "attributes.csv")
    result = I.validate_import(main, attributes_file=attrs)
    assert _codes(result) == (set(), {"attributes_unused"})
    assert result.tables.attributes == {7: "a", 9: "b"} and result.tables.attribute_ids == "supplied"


def test_errors_are_collected_in_one_pass_with_spreadsheet_rows(tmp_path):
    text = _HEAD + "x,Item 1,a,1\n2,,a;a,oops\n" + _TEN.replace("2,Item 2", "13,Item 13")
    result = I.validate_import(_write(tmp_path, text))
    assert [(e.row, e.column, e.code) for e in result.errors] == [
        (2, "id", "bad_id"), (3, "name", "empty_name"), (3, "attributes", "repeated_attribute"),
        (3, "score", "bad_score")]


def test_large_files_warn(tmp_path):
    n = I.MANY_ITEMS + 1
    text = "id,name,attributes\n" + "".join(f"{i},Item {i},a{i % 7}\n" for i in range(1, n + 1))
    assert _codes(I.validate_import(_write(tmp_path, text))) == (set(), {"many_items"})


# ----------------------------------------------------------------------------- the normalised tables


def test_a_valid_file_without_attributes_csv_numbers_attributes_in_code_point_order(tmp_path):
    result = I.validate_import(_write(tmp_path, "﻿" + BASE))  # a BOM is stripped
    t = result.tables
    assert t.attribute_ids == "numbered"
    assert t.attributes == {1: "Beta", 2: "Gamma", 3: "Zeta", 4: "alpha"}  # code-point order: capitals first
    first = t.items[0]
    assert (first.id, first.name, first.rank, first.attribute_ids) == (1, "Item 1", 2, (3, 4, 1))
    # Score descending, ties by file order: item 3 scores 100 and ranks before item 1 (99).
    assert [i.id for i in sorted(t.items, key=lambda i: i.rank)][:3] == [3, 1, 2]


def test_reordering_rows_does_not_renumber_attributes(tmp_path):
    lines = BASE.splitlines()
    reordered = "\n".join([lines[0], *reversed(lines[1:])]) + "\n"
    a = I.validate_import(_write(tmp_path, BASE, "a.csv")).tables.attributes
    b = I.validate_import(_write(tmp_path, reordered, "b.csv")).tables.attributes
    assert a == b


def test_without_a_score_rank_is_file_order_and_a_filter_and_extra_fields_are_kept(tmp_path):
    text = _rows(score=False, extra="months")
    t = I.validate_import(_write(tmp_path, text), filter_field="months").tables
    assert [i.rank for i in t.items] == list(range(1, 13)) and t.score_present is False
    assert t.filter_field == "months" and t.items[1].filter_value == 3.0 and t.extra_fields == ()
    t2 = I.validate_import(_write(tmp_path, text)).tables
    assert t2.filter_field is None and t2.extra_fields == ("months",) and t2.fields[2] == {"months": 3.0}


def test_names_are_trimmed_and_nfc_normalised(tmp_path):
    text = _HEAD + "1,  Café ,  Café ; b ,1\n" + _TEN
    t = I.validate_import(_write(tmp_path, text)).tables
    assert t.items[0].name == "Café" and "Café" in t.attributes.values()


# ----------------------------------------------------------------------------- storage


def test_make_import_stores_a_fixed_import_and_the_loader_reads_it_back(tmp_path):
    src = _write(tmp_path, BASE, "My Games.csv")
    folder = I.make_import(tmp_path, src, now=NOW)
    assert folder == tmp_path / "imports" / "20261108T093000Z-my-games"
    assert (folder / "original" / "My Games.csv").read_bytes() == src.read_bytes()
    meta = json.loads((folder / "import.json").read_text(encoding="utf-8"))
    assert meta["import_id"] == folder.name and meta["sha256"] == I.sha256_file(src)
    assert (meta["items"], meta["attributes"], meta["attribute_ids"]) == (12, 4, "numbered")
    assert meta["score_present"] is True and meta["filter_field"] is None and meta["warnings"] == []
    loaded = I.load_import(folder)
    assert loaded == I.validate_import(src).tables and loaded.import_id == folder.name


def test_a_byte_identical_reimport_is_refused_pointing_at_the_existing_one(tmp_path):
    src = _write(tmp_path, BASE)
    first = I.make_import(tmp_path, src, now=NOW)
    with pytest.raises(I.ImportRefused) as info:
        I.make_import(tmp_path, src, now=LATER)
    assert first.name in str(info.value) and info.value.existing == first.name
    attrs = _write(tmp_path, "id,name\n1,Beta\n2,Gamma\n3,Zeta\n4,alpha\n", "attributes.csv")
    I.make_import(tmp_path, src, attributes_file=attrs, now=LATER)  # with attributes.csv: another Import


def test_a_refused_import_writes_errors_csv_and_a_copy_of_the_input(tmp_path):
    src = _write(tmp_path, ERROR_CASES["duplicate_id"])
    with pytest.raises(I.ImportRefused) as info:
        I.make_import(tmp_path, src, now=NOW)
    failed = info.value.failed_folder
    assert failed.parent == tmp_path / "imports" / "failed"
    assert (failed / "games.csv").read_bytes() == src.read_bytes()
    rows = list(csv.DictReader(io.StringIO((failed / "errors.csv").read_text(encoding="utf-8"))))
    assert list(rows[0]) == ["file", "row", "column", "code", "value", "message"]
    assert rows[0]["code"] == "duplicate_id" and rows[0]["file"] == "games.csv" and rows[0]["value"] == "2"
    assert not any(p.name != "failed" for p in (tmp_path / "imports").iterdir())


def test_the_cli_imports_and_reports_refusals(tmp_path, capsys):
    from steamstudy.cli import main

    good = _write(tmp_path, _rows(extra="months"), "good.csv")
    assert main(["--root", str(tmp_path), "import", str(good), "--filter", "months"]) == 0
    (folder,) = [p for p in (tmp_path / "imports").iterdir()]
    assert I.load_import(folder).filter_field == "months"
    bad = _write(tmp_path, ERROR_CASES["bad_id"], "bad.csv")
    assert main(["--root", str(tmp_path), "import", str(bad)]) == 2
    out = capsys.readouterr().out
    assert "bad_id: 1" in out and "x1" in out


def test_row_numbers_count_blank_lines_as_the_spreadsheet_does(tmp_path):
    text = "id,name,attributes,score\n\n1,Item 1,a,1\n\nx2,Item 2,a,2\n" + "".join(
        f"{i},Item {i},a;b,{i}\n" for i in range(3, 14))
    result = I.validate_import(_write(tmp_path, text))
    (bad,) = [e for e in result.errors if e.code == "bad_id"]
    assert bad.row == 5

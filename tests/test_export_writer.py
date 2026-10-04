from __future__ import annotations

import pytest

from steamstudy.export.schema import Column, FileSchema, columns_block
from steamstudy.export.writer import SchemaError, read_typed_csv, write_csv

SCHEMA = FileSchema(
    "sample.csv",
    "A test file.",
    (
        Column("tag_id", "int", "Steam tag id."),
        Column("tag", "str", "Tag name."),
        Column("share", "float", "Share of games."),
        Column("mmp", "float6", "Mean Monthly Players."),
        Column("is_center", "bool", "Whether the tag is a Cluster Center."),
        Column("tags", "str_list", "Tag names."),
        Column("appids", "int_list", "AppIDs."),
    ),
)

ROW = {
    "tag_id": 1664,
    "tag": "Головоломка, \"quoted\"",
    "share": 0.1,
    "mmp": 1234.5,
    "is_center": True,
    "tags": ["Puzzle", "Casual"],
    "appids": [10, 20],
}


def test_writer_applies_conventions(tmp_path):
    path = tmp_path / "sample.csv"
    write_csv(path, SCHEMA, [ROW, {**ROW, "share": None, "is_center": False, "tags": [], "appids": None}])
    raw = path.read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf")
    assert b"\r\n" not in raw
    text = raw.decode("utf-8-sig")
    lines = text.split("\n")
    assert lines[0] == "tag_id,tag,share,mmp,is_center,tags,appids"
    assert lines[1] == '1664,"Головоломка, ""quoted""",0.1,1234.500000,true,Puzzle;Casual,10;20'
    assert lines[2] == '1664,"Головоломка, ""quoted""",,1234.500000,false,,'
    assert lines[3] == ""


def test_floats_use_shortest_round_trip_repr(tmp_path):
    path = tmp_path / "f.csv"
    value = 1 / 3
    write_csv(path, SCHEMA, [{**ROW, "share": value}])
    from steamstudy.export.writer import read_csv

    assert read_csv(path)[0]["share"] == repr(value) == "0.3333333333333333"
    assert read_typed_csv(path, SCHEMA)[0]["share"] == value


def test_numpy_scalars_are_accepted():
    np = pytest.importorskip("numpy")
    from steamstudy.export.writer import render_csv

    text = render_csv(SCHEMA, [{**ROW, "tag_id": np.int64(5), "share": np.float64(0.25), "is_center": np.bool_(True)}])
    assert text.split("\n")[1].startswith("5,")
    assert ",0.25," in text and ",true," in text


def test_round_trip(tmp_path):
    path = tmp_path / "r.csv"
    write_csv(path, SCHEMA, [ROW])
    assert read_typed_csv(path, SCHEMA) == [ROW]


def test_undeclared_column_is_refused(tmp_path):
    with pytest.raises(SchemaError, match="undeclared"):
        write_csv(tmp_path / "x.csv", SCHEMA, [{**ROW, "extra": 1}])


def test_missing_declared_column_is_refused(tmp_path):
    row = dict(ROW)
    del row["tag"]
    with pytest.raises(SchemaError, match="missing"):
        write_csv(tmp_path / "x.csv", SCHEMA, [row])


@pytest.mark.parametrize(
    "column, value",
    [("tag_id", "1664"), ("tag_id", True), ("share", float("nan")), ("is_center", 1), ("tags", "Puzzle"), ("tags", ["a;b"])],
)
def test_wrong_types_are_refused(tmp_path, column, value):
    with pytest.raises(SchemaError):
        write_csv(tmp_path / "x.csv", SCHEMA, [{**ROW, column: value}])


def test_columns_block_and_prefix():
    stacked = SCHEMA.with_prefix("stacked.csv", (Column("dataset", "str", "Dataset key."),))
    assert stacked.column_names[0] == "dataset" and stacked.column_names[1:] == SCHEMA.column_names
    block = columns_block([SCHEMA])
    assert block["sample.csv"]["share"] == {"type": "float", "description": "Share of games."}


def test_schema_version_is_an_integer():
    from steamstudy.export.schema import SCHEMA_VERSION

    assert isinstance(SCHEMA_VERSION, int)

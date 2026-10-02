import json
from typing import get_type_hints

import pytest

from datamimic_ce.engine.io.files.cache import FileContentStorage
from datamimic_ce.engine.io.files.readers import FileUtil


@pytest.mark.parametrize(
    ("value",),
    [
        (None,),
        (False,),
        (7,),
        (3.5,),
        ("scalar root",),
        ([1, {"nested": [True, None, "text"]}],),
    ],
)
def test_read_json_preserves_scalar_and_recursive_roots(tmp_path, value):
    path = tmp_path / "value.json"
    path.write_text(json.dumps(value), encoding="utf-8")

    assert FileUtil.read_json(path) == value


def test_read_json_to_list_preserves_list_roots_with_scalar_values(tmp_path):
    path = tmp_path / "scalar.json"
    path.write_text('[1, "scalar item"]', encoding="utf-8")

    assert FileUtil.read_json_to_list(path) == [1, "scalar item"]


def test_read_json_to_list_rejects_non_list_roots(tmp_path):
    path = tmp_path / "scalar.json"
    path.write_text('"scalar root"', encoding="utf-8")

    with pytest.raises(ValueError, match="must contain a list of objects"):
        FileUtil.read_json_to_list(path)


def test_csv_raw_reader_caches_quoted_rows(tmp_path):
    path = tmp_path / "quoted.csv"
    path.write_text('name|note\nAda|"uses | delimiter"\n', encoding="utf-8")

    assert FileUtil._read_raw_csv(path, "|") == [("name", "note"), ("Ada", "uses | delimiter")]

    path.unlink()
    assert FileUtil._read_raw_csv(path, "|") == [("name", "note"), ("Ada", "uses | delimiter")]


def test_csv_readers_preserve_bom_and_ragged_row_behavior(tmp_path):
    path = tmp_path / "ragged.csv"
    path.write_text("\ufeffname,value\nAda\nGrace,compiler,extra\n", encoding="utf-8")

    assert FileUtil.read_csv_to_dict_of_tuples_with_header(path) == (
        {"name": 0, "value": 1},
        [("Ada",), ("Grace", "compiler", "extra")],
    )
    assert FileUtil.read_csv_to_dict_list(path, ",") == [
        {"\ufeffname": "Ada"},
        {"\ufeffname": "Grace", "value": "compiler"},
    ]


@pytest.mark.parametrize("weight_column", ["weight", "chance"])
def test_weighted_csv_reader_preserves_string_rows_and_repeated_reads(tmp_path, weight_column):
    path = tmp_path / "weighted.csv"
    path.write_text(
        f'account id,display name,{weight_column}\n007,"A, Inc.",1.5\n008,Grace,2\n',
        encoding="utf-8",
    )

    expected = (
        [1.5, 2.0],
        [
            {"account id": "007", "display name": "A, Inc."},
            {"account id": "008", "display name": "Grace"},
        ],
    )
    assert FileUtil.read_csv_having_weight_column(path, weight_column) == expected
    assert FileUtil.read_csv_having_weight_column(path, weight_column) == expected


def test_csv_reader_rejects_malformed_cached_rows(tmp_path):
    path = tmp_path / "cached.csv"
    FileContentStorage._file_data_cache[str(path)] = [("valid",), (1,)]

    with pytest.raises(ValueError, match="Cached CSV data.*invalid shape"):
        FileUtil._read_raw_csv(path, ",")


def test_csv_empty_file_is_empty_for_raw_and_dict_readers(tmp_path):
    path = tmp_path / "empty.csv"
    path.write_text("", encoding="utf-8")

    assert FileUtil._read_raw_csv(path, ",") == []
    assert FileUtil.read_csv_to_dict_list(path, ",") == []
    with pytest.raises(IndexError):
        FileUtil.read_csv_to_dict_of_tuples_with_header(path)


def test_csv_reader_annotations_are_narrow():
    assert get_type_hints(FileUtil._read_raw_csv)["return"] == list[tuple[str, ...]]
    assert get_type_hints(FileUtil.read_csv_to_dict_list)["return"] == list[dict[str, str]]
    assert get_type_hints(FileUtil.read_csv_having_weight_column).get("return") == tuple[
        list[float], list[dict[str, str]]
    ]
    assert get_type_hints(FileUtil.read_csv_to_dict_of_tuples_with_header)["return"] == tuple[
        dict[str, int], list[tuple[str, ...]]
    ]
    assert get_type_hints(FileUtil.read_csv_to_list_of_tuples_without_header)["return"] == list[
        tuple[str, ...]
    ]

import json
from json import JSONDecodeError

import pytest

from datamimic_ce.engine.dsl.vocabulary.source_capabilities import SourceFileFormat
from datamimic_ce.engine.io.files.readers import load_source_rows


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ({"id": 1}, [{"id": 1}]),
        ([{"id": 1}, {"id": 2}], [{"id": 1}, {"id": 2}]),
        ([], []),
    ],
    ids=("single-object", "records", "empty-records"),
)
def test_json_source_accepts_object_and_record_list_shapes(tmp_path, value, expected) -> None:
    path = tmp_path / "source.json"
    path.write_text(json.dumps(value), encoding="utf-8")

    assert load_source_rows(path, ",", SourceFileFormat.JSON) == expected


@pytest.mark.parametrize(
    "value",
    [None, False, 7, 3.5, "scalar", [1], [{"id": 1}, "bad"]],
    ids=("null", "boolean", "integer", "float", "string", "scalar-list", "mixed-record-list"),
)
def test_json_source_rejects_non_record_shapes(tmp_path, value) -> None:
    path = tmp_path / "source.json"
    path.write_text(json.dumps(value), encoding="utf-8")

    with pytest.raises(ValueError, match="must contain a list of objects or a dictionary"):
        load_source_rows(path, ",", SourceFileFormat.JSON)


def test_malformed_json_source_is_rejected(tmp_path) -> None:
    path = tmp_path / "source.json"
    path.write_text('{"id":', encoding="utf-8")

    with pytest.raises(JSONDecodeError):
        load_source_rows(path, ",", SourceFileFormat.JSON)

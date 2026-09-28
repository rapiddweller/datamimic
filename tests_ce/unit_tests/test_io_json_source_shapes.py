import json

import pytest

from datamimic_ce.engine.dsl.vocabulary.source_capabilities import SourceFileFormat
from datamimic_ce.engine.io.data_sources.data_source_registry import DataSourceRegistry


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

    assert DataSourceRegistry._get_source(str(path), ",", SourceFileFormat.JSON) == expected


@pytest.mark.parametrize(
    "value",
    [None, False, 7, 3.5, "scalar", [1], [{"id": 1}, "bad"]],
    ids=("null", "boolean", "integer", "float", "string", "scalar-list", "mixed-record-list"),
)
def test_json_source_rejects_non_record_shapes(tmp_path, value) -> None:
    path = tmp_path / "source.json"
    path.write_text(json.dumps(value), encoding="utf-8")

    with pytest.raises(ValueError, match="must contain a list of objects or a dictionary"):
        DataSourceRegistry._get_source(str(path), ",", SourceFileFormat.JSON)

import json

import pytest

from datamimic_ce.engine.io.files import FileUtil


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

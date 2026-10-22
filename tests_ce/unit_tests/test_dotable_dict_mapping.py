# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

from collections.abc import Mapping

import pytest

from datamimic_ce.engine.runtime.scripting.evaluation import DotableDict, evaluate_python


def _row() -> DotableDict:
    return DotableDict({"id": 1, "items": [{"sku": "a"}, "plain"], "nested": {"x": 2}})


def test_item_access_wraps_nested_values() -> None:
    row = _row()

    assert row["id"] == 1
    assert isinstance(row["nested"], DotableDict)
    assert row["nested"]["x"] == 2
    assert isinstance(row["items"][0], DotableDict)
    assert row["items"][1] == "plain"


def test_dict_unpacking_and_iteration_follow_mapping_protocol() -> None:
    row = _row()

    assert list(dict(row)) == ["id", "items", "nested"]
    assert {**row}.keys() == {"id", "items", "nested"}
    assert list(row) == ["id", "items", "nested"]
    assert list(row.keys()) == ["id", "items", "nested"]


def test_len_and_membership_delegate_to_fields() -> None:
    row = _row()

    assert len(row) == 3
    assert "id" in row
    assert "zz" not in row


def test_get_returns_default_for_missing_key() -> None:
    row = _row()

    assert row.get("id") == 1
    assert row.get("zz", "none") == "none"
    assert row.get("zz") is None


def test_missing_key_raises_key_error_and_missing_attribute_raises_attribute_error() -> None:
    row = _row()

    with pytest.raises(KeyError):
        _ = row["zz"]
    with pytest.raises(AttributeError, match="Cannot find attribute 'zz'"):
        _ = row.zz


def test_is_registered_as_mapping_without_inheriting_methods() -> None:
    row = _row()

    assert isinstance(row, Mapping)
    # WHY: a field named `items` must stay a field, not the Mapping.items() method.
    assert isinstance(row.items, list)
    assert row.items[0].sku == "a"


def test_script_dict_result_exports_nested_rows_plain() -> None:
    row = _row()

    result = evaluate_python("dict(row)", {}, {"row": row})

    assert type(result) is dict
    assert type(result["nested"]) is dict
    assert type(result["items"][0]) is dict


def test_script_result_keeps_identity_and_dict_subclasses() -> None:
    from collections import Counter, defaultdict

    shared = {"a": 1, "nested": {"b": 2}}
    counts: defaultdict[str, int] = defaultdict(int)
    tally = Counter("aab")
    namespace: dict[str, object] = {"shared": shared, "counts": counts, "tally": tally}

    assert evaluate_python("shared", namespace, namespace) is shared
    assert evaluate_python("counts", namespace, namespace) is counts
    assert evaluate_python("tally", namespace, namespace) is tally
    # A row inside still exports as a plain dict, wherever it sits.
    row_result = evaluate_python("{'r': row, 'l': [row]}", {}, {"row": DotableDict({"id": 1})})
    assert type(row_result["r"]) is dict and type(row_result["l"][0]) is dict

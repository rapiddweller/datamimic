# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""RDBMS SQL matrix (#228): the same DSL cases (matrix_cases.xml) run end-to-end on every engine and must give
the same rows. Covers deterministic paging of table sources and selectors (own ORDER BY, ties, aliases, unions,
bounded selectors), the variable count path, <execute> script splitting, and dbms validation."""

from pathlib import Path

import pytest

from datamimic_ce.data_mimic_test import DataMimicTest

_TEST_DIR = Path(__file__).resolve().parent
_ENGINES = ["postgresql", "mssql", "oracle", "mysql", "sqlite"]

_BY_GRP_ID = [(1, 2), (1, 5), (1, 8), (1, 11), (2, 3), (2, 6), (2, 9), (2, 12), (3, 1), (3, 4), (3, 7), (3, 10)]
_BY_ID = sorted(_BY_GRP_ID, key=lambda row: row[1])
_BY_GRP_DESC_ID = sorted(_BY_GRP_ID, key=lambda row: (-row[0], row[1]))

_EXACT_ORDER = {
    "table_keyless": _BY_GRP_ID,
    "table_pk": _BY_ID,
    "table_composite_pk": _BY_GRP_ID,
    "selector_unordered": _BY_GRP_ID,
    "selector_window": _BY_GRP_ID,
    "selector_unique_order": _BY_ID[::-1],
    "selector_tied_order": _BY_GRP_ID,
    "selector_star_order": _BY_GRP_ID,
    "selector_union_order": [row for row in _BY_GRP_DESC_ID if row[0] != 2],
    "selector_terminated": _BY_ID,
    "selector_bounded_ordered": _BY_GRP_DESC_ID[:7],
    "selector_bounded_unordered": _BY_GRP_ID[:7],
}
_EVERY_ROW_ONCE = ["table_keyless_mp", "table_random_mp", "selector_unordered_mp", "selector_tied_order_mp"]


def _grp_id(rows: list[dict], grp_key: str = "grp") -> list[tuple[int, int]]:
    return [(row[grp_key], row["id"]) for row in rows]


@pytest.mark.parametrize("engine", _ENGINES)
def test_rdbms_sql_matrix(engine: str) -> None:
    test_engine = DataMimicTest(test_dir=_TEST_DIR, filename=f"matrix_{engine}.xml", capture_test_result=True)
    test_engine.test_with_timer()
    result = test_engine.capture_result()

    for product, expected in _EXACT_ORDER.items():
        assert _grp_id(result[product]) == expected, product
    for product in _EVERY_ROW_ONCE:
        assert sorted(_grp_id(result[product])) == _BY_GRP_ID, product

    assert all(row["rn"] == row["id"] for row in result["selector_window"])
    assert _grp_id(result["selector_alias_order"], grp_key="g") == _BY_GRP_DESC_ID
    assert [row["id"] for row in result["variable_selector_cyclic"]] == [*range(12, 0, -1), 12, 11, 10]
    assert [(row["id"], row["note"]) for row in result["script_rows"]] == [
        (1, "a;b"),
        (2, "x -- y"),
        (3, "p /* q */ r"),
        (4, "plsql"),
        (5, "trigger"),
        (6, "100% :done"),
    ]


def test_unsupported_dbms_fails_when_the_descriptor_is_read() -> None:
    with pytest.raises(Exception, match="dbms"):
        DataMimicTest(test_dir=_TEST_DIR, filename="invalid_dbms.xml").test_with_timer()

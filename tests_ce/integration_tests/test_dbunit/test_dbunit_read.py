"""Native dbunit READ — TDD against the real legacy shop.dbunit.xml plus an edge-case fixture.

dbunit flat XML: each child of <dataset> is a row, the element name is the table, attributes are the
columns. A dataset holds MANY tables, so a reader picks ONE table (the entity to read).
"""

from pathlib import Path

import pytest

from datamimic_ce.utils.file_util import FileUtil

_DATA = Path(__file__).resolve().parent / "data"
_SHOP = _DATA / "shop.dbunit.xml"
_COMPLEX = _DATA / "complex.dbunit.xml"


# ---- happy path: real migrated dataset ----


def test_reads_one_table_from_the_real_shop_dataset():
    cats = FileUtil.read_dbunit_to_dict_list(_SHOP, "db_category")
    assert len(cats) == 28
    assert FileUtil.read_dbunit_to_dict_list(_SHOP, "db_user").__len__() == 4
    # attributes become columns
    assert cats[0]["id"] == "FOOD"
    assert cats[0]["name"] == "Food"


def test_columns_are_unified_absent_attribute_becomes_a_null_cell():
    cats = FileUtil.read_dbunit_to_dict_list(_SHOP, "db_category")
    # column sensing: every row carries every column; the top-level category's absent parent_id is NULL
    assert cats[0]["parent_id"] is None
    # a child category carries the real value
    assert cats[1]["parent_id"] == "FOOD"


# ---- edge cases ----


def test_xml_special_chars_unicode_and_empty_string_are_preserved():
    accounts = FileUtil.read_dbunit_to_dict_list(_COMPLEX, "account")
    assert accounts[0]["name"] == "A & B <Ltd>"  # entities decoded
    assert accounts[0]["note"] == 'quote:"x"'
    assert accounts[1]["name"] == "Ünïcödé Ω"  # unicode
    assert accounts[1]["note"] == ""  # present empty string kept ""
    assert accounts[2]["note"] is None  # absent attribute -> NULL cell (distinct from "")
    assert accounts[0]["zip"] == "01234"  # leading zero kept as string, not coerced


def test_a_dtd_reference_is_ignored_not_fetched():
    # the fixture declares <!DOCTYPE ... SYSTEM "ignored.dtd"> - must parse without fetching it
    assert len(FileUtil.read_dbunit_to_dict_list(_COMPLEX, "tag")) == 2


# ---- error handling ----


def test_unknown_table_lists_the_available_tables():
    with pytest.raises(ValueError, match=r"no rows for table 'nope'.*db_category|account"):
        FileUtil.read_dbunit_to_dict_list(_SHOP, "nope")


def test_a_non_dataset_root_is_a_clear_error(tmp_path):
    bad = tmp_path / "bad.dbunit.xml"
    bad.write_text("<notadataset><row a='1'/></notadataset>")
    with pytest.raises(ValueError, match=r"dataset"):
        FileUtil.read_dbunit_to_dict_list(bad, "row")

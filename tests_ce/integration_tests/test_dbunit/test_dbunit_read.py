"""Native dbunit READ — TDD against the real Benerator shop.dbunit.xml plus an edge-case fixture.

dbunit flat XML: each child of <dataset> is a row, the element name is the table, attributes are the
columns. A dataset holds MANY tables, so a reader picks ONE table (the entity to read).
"""

from pathlib import Path

import pytest

from datamimic_ce.utils.file_util import FileUtil

_DATA = Path(__file__).resolve().parent / "data"
_SHOP = _DATA / "shop.dbunit.xml"
_COMPLEX = _DATA / "complex.dbunit.xml"


# ---- happy path: real Benerator dataset ----

def test_reads_one_table_from_the_real_shop_dataset():
    cats = FileUtil.read_dbunit_to_dict_list(_SHOP, "db_category")
    assert len(cats) == 28
    assert FileUtil.read_dbunit_to_dict_list(_SHOP, "db_user") .__len__() == 4
    # attributes become columns
    assert cats[0]["id"] == "FOOD"
    assert cats[0]["name"] == "Food"


def test_ragged_rows_keep_their_own_columns_null_is_an_absent_attribute():
    cats = FileUtil.read_dbunit_to_dict_list(_SHOP, "db_category")
    # top-level category has no parent_id (NULL = absent attribute)
    assert "parent_id" not in cats[0]
    # a child category carries parent_id
    assert cats[1]["parent_id"] == "FOOD"


# ---- edge cases ----

def test_xml_special_chars_unicode_and_empty_string_are_preserved():
    accounts = FileUtil.read_dbunit_to_dict_list(_COMPLEX, "account")
    assert accounts[0]["name"] == "A & B <Ltd>"        # entities decoded
    assert accounts[0]["note"] == 'quote:"x"'
    assert accounts[1]["name"] == "Ünïcödé Ω"          # unicode
    assert accounts[1]["note"] == ""                   # empty string kept (distinct from absent)
    assert "note" not in accounts[2]                   # absent attribute stays absent (NULL)
    assert accounts[0]["zip"] == "01234"               # leading zero kept as string, not coerced


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

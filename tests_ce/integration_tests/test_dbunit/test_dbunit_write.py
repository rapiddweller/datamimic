"""Native dbunit WRITE (target="DbUnit") — TDD, including a read->write->read round-trip."""

import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest
from datamimic_ce.utils.file_util import FileUtil

_DIR = Path(__file__).resolve().parent


def _clean():
    shutil.rmtree(_DIR / "output", ignore_errors=True)


def _written(basename: str) -> Path:
    hits = list((_DIR / "output").rglob(f"{basename}*.dbunit.xml"))
    assert hits, f"no {basename}.dbunit.xml written (found: {[p.name for p in (_DIR / 'output').rglob('*')]})"
    return hits[0]


def test_generate_writes_a_dbunit_dataset_named_by_targetentity():
    _clean()
    try:
        DataMimicTest(test_dir=_DIR, filename="write_products.xml", capture_test_result=True).test_with_timer()
        root = ET.parse(str(_written("products"))).getroot()
        assert root.tag == "dataset"
        rows = [c for c in root if c.tag == "products"]  # table named by targetEntity
        assert len(rows) == 3
        assert all("sku" in r.attrib and "price" in r.attrib for r in rows)
    finally:
        _clean()


def test_special_chars_and_unicode_are_escaped_on_write():
    _clean()
    try:
        DataMimicTest(test_dir=_DIR, filename="write_special.xml", capture_test_result=True).test_with_timer()
        # re-read via our own reader: the escaped attributes must decode back to the originals
        rows = FileUtil.read_dbunit_to_dict_list(_written("acct"), "acct")
        assert rows[0]["name"] == 'A & B <Ltd> "q"'
    finally:
        _clean()


def test_round_trip_read_write_read_is_structurally_identical():
    # read the complex fixture, write it out as a dbunit dataset, read it back -> same rows
    _clean()
    try:
        original = FileUtil.read_dbunit_to_dict_list(_DIR / "data" / "complex.dbunit.xml", "account")
        DataMimicTest(test_dir=_DIR, filename="roundtrip.xml", capture_test_result=True).test_with_timer()
        reread = FileUtil.read_dbunit_to_dict_list(_written("account"), "account")
        assert reread == original  # ragged columns, NULL-as-absent, empty-string, unicode all preserved
    finally:
        _clean()


def test_round_trip_of_the_real_legacy_shop_dataset():
    # the real legacy shop.dbunit.xml (28 categories, ragged parent_id) read -> DbUnit write -> read
    _clean()
    try:
        original = FileUtil.read_dbunit_to_dict_list(_DIR / "data" / "shop.dbunit.xml", "db_category")
        DataMimicTest(test_dir=_DIR, filename="roundtrip_shop.xml", capture_test_result=True).test_with_timer()
        reread = FileUtil.read_dbunit_to_dict_list(_written("db_category"), "db_category")
        assert reread == original
    finally:
        _clean()


def test_zero_records_writes_no_file_and_does_not_crash():
    # consistent with every buffered exporter: 0 records -> nothing flushed, no file, no error
    _clean()
    try:
        DataMimicTest(test_dir=_DIR, filename="write_empty.xml", capture_test_result=True).test_with_timer()
        assert not list((_DIR / "output").rglob("empty*.dbunit.xml"))
    finally:
        _clean()

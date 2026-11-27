"""Native dbunit WRITE (target="DbUnit") — TDD, including a read->write->read round-trip."""

import xml.etree.ElementTree as ET
from pathlib import Path

from datamimic_ce.engine.io.files.api import FileUtil
from datamimic_ce.interfaces.python.data_mimic_test import DataMimicTest


def _written(project_dir: Path, basename: str) -> Path:
    output = project_dir / "output"
    hits = list(output.rglob(f"{basename}*.dbunit.xml"))
    assert hits, f"no {basename}.dbunit.xml written (found: {[p.name for p in output.rglob('*')]})"
    return hits[0]


def test_generate_writes_a_dbunit_dataset_named_by_targetentity(project_dir):
    DataMimicTest(test_dir=project_dir, filename="write_products.xml", capture_test_result=True).test_with_timer()
    root = ET.parse(str(_written(project_dir, "products"))).getroot()
    assert root.tag == "dataset"
    rows = [c for c in root if c.tag == "products"]  # table named by targetEntity
    assert len(rows) == 3
    assert all("sku" in r.attrib and "price" in r.attrib for r in rows)


def test_special_chars_and_unicode_are_escaped_on_write(project_dir):
    DataMimicTest(test_dir=project_dir, filename="write_special.xml", capture_test_result=True).test_with_timer()
    # re-read via our own reader: the escaped attributes must decode back to the originals
    rows = FileUtil.read_dbunit_to_dict_list(_written(project_dir, "acct"), "acct")
    assert rows[0]["name"] == 'A & B <Ltd> "q"'


def test_round_trip_read_write_read_is_structurally_identical(project_dir):
    # read the complex fixture, write it out as a dbunit dataset, read it back -> same rows
    original = FileUtil.read_dbunit_to_dict_list(project_dir / "data" / "complex.dbunit.xml", "account")
    DataMimicTest(test_dir=project_dir, filename="roundtrip.xml", capture_test_result=True).test_with_timer()
    reread = FileUtil.read_dbunit_to_dict_list(_written(project_dir, "account"), "account")
    assert reread == original  # ragged columns, NULL-as-absent, empty-string, unicode all preserved


def test_round_trip_of_the_real_legacy_shop_dataset(project_dir):
    # the real legacy shop.dbunit.xml (28 categories, ragged parent_id) read -> DbUnit write -> read
    original = FileUtil.read_dbunit_to_dict_list(project_dir / "data" / "shop.dbunit.xml", "db_category")
    DataMimicTest(test_dir=project_dir, filename="roundtrip_shop.xml", capture_test_result=True).test_with_timer()
    reread = FileUtil.read_dbunit_to_dict_list(_written(project_dir, "db_category"), "db_category")
    assert reread == original


def test_zero_records_writes_no_file_and_does_not_crash(project_dir):
    # consistent with every buffered exporter: 0 records -> nothing flushed, no file, no error
    DataMimicTest(test_dir=project_dir, filename="write_empty.xml", capture_test_result=True).test_with_timer()
    assert not list((project_dir / "output").rglob("empty*.dbunit.xml"))

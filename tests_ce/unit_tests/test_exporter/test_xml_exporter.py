# test_xml_exporter.py

import tempfile
import unittest
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path

from datamimic_ce.exporters.exporter_state_manager import ExporterStateManager
from datamimic_ce.exporters.xml_exporter import XMLExporter  # Adjust the import path as necessary
from tests_ce.unit_tests.test_exporter.exporter_test_util import MockSetupContext, generate_mock_data


class TestXMLExporter(unittest.TestCase):
    def setUp(self, encoding='utf-8', root_element='list', item_element='item'):
        """Set up for each test."""
        self.setup_context = MockSetupContext(task_id=f"test_task_{uuid.uuid4().hex}", descriptor_dir="test_dir")
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp_dir_path = Path(self.tmp_dir.name)
        self.setup_context.descriptor_dir = self.tmp_dir_path
        self.setup_context.properties = {}

        self.exporter = XMLExporter(
            setup_context=self.setup_context,
            product_name="test_product",
            chunk_size=1000,
            root_element=root_element,
            item_element=item_element,
            encoding=encoding
        )

    def tearDown(self):
        """Clean up temporary directories."""
        self.tmp_dir.cleanup()

    def test_single_process_chunking(self):
        """Test exporting 3000 records with chunk size 1000 in a single process (3 chunk files expected)."""
        # Test data
        data = generate_mock_data(3000)
        product = ("test_product", data)
        stmt_full_name = "test_product"
        worker_id = 1
        exporter_state_manager = ExporterStateManager(worker_id)
        expected_chunks = 3  # 3000 data / 1000 chunk_size = 3

        # Run exporter

        self.exporter.consume(product, stmt_full_name, exporter_state_manager)
        self.exporter.finalize_chunks(worker_id)

        xml_files = [f for f in list(self.tmp_dir_path.rglob("*")) if f.is_file()]

        self.assertEqual(len(xml_files), expected_chunks)

        total_items = 0
        for xml_file in xml_files:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            self.assertEqual(root.tag, self.exporter.root_element)
            records = root.findall(f".//{self.exporter.item_element}")
            total_items += len(records)

        self.assertEqual(len(data), total_items)

    def test_export_with_custom_root_and_item_elements(self):
        """Test exporting data with custom root and item element names."""
        custom_root = "movies"
        custom_item = "movie"

        self.setUp(root_element=custom_root, item_element=custom_item)
        # Test data
        data = generate_mock_data(3000)
        product = ("test_product", data)
        stmt_full_name = "test_product"
        worker_id = 1
        exporter_state_manager = ExporterStateManager(worker_id)
        expected_chunks = 3  # 3000 data / 1000 chunk_size = 3

        # Run exporter

        self.exporter.consume(product, stmt_full_name, exporter_state_manager)
        self.exporter.finalize_chunks(worker_id)

        xml_files = [f for f in list(self.tmp_dir_path.rglob("*")) if f.is_file()]

        self.assertEqual(len(xml_files), expected_chunks)

        total_items = 0
        for xml_file in xml_files:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            self.assertEqual(root.tag, custom_root)
            records = root.findall(f".//{custom_item}")
            total_items += len(records)

        self.assertEqual(len(data), total_items)

    def test_invalid_product_handling(self):
        """Test that consuming an invalid product raises ValueError."""
        stmt_full_name = "test_product"
        worker_id = 1
        exporter_state_manager = ExporterStateManager(worker_id)

        # Product is not a tuple (this case is str)
        with self.assertRaises(ValueError) as e:
            self.exporter.consume("invalid_product", stmt_full_name, exporter_state_manager)
        self.assertEqual(str(e.exception), "Product must be a tuple of (name, data) or (name, data, extra)")

        # Product tuple has less than two elements
        with self.assertRaises(ValueError) as e:
            self.exporter.consume(("test_product",), stmt_full_name, exporter_state_manager)
        self.assertEqual(str(e.exception), "Product must be a tuple of (name, data) or (name, data, extra)")

        # Product name is None
        with self.assertRaises(ValueError) as e:
            self.exporter.consume((None, generate_mock_data(10)), stmt_full_name, exporter_state_manager)
        self.assertEqual(str(e.exception), "Product must contain non-None name and data")

    def test_special_characters_in_data(self):
        """Test exporting data containing special characters."""
        # Test data
        special_data = [
            {"id": "1", "title": 'Title with <tag>', "year": 2020},
            {"id": "2", "title": 'Title with & ampersand', "year": 2021},
            {"id": "3", "title": 'Title with "quotes"', "year": 2022},
            {"id": "4", "title": "Title with 'apostrophe'", "year": 2023},
        ]
        product = ("test_product", special_data)
        stmt_full_name = "test_product"
        worker_id = 1
        exporter_state_manager = ExporterStateManager(worker_id)
        expected_chunks = 1

        # Run exporter

        self.exporter.consume(product, stmt_full_name, exporter_state_manager)
        self.exporter.finalize_chunks(worker_id)

        xml_files = [f for f in list(self.tmp_dir_path.rglob("*")) if f.is_file()]

        self.assertEqual(len(xml_files), expected_chunks)

        total_items = 0
        for xml_file in xml_files:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            self.assertEqual(root.tag, self.exporter.root_element)
            records = root.findall(f".//{self.exporter.item_element}")
            total_items += len(records)
            # Verify each record's content
            for record, data in zip(records, special_data, strict=False):
                for key, value in data.items():
                    self.assertEqual(record.find(key).text, str(value))

        self.assertEqual(len(special_data), total_items)

    def test_empty_data_handling(self):
        """Test exporting when data list is empty."""
        product = ("test_product", [])
        stmt_full_name = "test_product"
        worker_id = 1
        exporter_state_manager = ExporterStateManager(worker_id)

        # Run exporter
        self.exporter.consume(product, stmt_full_name, exporter_state_manager)
        self.exporter.finalize_chunks(worker_id)
        # Should not write any files
        xml_files = [f for f in list(self.tmp_dir_path.rglob("*")) if f.is_file()]
        self.assertEqual(len(xml_files), 0)


if __name__ == '__main__':
    unittest.main()

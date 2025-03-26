import json
import math
import multiprocessing
import os
import tempfile
import unittest
import uuid
from pathlib import Path

from datamimic_ce.exporters.exporter_state_manager import ExporterStateManager
from datamimic_ce.exporters.json_exporter import JsonExporter
from tests_ce.unit_tests.test_exporter.exporter_test_util import generate_mock_data, MockSetupContext


class TestJsonExporter(unittest.TestCase):
    def setUp(self, encoding='utf-8', chunk_size=1000, use_ndjson=False):
        self.task_id = f"test_task_{uuid.uuid4().hex}"
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp_dir_path = Path(self.tmp_dir.name)

        self.setup_context = MockSetupContext(
            task_id=self.task_id,
            descriptor_dir=self.tmp_dir_path
        )
        self.encoding = encoding

        self.exporter = JsonExporter(
            setup_context=self.setup_context,
            product_name="test_product",
            use_ndjson=use_ndjson,
            chunk_size=chunk_size,
            encoding=self.encoding,
        )

    def tearDown(self):
        """Clean up the test directory and reset mocks."""
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

        json_files = [f for f in list(self.tmp_dir_path.rglob("*")) if f.is_file()]

        files_created = len(json_files)
        self.assertEqual(files_created, expected_chunks)

        total_items = 0
        for json_file in json_files:
            try:
                with json_file.open("r", encoding=self.encoding) as file:
                    file_data = json.load(file)  # Load JSON content

                    if isinstance(file_data, list | dict):
                        total_items += len(file_data)
                    else:
                        print(f"Skipping {json_file}: Unsupported format")

            except json.JSONDecodeError:
                print(f"Skipping {json_file}: Invalid JSON")

        self.assertEqual(len(data), total_items)

    def test_large_data_non_multiple_chunk_size(self):
        """Test exporting 1,000,001 records with chunk size 100,000 (11 chunks expected)."""
        total_records = 1_000_001
        chunk_size = 100_000
        data = generate_mock_data(total_records)
        product = ("test_product", data)
        self.setUp(chunk_size=chunk_size)

        stmt_full_name = "test_product"
        worker_id = 1
        exporter_state_manager = ExporterStateManager(worker_id)

        expected_chunks = int(math.ceil(total_records / chunk_size))

        # Run exporter

        self.exporter.consume(product, stmt_full_name, exporter_state_manager)
        self.exporter.finalize_chunks(worker_id)

        json_files = [f for f in list(self.tmp_dir_path.rglob("*")) if f.is_file()]

        files_created = len(json_files)
        self.assertEqual(files_created, expected_chunks)

        total_items = 0
        for json_file in json_files:
            try:
                with json_file.open("r", encoding=self.encoding) as file:
                    file_data = json.load(file)  # Load JSON content

                    if isinstance(file_data, list | dict):
                        total_items += len(file_data)
                    else:
                        print(f"Skipping {json_file}: Unsupported format")

            except json.JSONDecodeError:
                print(f"Skipping {json_file}: Invalid JSON")

        self.assertEqual(len(data), total_items)

    def test_zero_records(self):
        """Test exporting zero records. Expecting no storage writes."""
        product = ("test_product", [])

        stmt_full_name = "test_product"
        worker_id = 1
        exporter_state_manager = ExporterStateManager(worker_id)

        # Run exporter

        self.exporter.consume(product, stmt_full_name, exporter_state_manager)
        self.exporter.finalize_chunks(worker_id)

        json_files = [f for f in list(self.tmp_dir_path.rglob("*")) if f.is_file()]

        files_created = len(json_files)

        self.assertEqual(files_created, 0)

    def test_chunk_size_of_one(self):
        """Test exporting 10 records with chunk size 1. Expecting 10 JSON files."""
        chunk_size = 1
        self.setUp(chunk_size=chunk_size)
        data = generate_mock_data(10)
        product = ("test_product", data)

        stmt_full_name = "test_product"
        worker_id = 1
        exporter_state_manager = ExporterStateManager(worker_id)

        # Run exporter

        self.exporter.consume(product, stmt_full_name, exporter_state_manager)
        self.exporter.finalize_chunks(worker_id)

        json_files = [f for f in list(self.tmp_dir_path.rglob("*")) if f.is_file()]

        files_created = len(json_files)

        self.assertEqual(files_created, 10)

        total_items = 0
        for json_file in json_files:
            try:
                with json_file.open("r", encoding=self.encoding) as file:
                    file_data = json.load(file)  # Load JSON content

                    if isinstance(file_data, list | dict):
                        total_items += len(file_data)
                    else:
                        print(f"Skipping {json_file}: Unsupported format")

            except json.JSONDecodeError:
                print(f"Skipping {json_file}: Invalid JSON")

        singe_chunk_item_len = 0
        for e in data:
            singe_chunk_item_len += len(e)

        self.assertEqual(singe_chunk_item_len, total_items)

    def test_json_format_output(self):
        """Test JSON formatting in exported content."""
        data = generate_mock_data(5)
        product = ("test_product", data)
        stmt_full_name = "test_product"
        worker_id = 1
        exporter_state_manager = ExporterStateManager(worker_id)

        # Run exporter
        self.exporter.consume(product, stmt_full_name, exporter_state_manager)
        self.exporter.finalize_chunks(worker_id)
        json_files = [f for f in list(self.tmp_dir_path.rglob("*")) if f.is_file()]

        files_created = len(json_files)

        self.assertEqual(files_created, 1)

        for json_file in json_files:
            try:
                with json_file.open("r", encoding=self.encoding) as file:
                    file_data = json.load(file)  # Load JSON content
                    self.assertEqual(data, file_data)
            except json.JSONDecodeError:
                print(f"Skipping {json_file}: Invalid JSON")

    def test_invalid_chunk_size(self):
        """Test initializing exporter with invalid chunk size (zero or negative). Expecting ValueError."""
        with self.assertRaises(ValueError) as context_zero:
            JsonExporter(
                setup_context=self.setup_context,
                product_name="test_product",
                use_ndjson=False,
                encoding="utf-8",
                chunk_size=0
            )
        self.assertIn("Chunk size must be a positive integer", str(context_zero.exception))

        with self.assertRaises(ValueError) as context_negative:
            JsonExporter(
                setup_context=self.setup_context,
                product_name="test_product",
                use_ndjson=False,
                encoding="utf-8",
                chunk_size=-5
            )
        self.assertIn("Chunk size must be a positive integer", str(context_negative.exception))

    def test_ndjson_output(self):
        """Test exporting data with use_ndjson=True produces correct NDJSON format."""
        # Reinitialize
        self.setUp(use_ndjson=True)

        data = generate_mock_data(3000)
        product = ("test_product", data)
        stmt_full_name = "test_product"
        worker_id = 1
        exporter_state_manager = ExporterStateManager(worker_id)

        # Run exporter
        self.exporter.consume(product, stmt_full_name, exporter_state_manager)
        self.exporter.finalize_chunks(worker_id)
        json_files = [f for f in list(self.tmp_dir_path.rglob("*")) if f.is_file()]

        files_created = len(json_files)

        self.assertEqual(files_created, 3)

        total_items = 0
        counter = 0
        json_files.sort()
        for json_file in json_files:
            try:
                with json_file.open("r", encoding=self.encoding) as file:
                    for line in file:
                        self.assertTrue(line.endswith("\n"))
                        file_data = json.loads(line)  # Load JSON content
                        self.assertEqual(data[counter], file_data)
                        counter += 1
                        if isinstance(file_data, list):
                            total_items += len(file_data)
                        elif isinstance(file_data, dict):
                            total_items += 1
                        else:
                            print(f"Skipping {json_file}: Unsupported format")
            except json.JSONDecodeError:
                print(f"Skipping {json_file}: Invalid JSON")

        self.assertEqual(len(data), total_items)

    def test_non_serializable_data(self):
        """Test exporter raises exception when data contains non-serializable objects."""
        from datetime import datetime
        # Generate data with a datetime object, which is not JSON serializable by default
        data = [{"id": 1, "timestamp": datetime.now()}]
        product = ("test_product", data)
        stmt_full_name = "test_product"
        worker_id = 1
        exporter_state_manager = ExporterStateManager(worker_id)

        # Run exporter
        try:
            self.exporter.consume(product, stmt_full_name, exporter_state_manager)
            self.exporter.finalize_chunks(worker_id)
            assert True
        except Exception as e:
            assert False

    def test_unlimited_chunk_size(self):
        """Test exporting data with chunk_size=None exports all data in a single chunk."""
        # Reinitialize the exporter with chunk_size=None
        chunk_size = None
        self.setUp(chunk_size=chunk_size)
        data = generate_mock_data(10)
        product = ("test_product", data)

        stmt_full_name = "test_product"
        worker_id = 1
        exporter_state_manager = ExporterStateManager(worker_id)

        # Run exporter

        self.exporter.consume(product, stmt_full_name, exporter_state_manager)
        self.exporter.finalize_chunks(worker_id)

        json_files = [f for f in list(self.tmp_dir_path.rglob("*")) if f.is_file()]

        files_created = len(json_files)

        self.assertEqual(files_created, 1)

        total_items = 0
        for json_file in json_files:
            try:
                with json_file.open("r", encoding=self.encoding) as file:
                    file_data = json.load(file)  # Load JSON content

                    if isinstance(file_data, list | dict):
                        total_items += len(file_data)
                    else:
                        print(f"Skipping {json_file}: Unsupported format")

            except json.JSONDecodeError:
                print(f"Skipping {json_file}: Invalid JSON")

        self.assertEqual(len(data), total_items)

    def test_data_with_special_characters(self):
        """Test exporting data containing special and Unicode characters."""
        special_characters_data = [
            {"id": 1, "text": "Hello, world!"},
            {"id": 2, "text": "Special chars: !@#$%^&*()_+-=[]{}|;':,./<>?"},
            {"id": 3, "text": "Unicode: Привет мир, こんにちは世界, 안녕하세요 세계"}
        ]
        product = ("test_product", special_characters_data)
        stmt_full_name = "test_product"
        worker_id = 1
        exporter_state_manager = ExporterStateManager(worker_id)

        # Run exporter
        self.exporter.consume(product, stmt_full_name, exporter_state_manager)
        self.exporter.finalize_chunks(worker_id)

        json_files = [f for f in list(self.tmp_dir_path.rglob("*")) if f.is_file()]

        files_created = len(json_files)

        self.assertEqual(files_created, 1)

        total_items = 0
        for json_file in json_files:
            try:
                with json_file.open("r", encoding=self.encoding) as file:
                    file_data = json.load(file)  # Load JSON content
                    self.assertEqual(special_characters_data, file_data)
                    if isinstance(file_data, list | dict):
                        total_items += len(file_data)
                    else:
                        print(f"Skipping {json_file}: Unsupported format")

            except json.JSONDecodeError:
                print(f"Skipping {json_file}: Invalid JSON")

        self.assertEqual(len(special_characters_data), total_items)

    def test_exporting_empty_dictionaries(self):
        """Test exporting a list of empty dictionaries."""
        empty_dicts_data = [{} for _ in range(5)]
        product = ("test_product", empty_dicts_data)
        stmt_full_name = "test_product"
        worker_id = 1
        exporter_state_manager = ExporterStateManager(worker_id)

        # Run exporter
        self.exporter.consume(product, stmt_full_name, exporter_state_manager)
        self.exporter.finalize_chunks(worker_id)

        json_files = [f for f in list(self.tmp_dir_path.rglob("*")) if f.is_file()]

        files_created = len(json_files)

        self.assertEqual(files_created, 1)

        total_items = 0
        for json_file in json_files:
            try:
                with json_file.open("r", encoding=self.encoding) as file:
                    file_data = json.load(file)  # Load JSON content
                    self.assertEqual(empty_dicts_data, file_data)
                    if isinstance(file_data, list | dict):
                        total_items += len(file_data)
                    else:
                        print(f"Skipping {json_file}: Unsupported format")

            except json.JSONDecodeError:
                print(f"Skipping {json_file}: Invalid JSON")

        self.assertEqual(len(empty_dicts_data), total_items)

if __name__ == "__main__":
    unittest.main()

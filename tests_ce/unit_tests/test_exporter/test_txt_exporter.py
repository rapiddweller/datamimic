import tempfile
import unittest
import uuid
from pathlib import Path

from datamimic_ce.exporters.exporter_state_manager import ExporterStateManager
from datamimic_ce.exporters.txt_exporter import TXTExporter
from tests_ce.unit_tests.test_exporter.exporter_test_util import MockSetupContext, generate_mock_data


class TestTXTExporter(unittest.TestCase):
    def setUp(self, encoding='utf-8', separator=None, line_terminator=None, chunk_size=1000):
        """Set up test fixtures."""
        self.setup_context = MockSetupContext(task_id=f"test_task_{uuid.uuid4().hex}", descriptor_dir="test_dir")
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp_dir_path = Path(self.tmp_dir.name)
        self.setup_context.descriptor_dir = self.tmp_dir_path
        self.setup_context.properties = {}

        self.product_name = "test_product"
        self.chunk_size = chunk_size
        self.separator = separator
        self.line_terminator = line_terminator
        self.encoding = encoding

        self.exporter = TXTExporter(
            setup_context=self.setup_context,
            product_name=self.product_name,
            chunk_size=self.chunk_size,
            separator=self.separator,
            line_terminator=self.line_terminator,
            encoding=self.encoding,
        )

    def tearDown(self):
        """Clean up temporary directories."""
        self.tmp_dir.cleanup()

    def test_single_process_chunking(self):
        """Test the number of chunk files created and total records exported."""
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
        txt_files = [f for f in list(self.tmp_dir_path.rglob("*")) if f.is_file()]

        # Verify the number of chunk files created
        chunk_files_created = len(txt_files)
        self.assertEqual(chunk_files_created, expected_chunks)

        # Verify the total number of records written
        actual_write_calls = 0
        out_data = []
        txt_files.sort()

        for txt_file in txt_files:
            with txt_file.open("r", encoding=self.encoding) as file:
                file_data = file.read()
                lines = file_data.split("\n")
                # Remove the last empty element if split by terminator
                if lines and not lines[-1]:
                    lines.pop()
                self.assertEqual(len(lines), 1000)
                actual_write_calls += len(lines)
                out_data.extend(lines)

        self.assertEqual(actual_write_calls, len(data))
        # Verify TXT content
        for record, out in zip(data, out_data, strict=False):
            expected_line = f"test_product: {record}"
            self.assertEqual(out, expected_line)

    def test_export_with_different_line_terminators(self):
        """Test exporting data with different line terminator settings."""
        terminators = ["@@@@@@", "&&&&&", "YYYYYY", "!@##$%$^%^%^", "--__--"]
        for terminator in terminators:
            data = generate_mock_data(3000)
            product = ("test_product", data)
            stmt_full_name = "test_product"
            worker_id = 1
            exporter_state_manager = ExporterStateManager(worker_id)
            expected_chunks = 3  # 3000 data / 1000 chunk_size = 3

            self.setUp(line_terminator=terminator)
            # Run exporter
            self.exporter.consume(product, stmt_full_name, exporter_state_manager)
            self.exporter.finalize_chunks(worker_id)
            txt_files = [f for f in list(self.tmp_dir_path.rglob("*")) if f.is_file()]

            # Verify the number of chunk files created
            chunk_files_created = len(txt_files)
            self.assertEqual(chunk_files_created, expected_chunks)

            # Verify the total number of records written
            actual_write_calls = 0
            out_data = []
            txt_files.sort()

            for txt_file in txt_files:
                with txt_file.open("r", encoding=self.encoding) as file:
                    file_data = file.read()
                    lines = file_data.split(terminator)
                    # Remove the last empty element if split by terminator
                    if lines and not lines[-1]:
                        lines.pop()
                    self.assertEqual(len(lines), 1000)
                    actual_write_calls += len(lines)
                    out_data.extend(lines)

            self.assertEqual(actual_write_calls, len(data))
            # Verify TXT content
            for record, out in zip(data, out_data, strict=False):
                expected_line = f"test_product: {record}"
                self.assertEqual(out, expected_line)

            # clear previous files
            self.tmp_dir.cleanup()

    def test_custom_separator_and_encoding(self):
        """Test exporting with custom separator and encoding."""
        self.setUp(encoding='utf-16', separator='|')

        original_data = generate_mock_data(10)
        product = ("test_product", original_data)
        stmt_full_name = "test_product"
        worker_id = 1
        exporter_state_manager = ExporterStateManager(worker_id)

        # Run exporter
        self.exporter.consume(product, stmt_full_name, exporter_state_manager)
        self.exporter.finalize_chunks(worker_id)
        txt_files = [f for f in list(self.tmp_dir_path.rglob("*")) if f.is_file()]

        # Verify the number of chunk files created
        chunk_files_created = len(txt_files)
        self.assertEqual(1, chunk_files_created)

        written_content = []
        expected_content = []
        txt_files.sort()

        for txt_file in txt_files:
            with txt_file.open("r", encoding=self.encoding) as file:
                file_data = file.read()
                lines = file_data.split("\n")
                if lines and not lines[-1]:
                    lines.pop()
                written_content.extend(lines)

        for field in original_data:
            expected_content.append(f"test_product: {field}")
        self.assertEqual(expected_content, written_content)

    def test_special_characters_in_data(self):
        """Test exporting data containing separators, quotes, and newlines."""
        # Change exporter setup
        self.setUp(encoding='utf-16', separator='|')

        # Simulate data export
        data = [
            {"id": "1", "title": 'Title with | pipe', "year": 2020},
            {"id": "2", "title": 'Title with "quote"', "year": 2021},
            {"id": "3", "title": 'Title with \n newline', "year": 2022},
            {"id": "4", "title": 'Title with separator|semicolon', "year": 2023},
        ]

        product = ("test_product", data)
        stmt_full_name = "test_product"
        worker_id = 1
        exporter_state_manager = ExporterStateManager(worker_id)

        # Execute the export
        self.exporter.consume(product, stmt_full_name, exporter_state_manager)
        self.exporter.finalize_chunks(worker_id)
        txt_files = [f for f in list(self.tmp_dir_path.rglob("*")) if f.is_file()]

        written_content = ""
        txt_files.sort()

        for txt_file in txt_files:
            with txt_file.open("r", encoding=self.encoding) as file:
                file_data = file.read()
                written_content = written_content.join(file_data)

        # Expected content with the separator applied
        expected_content = ("test_product: {'id': '1', 'title': 'Title with | pipe', 'year': 2020}\n"
                            'test_product: {\'id\': \'2\', \'title\': \'Title with "quote"\', \'year\': 2021}\n'
                            "test_product: {'id': '3', 'title': 'Title with \\n newline', 'year': 2022}\n"
                            "test_product: {'id': '4', 'title': 'Title with separator|semicolon', 'year': 2023}\n")

        # Assert that the content written to the file matches the expected content
        self.assertEqual(expected_content, written_content)

    def test_large_dataset(self):
        """Test the number of chunk files created and total records exported."""
        # Test data
        self.setUp(chunk_size=100_000)
        data = generate_mock_data(500_000)
        product = ("test_product", data)
        stmt_full_name = "test_product"
        worker_id = 1
        exporter_state_manager = ExporterStateManager(worker_id)
        expected_chunks = 5  # 500_000 data / 100_000 chunk_size = 5

        # Run exporter
        self.exporter.consume(product, stmt_full_name, exporter_state_manager)
        self.exporter.finalize_chunks(worker_id)
        txt_files = [f for f in list(self.tmp_dir_path.rglob("*")) if f.is_file()]

        # Verify the number of chunk files created
        chunk_files_created = len(txt_files)
        self.assertEqual(chunk_files_created, expected_chunks)

        # Verify the total number of records written
        actual_write_calls = 0
        out_data = []
        txt_files.sort()

        for txt_file in txt_files:
            with txt_file.open("r", encoding=self.encoding) as file:
                file_data = file.read()
                lines = file_data.split("\n")
                # Remove the last empty element if split by terminator
                if lines and not lines[-1]:
                    lines.pop()
                self.assertEqual(len(lines), 100_000)
                actual_write_calls += len(lines)
                out_data.extend(lines)

        self.assertEqual(actual_write_calls, len(data))
        # Verify TXT content
        for record, out in zip(data, out_data, strict=False):
            expected_line = f"test_product: {record}"
            self.assertEqual(out, expected_line)

    def test_invalid_data_handling(self):
        """Test exporting data with invalid data types."""
        invalid_data = [
            {"id": "1", "title": "Valid Title", "year": 2020},
            {"id": "2", "title": "Another Title", "year": None},  # 'year' as None
            {"id": "3", "title": "Title with | separator", "year": "Invalid Year"},  # 'year' as str
        ]
        product = ("test_product", invalid_data)
        stmt_full_name = "test_product"
        worker_id = 1
        exporter_state_manager = ExporterStateManager(worker_id)

        # Run exporter
        self.exporter.consume(product, stmt_full_name, exporter_state_manager)
        self.exporter.finalize_chunks(worker_id)
        txt_files = [f for f in list(self.tmp_dir_path.rglob("*")) if f.is_file()]

        # Verify the number of chunk files created
        chunk_files_created = len(txt_files)
        self.assertEqual(1, chunk_files_created)

        written_content = []
        expected_content = []
        txt_files.sort()

        for txt_file in txt_files:
            with txt_file.open("r", encoding=self.encoding) as file:
                file_data = file.read()
                lines = file_data.split("\n")
                if lines and not lines[-1]:
                    lines.pop()
                written_content.extend(lines)

        for field in invalid_data:
            expected_content.append(f"test_product: {field}")
        self.assertEqual(expected_content, written_content)

    def test_empty_records_and_missing_fields(self):
        """Test exporting data with empty records and missing fields."""
        data_with_missing_fields = [
            {"id": "1", "title": "Title 1", "year": 2020},
            {"id": "2", "title": "Title 2"},  # Missing 'year'
            {},  # Empty record
            {"id": "3", "year": 2022},  # Missing 'title'
        ]
        product = ("test_product", data_with_missing_fields)
        stmt_full_name = "test_product"
        worker_id = 1
        exporter_state_manager = ExporterStateManager(worker_id)

        # Run exporter
        self.exporter.consume(product, stmt_full_name, exporter_state_manager)
        self.exporter.finalize_chunks(worker_id)
        txt_files = [f for f in list(self.tmp_dir_path.rglob("*")) if f.is_file()]

        # Verify the number of chunk files created
        chunk_files_created = len(txt_files)
        self.assertEqual(1, chunk_files_created)

        written_content = []
        expected_content = []
        txt_files.sort()

        for txt_file in txt_files:
            with txt_file.open("r", encoding=self.encoding) as file:
                file_data = file.read()
                lines = file_data.split("\n")
                if lines and not lines[-1]:
                    lines.pop()
                written_content.extend(lines)

        for field in data_with_missing_fields:
            expected_content.append(f"test_product: {field}")
        self.assertEqual(expected_content, written_content)

    def test_consume_invalid_product(self):
        """Test that consuming an invalid product raises ValueError."""
        stmt_full_name = "test_product"
        exporter_state_manager = ExporterStateManager(1)
        with self.assertRaises(ValueError):
            self.exporter.consume("invalid_product", stmt_full_name, exporter_state_manager)

    def test_no_name_provided(self):
        """Test exporting when the product name is not provided."""
        # Modify consume method to handle missing name appropriately
        # Since the current consume method expects a tuple with (name, data), this test ensures proper error handling
        stmt_full_name = "test_product"
        worker_id = 1
        exporter_state_manager = ExporterStateManager(worker_id)
        with self.assertRaises(ValueError):
            self.exporter.consume((None, generate_mock_data(10)), stmt_full_name, exporter_state_manager)

    def test_export_with_custom_line_terminator(self):
        """Test exporting data with a custom line terminator."""
        self.setUp(line_terminator="|")
        data = generate_mock_data(5)
        product = ("test_product", data)
        stmt_full_name = "test_product"
        worker_id = 1
        exporter_state_manager = ExporterStateManager(worker_id)

        self.exporter.consume(product, stmt_full_name, exporter_state_manager)
        self.exporter.finalize_chunks(worker_id)
        txt_files = [f for f in list(self.setup_context.descriptor_dir.rglob("*")) if f.is_file()]
        self.assertEqual(len(txt_files), 1)

        for txt_file in txt_files:
            with txt_file.open("r", encoding=self.encoding) as file:
                file_data = file.read()
                # Split using custom line terminator
                lines = file_data.split('|')
                # Remove the last empty element if split by terminator
                if lines and not lines[-1]:
                    lines.pop()
                self.assertEqual(len(lines), 5)
                # Verify TXT content
                for record, line in zip(data, lines, strict=False):
                    expected_line = f"test_product: {record}"
                    self.assertEqual(line, expected_line)

    def test_export_empty_data_list(self):
        """Test exporting when data list is empty."""
        product = ("test_product", [])
        stmt_full_name = "test_product"
        worker_id = 1
        exporter_state_manager = ExporterStateManager(worker_id)

        self.exporter.consume(product, stmt_full_name, exporter_state_manager)
        self.exporter.finalize_chunks(worker_id)
        # Should not write any files
        txt_files = [f for f in list(self.tmp_dir_path.rglob("*")) if f.is_file()]
        self.assertEqual(len(txt_files), 0)


if __name__ == "__main__":
    unittest.main()

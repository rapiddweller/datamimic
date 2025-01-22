import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from datamimic_ce.contexts.setup_context import SetupContext
from datamimic_ce.exporters.exporter_state_manager import ExporterStateManager
from datamimic_ce.exporters.txt_exporter import TXTExporter
from unittest.mock import mock_open, patch
import tempfile
import os


def generate_mock_data(total_records=3000, title="Mock Title", year=2020):
    """Generate mock data for testing."""
    return [{"id": f"movie_{i + 1}", "title": f"{title} {i + 1}", "year": year} for i in range(total_records)]


class TestTXTExporter(unittest.TestCase):
    def setUp(self, encoding='utf-8', separator=None, line_terminator=None, chunk_size=1000):
        """Set up test fixtures."""
        self.setup_context = MagicMock(spec=SetupContext)
        self.setup_context.default_separator = ":"
        self.setup_context.default_line_separator = "\n"
        self.setup_context.default_encoding = "utf-8"
        self.setup_context.use_mp = False
        self.setup_context.task_id = "test_task"
        self.setup_context.descriptor_dir = Path("/tmp/test_descriptor")

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

    @patch("pathlib.Path.open", create=True)
    @patch("pathlib.Path.glob")
    def test_single_process_chunking(self, mock_glob, mock_open):
        """Test the number of chunk files created and total records exported."""
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file

        # Test data
        data = generate_mock_data(3000)
        product = ("test_product", data)
        stmt_full_name = "test_product"
        worker_id = 1
        exporter_state_manager = ExporterStateManager(worker_id)

        expected_chunks = 3  # 3000 data / 1000 chunk_size = 3

        # Dynamically create mock buffer files
        buffer_files = [
            Path(f"/tmp/buffer_{worker_id}_chunk_{i}.txt") for i in range(expected_chunks)
        ]
        mock_glob.return_value = buffer_files

        with patch.object(self.exporter, "_get_buffer_file", side_effect=lambda w, c: buffer_files[c]):
            self.exporter.consume(product, stmt_full_name, exporter_state_manager)
            self.exporter.finalize_chunks(worker_id)

        # Verify the number of chunk files created
        chunk_files_created = len(buffer_files)
        self.assertEqual(chunk_files_created, expected_chunks)

        # Verify the total number of records written
        expected_total_records = len(data)
        actual_write_calls = mock_file.write.call_count
        self.assertEqual(actual_write_calls, expected_total_records)

        # Verify the content of the write calls
        expected_calls = [
            f"{self.exporter.product_name}: {record}{self.exporter.line_terminator}"
            for record in data
        ]
        for call in expected_calls:
            mock_file.write.assert_any_call(call)

    @patch("pathlib.Path.open", create=True)
    @patch("pathlib.Path.glob")
    def test_export_with_different_line_terminators(self, mock_glob, mock_open):
        """Test exporting data with different line terminator settings."""
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file

        # Test data
        data = generate_mock_data(3000)
        expected_chunks = 3  # 3000 data / 1000 chunk_size = 3

        product = ("test_product", data)
        stmt_full_name = "test_product"
        worker_id = 1
        exporter_state_manager = ExporterStateManager(worker_id)

        # Test with different line terminators
        terminators = ["\n", "\r\n", "\r"]
        for terminator in terminators:
            with self.subTest(line_terminator=terminator):
                self.exporter.line_terminator = terminator

                # Dynamically create mock buffer files
                buffer_files = [
                    Path(f"/tmp/buffer_{worker_id}_chunk_{i}.txt") for i in range(expected_chunks)
                ]
                mock_glob.return_value = buffer_files

                with patch.object(self.exporter, "_get_buffer_file", side_effect=lambda w, c: buffer_files[c]):
                    # Call consume and finalize
                    self.exporter.consume(product, stmt_full_name, exporter_state_manager)
                    self.exporter.finalize_chunks(worker_id)

                # Retrieve the written content from the mocked file
                written_content = "".join(
                    call.args[0] for call in mock_file.write.call_args_list
                )

                # Verify the content matches the expected format
                expected_content = "".join(
                    f"{self.exporter.product_name}: {record}{terminator}" for record in data
                )
                self.assertEqual(written_content, expected_content)

                # Reset mock for the next iteration
                mock_file.write.reset_mock()

    @patch("pathlib.Path.open", create=True)
    def test_special_characters_in_data(self, mock_open):
        """Test exporting data containing separators, quotes, and newlines."""
        # Mock the file object
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file

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
        stmt_full_name = "test_stmt"
        worker_id = 1
        exporter_state_manager = ExporterStateManager(worker_id)

        # Execute the export
        self.exporter.consume(product, stmt_full_name, exporter_state_manager)
        self.exporter.finalize_chunks(worker_id)

        # Extract the written content
        written_content = "".join(call.args[0] for call in mock_file.write.call_args_list)

        # Expected content with the separator applied
        expected_content = ("test_product: {'id': '1', 'title': 'Title with | pipe', 'year': 2020}\n"
                            'test_product: {\'id\': \'2\', \'title\': \'Title with "quote"\', \'year\': 2021}\n'
                            "test_product: {'id': '3', 'title': 'Title with \\n newline', 'year': 2022}\n"
                            "test_product: {'id': '4', 'title': 'Title with separator|semicolon', 'year': 2023}\n")

        # Assert that the content written to the file matches the expected content
        self.assertEqual(expected_content, written_content)


    @patch("pathlib.Path.open", create=True)
    @patch("pathlib.Path.glob")
    def test_large_dataset(self, mock_glob, mock_open):
        """Test the number of chunk files created and total records exported."""
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file

        # Test data
        data = generate_mock_data(500_000)
        self.setUp(chunk_size=100_000)
        product = ("test_product", data)
        stmt_full_name = "test_product"
        worker_id = 1
        exporter_state_manager = ExporterStateManager(worker_id)

        expected_chunks = 5  # 500_000 data / 100_000 chunk_size = 5

        # Dynamically create mock buffer files
        buffer_files = [
            Path(f"/tmp/buffer_{worker_id}_chunk_{i}.txt") for i in range(expected_chunks)
        ]
        mock_glob.return_value = buffer_files

        with patch.object(self.exporter, "_get_buffer_file", side_effect=lambda w, c: buffer_files[c]):
            self.exporter.consume(product, stmt_full_name, exporter_state_manager)
            self.exporter.finalize_chunks(worker_id)

        # Verify the number of chunk files created
        chunk_files_created = len(buffer_files)
        self.assertEqual(chunk_files_created, expected_chunks)

        # Verify the total number of records written
        expected_total_records = len(data)
        actual_write_calls = mock_file.write.call_count
        self.assertEqual(actual_write_calls, expected_total_records)

    def test_invalid_data_handling(self):
        """Test exporting data with invalid data types."""
        pass

    def test_empty_records_and_missing_fields(self):
        """Test exporting data with empty records and missing fields."""
        pass

    def test_no_name_provided(self):
        """Test exporting when the product name is not provided."""
        # Modify consume method to handle missing name appropriately
        # Since the current consume method expects a tuple with (name, data), this test ensures proper error handling
        stmt_full_name = "test_product"
        worker_id = 1
        exporter_state_manager = ExporterStateManager(worker_id)
        with self.assertRaises(ValueError):
            self.exporter.consume((None, generate_mock_data(10)), stmt_full_name, exporter_state_manager)


if __name__ == "__main__":
    unittest.main()

import csv
import tempfile
import unittest
import uuid
from pathlib import Path

from datamimic_ce.exporters.csv_exporter import CSVExporter
from datamimic_ce.exporters.exporter_state_manager import ExporterStateManager
from tests_ce.unit_tests.test_exporter.exporter_test_util import MockSetupContext, generate_mock_data


class TestCSVExporter(unittest.TestCase):
    def setUp(self, encoding="utf-8", delimiter=None, quotechar=None, quoting=None, line_terminator=None):
        """Set up for each test."""
        self.setup_context = MockSetupContext(task_id="test_task", descriptor_dir="test_dir")
        self.setup_context.task_id = f"test_task_{uuid.uuid4().hex}"
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp_dir_path = Path(self.tmp_dir.name)
        self.setup_context.descriptor_dir = self.tmp_dir_path
        self.setup_context.properties = {}
        self.exporter = CSVExporter(
            setup_context=self.setup_context,
            product_name="test_product",
            chunk_size=1000,
            delimiter=delimiter,
            quotechar=quotechar,
            quoting=quoting,
            line_terminator=line_terminator,
            fieldnames=None,
            encoding=encoding,
        )

    def tearDown(self):
        """Clean up temporary directories."""
        self.tmp_dir.cleanup()

    def test_single_process_chunking(self):
        """Test exporting 3000 records with chunk size 1000 in a single process (3 chunk files expected)."""
        original_data = generate_mock_data(3000)
        product = ("test_product", original_data)
        stmt_full_name = "test_product"
        worker_id = 1
        exporter_state_manager = ExporterStateManager(worker_id)
        self.exporter.consume(product, stmt_full_name, exporter_state_manager)
        self.exporter.finalize_chunks(worker_id)

    def test_custom_delimiter_and_encoding(self):
        """Test exporting with custom delimiter and encoding."""

        self.setUp(encoding="utf-16", delimiter=";")

        original_data = generate_mock_data(10)
        product = ("test_product", original_data)

        stmt_full_name = "test_product"
        worker_id = 1
        exporter_state_manager = ExporterStateManager(worker_id)

        self.exporter.consume(product, stmt_full_name, exporter_state_manager)
        self.exporter.finalize_chunks(worker_id)

    def test_special_characters_in_data(self):
        """Test exporting data containing delimiters, quotes, and newlines."""

        self.setUp(quoting=csv.QUOTE_ALL, delimiter=";")

        special_data = [
            {"id": "1", "title": "Title with, comma", "year": 2020},
            {"id": "2", "title": 'Title with "quote"', "year": 2021},
            {"id": "3", "title": "Title with \n newline", "year": 2022},
            {"id": "4", "title": "Title with delimiter; semicolon", "year": 2023},
        ]
        product = ("test_product", special_data)

        stmt_full_name = "test_product"
        worker_id = 1
        exporter_state_manager = ExporterStateManager(worker_id)

        self.exporter.consume(product, stmt_full_name, exporter_state_manager)
        self.exporter.finalize_chunks(worker_id)

    def test_large_dataset(self):
        """Test exporting a very large dataset to check performance and memory usage."""
        total_records = 500_000  # Half a million records
        self.exporter = CSVExporter(
            setup_context=self.setup_context,
            product_name="test_product",
            chunk_size=100_000,
            delimiter=None,
            quotechar=None,
            quoting=None,
            line_terminator=None,
            fieldnames=None,
            encoding="utf-8",
        )

        original_data = generate_mock_data(total_records)
        product = ("test_product", original_data)

        stmt_full_name = "test_product"
        worker_id = 1
        exporter_state_manager = ExporterStateManager(worker_id)

        self.exporter.consume(product, stmt_full_name, exporter_state_manager)
        self.exporter.finalize_chunks(worker_id)

    def test_invalid_data_handling(self):
        """Test exporting data with invalid data types."""
        invalid_data = [
            {"id": "1", "title": "Valid Title", "year": 2020},
            {"id": "2", "title": "Another Title", "year": "Invalid Year"},  # Year should be an int
        ]
        product = ("test_product", invalid_data)

        stmt_full_name = "test_product"
        worker_id = 1
        exporter_state_manager = ExporterStateManager(worker_id)

        self.exporter.consume(product, stmt_full_name, exporter_state_manager)
        self.exporter.finalize_chunks(worker_id)

    # @unittest.skipIf(os.name == "posix", "Skipping multiprocessing test on Linux")
    # def test_multiprocessing_export(self):
    #     total_processes = os.cpu_count() or 1
    #     total_records_per_process = 5000
    #     data = generate_mock_data(total_records_per_process * total_processes)
    #     data_chunks = [
    #         data[i * total_records_per_process : (i + 1) * total_records_per_process] for i in range(total_processes)
    #     ]
    #
    #     manager = multiprocessing.Manager()
    #     shared_storage_list = manager.list()
    #     processes = []
    #     for chunk in data_chunks:
    #         p = multiprocessing.Process(
    #             target=worker,
    #             args=(
    #                 chunk,
    #                 shared_storage_list,
    #                 self.setup_context.task_id,
    #                 self.setup_context.descriptor_dir,
    #                 self.setup_context.properties,
    #             ),
    #         )
    #         p.start()
    #         processes.append(p)
    #     for p in processes:
    #         p.join()

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

        self.exporter.fieldnames = ["id", "title", "year"]  # Specify fieldnames to handle missing fields
        self.exporter.consume(product, stmt_full_name, exporter_state_manager)
        self.exporter.finalize_chunks(worker_id)

    def test_product_with_type(self):
        """Test exporting data with product type."""
        data = generate_mock_data(5)
        product = ("test_product", data, {"type": "test_type"})
        stmt_full_name = "test_product"
        worker_id = 1
        exporter_state_manager = ExporterStateManager(worker_id)

        self.exporter.consume(product, stmt_full_name, exporter_state_manager)
        self.exporter.finalize_chunks(worker_id)

    def test_consume_invalid_product(self):
        """Test that consuming an invalid product raises ValueError."""
        stmt_full_name = "test_product"
        worker_id = 1
        exporter_state_manager = ExporterStateManager(worker_id)

        with self.assertRaises(ValueError):
            self.exporter.consume("invalid_product", stmt_full_name, exporter_state_manager)

    def test_chunk_rotation_without_remainder(self):
        """Test exporting data where total records are a multiple of chunk size."""
        total_records = 5000
        self.exporter = CSVExporter(
            setup_context=self.setup_context,
            product_name="test_product",
            chunk_size=1000,
            delimiter=None,
            quotechar=None,
            quoting=None,
            line_terminator=None,
            fieldnames=None,
            encoding="utf-8",
        )

        original_data = generate_mock_data(total_records)
        product = ("test_product", original_data)
        stmt_full_name = "test_product"
        worker_id = 1
        exporter_state_manager = ExporterStateManager(worker_id)

        self.exporter.consume(product, stmt_full_name, exporter_state_manager)
        self.exporter.finalize_chunks(worker_id)

    def test_chunk_rotation_with_remainder(self):
        """Test exporting data where total records are not a multiple of chunk size."""
        total_records = 5500
        self.exporter = CSVExporter(
            setup_context=self.setup_context,
            product_name="test_product",
            chunk_size=1000,
            delimiter=None,
            quotechar=None,
            quoting=None,
            line_terminator=None,
            fieldnames=None,
            encoding="utf-8",
        )

        original_data = generate_mock_data(total_records)
        product = ("test_product", original_data)
        stmt_full_name = "test_product"
        worker_id = 1
        exporter_state_manager = ExporterStateManager(worker_id)

        self.exporter.consume(product, stmt_full_name, exporter_state_manager)
        self.exporter.finalize_chunks(worker_id)

    def test_no_fieldnames_provided(self):
        """Test exporting when fieldnames are not provided and need to be inferred."""
        data = [
            {"id": "1", "title": "Title 1", "year": 2020},
            {"id": "2", "title": "Title 2", "year": 2021},
        ]
        self.exporter.fieldnames = None  # Ensure fieldnames are not set
        product = ("test_product", data)
        stmt_full_name = "test_product"
        worker_id = 1
        exporter_state_manager = ExporterStateManager(worker_id)

        self.exporter.consume(product, stmt_full_name, exporter_state_manager)
        self.assertEqual(self.exporter.fieldnames, ["id", "title", "year"])  # Fieldnames inferred
        self.exporter.finalize_chunks(worker_id)

    def test_export_with_custom_quotechar(self):
        """Test exporting data with a custom quote character."""
        self.setup_context.properties = {"quotechar": "'", "quoting": csv.QUOTE_ALL}
        self.exporter = CSVExporter(
            setup_context=self.setup_context,
            product_name="test_product",
            chunk_size=1000,
            delimiter=None,
            quotechar=None,
            quoting=None,
            line_terminator=None,
            fieldnames=None,
            encoding=None,
        )

        data = generate_mock_data(5)
        product = ("test_product", data)
        stmt_full_name = "test_product"
        worker_id = 1
        exporter_state_manager = ExporterStateManager(worker_id)

        self.exporter.consume(product, stmt_full_name, exporter_state_manager)
        self.exporter.finalize_chunks(worker_id)

    def test_export_with_different_quoting_options(self):
        """Test exporting data with different quoting options."""
        for quoting_option in [csv.QUOTE_MINIMAL, csv.QUOTE_NONNUMERIC, csv.QUOTE_NONE]:
            self.setUp(quoting=quoting_option)

            data = generate_mock_data(5)
            product = ("test_product", data)
            stmt_full_name = "test_product"
            worker_id = 1
            exporter_state_manager = ExporterStateManager(worker_id)

            self.exporter.consume(product, stmt_full_name, exporter_state_manager)
            self.exporter.finalize_chunks(worker_id)

    def test_export_with_custom_encoding(self):
        """Test exporting data with a custom encoding."""
        self.setUp(encoding="utf-16")

        data = generate_mock_data(10)
        product = ("test_product", data)
        stmt_full_name = "test_product"
        worker_id = 1
        exporter_state_manager = ExporterStateManager(worker_id)

        self.exporter.consume(product, stmt_full_name, exporter_state_manager)
        self.exporter.finalize_chunks(worker_id)

    def test_export_empty_data_list(self):
        """Test exporting when data list is empty."""
        product = ("test_product", [])
        stmt_full_name = "test_product"
        worker_id = 1
        exporter_state_manager = ExporterStateManager(worker_id)

        self.exporter.consume(product, stmt_full_name, exporter_state_manager)
        self.exporter.finalize_chunks(worker_id)


if __name__ == "__main__":
    unittest.main()

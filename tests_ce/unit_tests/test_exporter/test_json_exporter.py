# import json
# import multiprocessing
# import os
# import re
# import tempfile
# import unittest
# import uuid
# from pathlib import Path
# from unittest.mock import MagicMock
#
# from datamimic_ce.exporters.json_exporter import JsonExporter
#
#
# def worker(data_chunk, setup_context, storage_list, chunk_size):
#     """Worker function for multiprocessing."""
#     exporter = JsonExporter(
#         setup_context=setup_context,
#         product_name="test_product",
#         storage_id="minio",
#         target_uri="test_path",
#         use_ndjson=False,
#         chunk_size=chunk_size
#     )
#     exporter._storage = StorageMock(storage_list)
#     exporter.consume(("test_product", data_chunk))
#     exporter.finalize_chunks()
#
#
# def generate_mock_data(total_records=3000, title="Test Title", year=2021):
#     """Generate mock JSON data for testing."""
#     return [{"title": title, "year": year, "id": f"item_{i}"} for i in range(total_records)]
#
#
# class MockSetupContext:
#     def __init__(self, task_id, descriptor_dir):
#         self.task_id = task_id
#         self.descriptor_dir = descriptor_dir
#         self.default_separator = ","
#         self.default_line_separator = "\n"
#         self.default_encoding = "utf-8"
#         self.use_mp = False
#
#     def get_client_by_id(self, client_id):
#         # Return a dummy client or data, replace MagicMock dependency
#         return {"id": client_id, "data": "mock_client_data"}
#
# class TestJsonExporter(unittest.TestCase):
#     def setUp(self):
#         self.task_id = f"test_task_{uuid.uuid4().hex}"
#         self.tmp_dir = tempfile.TemporaryDirectory()
#         self.tmp_dir_path = Path(self.tmp_dir.name)
#
#         self.setup_context = MockSetupContext(
#             task_id=self.task_id,
#             descriptor_dir=self.tmp_dir_path
#
#         )
#
#         self.storage = MagicMock()
#         self.exporter = JsonExporter(
#             setup_context=self.setup_context,
#             product_name="test_product",
#             use_ndjson=False,
#             chunk_size=1000
#         )
#         self.exporter._storage = self.storage
#
#     def tearDown(self):
#         """Clean up the test directory and reset mocks."""
#         self.tmp_dir.cleanup()
#         self.storage.reset_mock()
#         # self.exporter.reset_instance()
#
#     def test_single_process_chunking(self):
#         """Test exporting 3000 records with chunk size 1000 in a single process (3 chunk files expected)."""
#         product = ("test_product", generate_mock_data(3000))
#         self.exporter.consume(product)
#         self.exporter.finalize_chunks()
#         self.exporter.upload_to_storage(bucket="test_bucket", name=self.exporter.product_name)
#         self.assertEqual(self.storage.write.call_count, 3)
#
#         # Verify each call to storage.write
#         total_records_exported = 0
#         for i, call in enumerate(self.storage.write.call_args_list):
#             args, _ = call
#             bucket, uri, data_buffer, content_type = args
#             self.assertEqual(bucket, "test_bucket")
#             self.assertTrue(uri.startswith(f"{self.exporter._task_id}"))
#             self.assertEqual(content_type, "application/json")
#
#             # Read the data buffer
#             data_buffer.seek(0)
#             content = data_buffer.read().decode('utf-8')
#             records = json.loads(content)
#
#             # Verify the number of records in each chunk
#             self.assertEqual(len(records), 1000)
#             total_records_exported += len(records)
#
#             # Optionally, verify the content matches the input data
#             expected_records = product[1][i * 1000:(i + 1) * 1000]
#             self.assertEqual(records, expected_records)
#
#         # Verify total records exported
#         self.assertEqual(total_records_exported, 3000)
#
#     def test_large_data_non_multiple_chunk_size(self):
#         """Test exporting 1,000,001 records with chunk size 100,000 (11 chunks expected)."""
#         total_records = 1_000_001
#         chunk_size = 100_000
#         product = ("test_product", generate_mock_data(total_records))
#         self.exporter.chunk_size = chunk_size
#         self.exporter.consume(product)
#         self.exporter.finalize_chunks()
#         self.exporter.upload_to_storage(bucket="test_bucket", name=self.exporter.product_name)
#         self.assertEqual(self.storage.write.call_count, 11)
#
#         total_records_exported = 0
#         expected_chunk_sizes = [100_000] * 10 + [1]
#         for i, call in enumerate(self.storage.write.call_args_list):
#             args, _ = call
#             bucket, uri, data_buffer, content_type = args
#             self.assertEqual(bucket, "test_bucket")
#             self.assertTrue(uri.startswith(f"{self.exporter._task_id}"))
#             self.assertEqual(content_type, "application/json")
#
#             data_buffer.seek(0)
#             content = data_buffer.read().decode('utf-8')
#             records = json.loads(content)
#
#             # Verify chunk sizes
#             self.assertEqual(len(records), expected_chunk_sizes[i])
#             total_records_exported += len(records)
#
#             # Optionally, verify content
#             start_index = i * chunk_size
#             end_index = start_index + expected_chunk_sizes[i]
#             expected_records = product[1][start_index:end_index]
#             self.assertEqual(records, expected_records)
#
#         self.assertEqual(total_records_exported, total_records)
#
#     def test_zero_records(self):
#         """Test exporting zero records. Expecting no storage writes."""
#         product = ("test_product", [])
#         self.exporter.consume(product)
#         self.exporter.finalize_chunks()
#         self.exporter.upload_to_storage(bucket="test_bucket", name=self.exporter.product_name)
#         self.assertEqual(self.storage.write.call_count, 0)
#
#         # Verify no buffer files were created
#         buffer_files = list(self.tmp_dir_path.glob(f"{self.exporter.product_name}_*.json"))
#         self.assertEqual(len(buffer_files), 0)
#
#     def test_chunk_size_of_one(self):
#         """Test exporting 10 records with chunk size 1. Expecting 10 JSON files."""
#         self.exporter.chunk_size = 1
#         product = ("test_product", generate_mock_data(10))
#         self.exporter.consume(product)
#         self.exporter.finalize_chunks()
#         self.exporter.upload_to_storage(bucket="test_bucket", name=self.exporter.product_name)
#         self.assertEqual(self.storage.write.call_count, 10)
#
#         for i, call in enumerate(self.storage.write.call_args_list):
#             args, _ = call
#             bucket, uri, data_buffer, content_type = args
#             self.assertEqual(bucket, "test_bucket")
#             # self.assertTrue(uri.endswith(f"{i + 1}_pid_.json"))
#             self.assertTrue(re.search(rf"{i + 1}.json$", uri))
#
#             self.assertEqual(content_type, "application/json")
#
#             data_buffer.seek(0)
#             content = data_buffer.read().decode('utf-8')
#             record = json.loads(content)
#
#             # Verify that only one record is in the chunk
#             self.assertIsInstance(record, dict)
#             self.assertEqual(record, product[1][i])
#
#     def test_json_format_output(self):
#         """Test JSON formatting in exported content."""
#         product = ("test_product", generate_mock_data(5))
#         self.exporter.consume(product)
#         self.exporter.finalize_chunks()
#         self.exporter.upload_to_storage(bucket="test_bucket", name=self.exporter.product_name)
#
#         self.assertEqual(self.storage.write.call_count, 1)
#         call = self.storage.write.call_args
#         args, _ = call
#         bucket, uri, data_buffer, content_type = args
#
#         data_buffer.seek(0)
#         content = data_buffer.read().decode('utf-8')
#         records = json.loads(content)
#
#         self.assertIsInstance(records, list)
#         self.assertEqual(len(records), 5)
#         for record in records:
#             self.assertIsInstance(record, dict)
#         self.assertEqual(records, product[1])
#
#     def test_invalid_chunk_size(self):
#         """Test initializing exporter with invalid chunk size (zero or negative). Expecting ValueError."""
#         with self.assertRaises(ValueError) as context_zero:
#             JsonExporter(
#                 setup_context=self.setup_context,
#                 product_name="test_product",
#                 storage_id="minio",
#                 target_uri="test_path",
#                 use_ndjson=False,
#                 chunk_size=0
#             )
#         self.assertIn("Chunk size must be a positive integer", str(context_zero.exception))
#
#         with self.assertRaises(ValueError) as context_negative:
#             JsonExporter(
#                 setup_context=self.setup_context,
#                 product_name="test_product",
#                 storage_id="minio",
#                 target_uri="test_path",
#                 use_ndjson=False,
#                 chunk_size=-5
#             )
#         self.assertIn("Chunk size must be a positive integer", str(context_negative.exception))
#
#     def test_ndjson_output(self):
#         """Test exporting data with use_ndjson=True produces correct NDJSON format."""
#         # Reinitialize the exporter with use_ndjson=True
#         self.exporter = JsonExporter(
#             setup_context=self.setup_context,
#             product_name="test_product",
#             storage_id="minio",
#             target_uri="test_path",
#             use_ndjson=True,
#             chunk_size=1000
#         )
#         self.exporter._storage = self.storage
#
#         product = ("test_product", generate_mock_data(5))
#         self.exporter.consume(product)
#         self.exporter.finalize_chunks()
#         self.exporter.upload_to_storage(bucket="test_bucket", name=self.exporter.product_name)
#
#         self.assertEqual(self.storage.write.call_count, 1)
#         call = self.storage.write.call_args
#         args, _ = call
#         bucket, uri, data_buffer, content_type = args
#
#         data_buffer.seek(0)
#         content = data_buffer.read().decode('utf-8')
#         lines = content.strip().split('\n')
#
#         # Verify that each line is a valid JSON object
#         self.assertEqual(len(lines), 5)
#         for line, expected_record in zip(lines, product[1]):
#             record = json.loads(line)
#             self.assertIsInstance(record, dict)
#             self.assertEqual(record, expected_record)
#
#         # Verify content type
#         self.assertEqual(content_type, "application/x-ndjson")
#
#     def test_non_serializable_data(self):
#         """Test exporter raises exception when data contains non-serializable objects."""
#         from datetime import datetime
#
#         # Generate data with a datetime object, which is not JSON serializable by default
#         data = [{"id": 1, "timestamp": datetime.now()}]
#         product = ("test_product", data)
#
#         self.exporter.consume(product)
#         self.exporter.finalize_chunks()
#         self.exporter.upload_to_storage(bucket="test_bucket", name=self.exporter.product_name)
#
#     def test_unlimited_chunk_size(self):
#         """Test exporting data with chunk_size=None exports all data in a single chunk."""
#         # Reinitialize the exporter with chunk_size=None
#         self.exporter = JsonExporter(
#             setup_context=self.setup_context,
#             product_name="test_product",
#             storage_id="minio",
#             target_uri="test_path",
#             use_ndjson=False,
#             chunk_size=None
#         )
#         self.exporter._storage = self.storage
#
#         total_records = 2500
#         product = ("test_product", generate_mock_data(total_records), {"type": "test_type"})
#         self.exporter.consume(product)
#         self.exporter.finalize_chunks()
#         self.exporter.upload_to_storage(bucket="test_bucket", name=self.exporter.product_name)
#
#         # Expecting only one write call
#         self.assertEqual(self.storage.write.call_count, 1)
#
#         # Verify that all data is in the single chunk
#         call = self.storage.write.call_args
#         args, _ = call
#         bucket, uri, data_buffer, content_type = args
#
#         data_buffer.seek(0)
#         content = data_buffer.read().decode('utf-8')
#         records = json.loads(content)
#         self.assertEqual(len(records), total_records)
#         self.assertEqual(records, product[1])
#
#     def test_data_with_special_characters(self):
#         """Test exporting data containing special and Unicode characters."""
#         special_characters_data = [
#             {"id": 1, "text": "Hello, world!"},
#             {"id": 2, "text": "Special chars: !@#$%^&*()_+-=[]{}|;':,./<>?"},
#             {"id": 3, "text": "Unicode: Привет мир, こんにちは世界, 안녕하세요 세계"}
#         ]
#         product = ("test_product", special_characters_data)
#         self.exporter.consume(product)
#         self.exporter.finalize_chunks()
#         self.exporter.upload_to_storage(bucket="test_bucket", name=self.exporter.product_name)
#
#         self.assertEqual(self.storage.write.call_count, 1)
#         call = self.storage.write.call_args
#         args, _ = call
#         bucket, uri, data_buffer, content_type = args
#
#         data_buffer.seek(0)
#         content = data_buffer.read().decode('utf-8')
#         records = json.loads(content)
#         self.assertEqual(records, special_characters_data)
#
#     def test_exporting_empty_dictionaries(self):
#         """Test exporting a list of empty dictionaries."""
#         empty_dicts_data = [{} for _ in range(5)]
#         product = ("test_product", empty_dicts_data)
#         self.exporter.consume(product)
#         self.exporter.finalize_chunks()
#         self.exporter.upload_to_storage(bucket="test_bucket", name=self.exporter.product_name)
#
#         self.assertEqual(self.storage.write.call_count, 1)
#         call = self.storage.write.call_args
#         args, _ = call
#         bucket, uri, data_buffer, content_type = args
#
#         data_buffer.seek(0)
#         content = data_buffer.read().decode('utf-8')
#         records = json.loads(content)
#         self.assertEqual(records, empty_dicts_data)
#
#     def test_exception_during_file_write(self):
#         """Test exporter handles exceptions during file writing gracefully."""
#         product = ("test_product", generate_mock_data(5))
#
#         # Mock the open method to raise an IOError
#         original_open = Path.open
#
#         def mock_open(*args, **kwargs):
#             raise IOError("Simulated file write error")
#
#         Path.open = mock_open
#
#         try:
#             with self.assertRaises(IOError) as context:
#                 self.exporter.consume(product)
#             self.assertIn("Simulated file write error", str(context.exception))
#         finally:
#             # Restore the original open method
#             Path.open = original_open
#
#     @unittest.skipIf(os.name == 'posix', "Skipping multiprocessing test on Linux")
#     def test_multiprocessing_export_with_multiple_child_processes(self):
#         """Test exporter works correctly with multiple child processes."""
#         total_records = 3000
#         chunk_size = 1000
#         data = generate_mock_data(total_records)
#         data_chunks = [data[i:i + chunk_size] for i in range(0, total_records, chunk_size)]
#
#         manager = multiprocessing.Manager()
#         shared_storage_list = manager.list()
#
#         processes = []
#         for chunk in data_chunks:
#             p = multiprocessing.Process(target=worker,
#                                         args=(chunk, self.setup_context, shared_storage_list, chunk_size))
#             p.start()
#             processes.append(p)
#         for p in processes:
#             p.join()
#
#         # Parent process finalizes and uploads
#         exporter = JsonExporter(
#             setup_context=self.setup_context,
#             product_name="test_product",
#             storage_id="minio",
#             target_uri="test_path",
#             use_ndjson=False,
#             chunk_size=chunk_size
#         )
#         exporter._storage = StorageMock(shared_storage_list)
#         exporter.finalize_chunks()
#         exporter.upload_to_storage(bucket="test_bucket", name="test_product")
#
#         # Verify that storage writes include data from all child processes
#         self.assertEqual(len(shared_storage_list), len(data_chunks))
#         total_records_exported = 0
#         for entry in shared_storage_list:
#             bucket, uri, content, content_type = entry
#             records = json.loads(content)
#             total_records_exported += len(records)
#         self.assertEqual(total_records_exported, total_records)
#
#
# if __name__ == "__main__":
#     unittest.main()

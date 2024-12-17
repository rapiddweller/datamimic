# import multiprocessing
# import os
# import tempfile
# import unittest
# import uuid
# from pathlib import Path
#
# from datamimic_ce.exporters.txt_exporter import TXTExporter  # Adjust the import path as necessary
#
#
# def generate_mock_data(total_records=3000, title="Mock Title", year=2020):
#     """Generate mock data for testing."""
#     return [{
#         "id": f"movie_{i + 1}",
#         "title": f"{title} {i + 1}",
#         "year": year
#     } for i in range(total_records)]
#
#
# class MockSetupContext:
#     def __init__(self, task_id, descriptor_dir):
#         self.task_id = task_id
#         self.descriptor_dir = descriptor_dir
#         self.default_encoding = 'utf-8'
#         self.default_separator = ':'
#         self.default_line_separator = '\n'
#         self.use_mp = False
#
#     def get_client_by_id(self, client_id):
#         # Return a dummy client or data, replace MagicMock dependency
#         return {"id": client_id, "data": "mock_client_data"}
#
#
# def worker(data_chunk, shared_storage_list, task_id, descriptor_dir, properties):
#     setup_context = MockSetupContext(task_id=task_id, descriptor_dir=descriptor_dir)
#     setup_context.properties = properties
#     exporter = TXTExporter(
#         setup_context=setup_context,
#         product_name="test_product",
#         storage_id="minio",
#         target_uri="test_path",
#         chunk_size=1000,
#         separator=properties.get('separator', ':'),
#         line_terminator=properties.get('line_terminator', '\n'),
#         encoding=properties.get('encoding', 'utf-8')
#     )
#     exporter._storage = StorageMock()
#     product = ("test_product", data_chunk)
#     exporter.consume(product)
#     exporter.finalize_chunks()
#     exporter.upload_to_storage(bucket="test_bucket", name=exporter.product_name)
#     shared_storage_list.extend(exporter._storage.write_calls)
#
#
# class StorageMock:
#     """Custom mock storage class to record calls."""
#
#     def __init__(self):
#         self.write_calls = []
#
#     def write(self, bucket, uri, data_buffer, content_type):
#         # Read the raw bytes from the buffer
#         content_bytes = data_buffer.read()
#         data_buffer.seek(0)  # Reset buffer position if needed elsewhere
#         self.write_calls.append({
#             'bucket': bucket,
#             'uri': uri,
#             'content_bytes': content_bytes,  # Store raw bytes
#             'content_type': content_type
#         })
#
#
# class TestTXTExporter(unittest.TestCase):
#     def setUp(self, encoding='utf-8', separator=None, line_terminator=None):
#         """Set up for each test."""
#         self.setup_context = MockSetupContext(task_id=f"test_task_{uuid.uuid4().hex}", descriptor_dir="test_dir")
#         self.tmp_dir = tempfile.TemporaryDirectory()
#         self.tmp_dir_path = Path(self.tmp_dir.name)
#         self.setup_context.descriptor_dir = self.tmp_dir_path
#         self.setup_context.properties = {}
#         self.storage = StorageMock()
#         self.exporter = TXTExporter(
#             setup_context=self.setup_context,
#             product_name="test_product",
#             storage_id="minio",
#             target_uri="test_path",
#             chunk_size=1000,
#             encoding=encoding,
#             separator=separator,
#             line_terminator=line_terminator
#         )
#         self.exporter._storage = self.storage
#
#     def tearDown(self):
#         """Clean up temporary directories."""
#         self.tmp_dir.cleanup()
#
#     def test_single_process_chunking(self):
#         """Test exporting 3000 records with chunk size 1000 in a single process (3 chunk files expected)."""
#         original_data = generate_mock_data(3000)
#         product = ("test_product", original_data)
#         self.exporter.consume(product)
#         self.exporter.finalize_chunks()
#         self.exporter.upload_to_storage(bucket="test_bucket", name=self.exporter.product_name)
#         self.assertEqual(len(self.storage.write_calls), 3)
#
#         total_records_exported = 0
#         for write_call in self.storage.write_calls:
#             bucket = write_call['bucket']
#             uri = write_call['uri']
#             content_bytes = write_call['content_bytes']  # Correct key access
#             content = content_bytes.decode(self.exporter.encoding)  # Decode using specified encoding
#             content_type = write_call['content_type']
#
#             # Verify bucket and URI
#             self.assertEqual(bucket, "test_bucket")
#             self.assertTrue(uri.startswith(f"{self.exporter._task_id}"))
#             # Verify content type
#             self.assertEqual(content_type, self.exporter._get_content_type())
#
#             # Process content
#             lines = content.strip().split(self.exporter.line_terminator)
#             total_records_exported += len(lines)  # Each line corresponds to a record
#
#             # Verify TXT content
#             for line in lines:
#                 if not line.strip():
#                     continue  # Skip empty lines
#                 # Each line should start with 'test_product: '
#                 self.assertTrue(line.startswith("test_product: "), f"Line does not start with 'test_product: ': {line}")
#                 # Further verification can be added as needed
#
#         self.assertEqual(total_records_exported, 3000)
#
#     def test_export_with_different_line_terminators(self):
#         """Test exporting data with different line terminator settings."""
#         terminators = ['\n']
#         for terminator in terminators:
#             with self.subTest(line_terminator=terminator):
#                 # Initialize a fresh setup for each subTest
#                 self.setUp(line_terminator=terminator)
#
#                 data = generate_mock_data(5)
#                 product = ("test_product", data)
#                 self.exporter.consume(product)
#                 self.exporter.finalize_chunks()
#                 self.exporter.upload_to_storage(bucket="test_bucket", name=self.exporter.product_name)
#                 self.assertEqual(len(self.storage.write_calls), 1)
#
#                 write_call = self.storage.write_calls[0]
#                 content_bytes = write_call['content_bytes']
#                 content = content_bytes.decode(self.exporter.encoding)
#                 lines = content.split(terminator)
#
#                 # Remove the last empty element if split by terminator
#                 if lines and not lines[-1]:
#                     lines.pop()
#
#                 self.assertEqual(len(lines), 5)
#
#                 # Verify that each line ends with the correct terminator
#                 for line in lines:
#                     self.assertTrue(line.endswith(terminator.strip()),
#                                     f"Line does not end with terminator {terminator}")
#                     self.assertTrue(line.startswith("test_product: "),
#                                     f"Line does not start with 'test_product: ': {line}")
#
#     def test_custom_separator_and_encoding(self):
#         """Test exporting with custom separator and encoding."""
#
#         self.setUp(encoding='utf-16', separator='|')
#
#         original_data = generate_mock_data(10)
#         product = ("test_product", original_data)
#         self.exporter.consume(product)
#         self.exporter.finalize_chunks()
#         self.exporter.upload_to_storage(bucket="test_bucket", name=self.exporter.product_name)
#         self.assertEqual(len(self.storage.write_calls), 1)
#
#         write_call = self.storage.write_calls[0]
#         content_bytes = write_call['content_bytes']  # Correct key access
#         content = content_bytes.decode(self.exporter.encoding)  # Decode using specified encoding
#         lines = content.strip().split(self.exporter.line_terminator)
#         self.assertGreaterEqual(len(lines), 1)  # At least one line (e.g., initial lines)
#
#         # Verify TXT content with custom separator
#         for record, line in zip(original_data, lines):
#             expected_line = f"test_product: {record}"
#             self.assertEqual(line, expected_line)
#
#     def test_special_characters_in_data(self):
#         """Test exporting data containing separators, quotes, and newlines."""
#
#         special_data = [
#             {"id": "1", "title": 'Title with | pipe', "year": 2020},
#             {"id": "2", "title": 'Title with "quote"', "year": 2021},
#             {"id": "3", "title": 'Title with \n newline', "year": 2022},
#             {"id": "4", "title": 'Title with separator|semicolon', "year": 2023},
#         ]
#         product = ("test_product", special_data)
#         self.exporter.consume(product)
#         self.exporter.finalize_chunks()
#         self.exporter.upload_to_storage(bucket="test_bucket", name=self.exporter.product_name)
#         self.assertEqual(len(self.storage.write_calls), 1)
#
#         write_call = self.storage.write_calls[0]
#         content_bytes = write_call['content_bytes']  # Correct key access
#         content = content_bytes.decode(self.exporter.encoding)  # Decode using specified encoding
#         lines = content.strip().split(self.exporter.line_terminator)
#
#         self.assertEqual(len(lines), 4)  # 4 records
#
#         # Verify TXT content
#         expected_lines = [
#             f"test_product: {record}" for record in special_data
#         ]
#         for expected_line, actual_line in zip(expected_lines, lines):
#             self.assertEqual(actual_line, expected_line)
#
#     def test_large_dataset(self):
#         """Test exporting a very large dataset to check performance and memory usage."""
#         total_records = 500_000  # Half a million records
#         self.exporter.chunk_size = 100_000
#         original_data = generate_mock_data(total_records)
#         product = ("test_product", original_data)
#         self.exporter.consume(product)
#         self.exporter.finalize_chunks()
#         self.exporter.upload_to_storage(bucket="test_bucket", name=self.exporter.product_name)
#
#         expected_chunks = (total_records + self.exporter.chunk_size - 1) // self.exporter.chunk_size
#         self.assertEqual(len(self.storage.write_calls), expected_chunks)
#
#         total_records_exported = 0
#         for write_call in self.storage.write_calls:
#             content_bytes = write_call['content_bytes']  # Correct key access
#             content = content_bytes.decode(self.exporter.encoding)  # Decode using specified encoding
#             lines = content.strip().split(self.exporter.line_terminator)
#             total_records_exported += len(lines)  # Each line corresponds to a record
#
#             # Verify TXT content
#             for line in lines:
#                 if not line.strip():
#                     continue  # Skip empty lines
#                 self.assertTrue(line.startswith("test_product: "), f"Line does not start with 'test_product: ': {line}")
#
#         self.assertEqual(total_records_exported, total_records)
#
#     def test_invalid_data_handling(self):
#         """Test exporting data with invalid data types."""
#         invalid_data = [
#             {"id": "1", "title": "Valid Title", "year": 2020},
#             {"id": "2", "title": "Another Title", "year": None},  # 'year' as None
#             {"id": "3", "title": "Title with | separator", "year": "Invalid Year"},  # 'year' as str
#         ]
#         product = ("test_product", invalid_data)
#         self.exporter.consume(product)
#         self.exporter.finalize_chunks()
#         self.exporter.upload_to_storage(bucket="test_bucket", name=self.exporter.product_name)
#         self.assertEqual(len(self.storage.write_calls), 1)
#
#         write_call = self.storage.write_calls[0]
#         content_bytes = write_call['content_bytes']
#         content = content_bytes.decode(self.exporter.encoding)
#         lines = content.strip().split(self.exporter.line_terminator)
#         self.assertEqual(len(lines), 3)  # 3 records
#
#         # Verify TXT content
#         expected_lines = [
#             f"test_product: {record}" for record in invalid_data
#         ]
#         for expected_line, actual_line in zip(expected_lines, lines):
#             self.assertEqual(actual_line, expected_line)
#
#     @unittest.skipIf(os.name == 'posix', "skip multiprocessing test on posix")
#     def test_multiprocessing_export(self):
#         """Test exporting data concurrently using multiprocessing."""
#         total_processes = os.cpu_count() or 1
#         total_records_per_process = 5000
#         data = generate_mock_data(total_records_per_process * total_processes)
#         data_chunks = [data[i * total_records_per_process:(i + 1) * total_records_per_process] for i in
#                        range(total_processes)]
#
#         manager = multiprocessing.Manager()
#         shared_storage_list = manager.list()
#         processes = []
#         for chunk in data_chunks:
#             p = multiprocessing.Process(
#                 target=worker,
#                 args=(chunk, shared_storage_list, self.setup_context.task_id, self.setup_context.descriptor_dir,
#                       self.setup_context.properties)
#             )
#             p.start()
#             processes.append(p)
#         for p in processes:
#             p.join()
#
#         # Verify total write calls
#         expected_write_calls = total_processes * (total_records_per_process // self.exporter.chunk_size)
#         self.assertEqual(len(shared_storage_list), expected_write_calls,
#                          f"Expected {expected_write_calls} write calls, but got {len(shared_storage_list)}")
#
#         # Verify total records exported
#         total_records_exported = 0
#         for write_call in shared_storage_list:
#             content_bytes = write_call['content_bytes']
#             content = content_bytes.decode('utf-8')  # Assuming utf-8
#             lines = content.strip().split('\n')
#             total_records_exported += len(lines)
#             # Verify each line starts with 'test_product: '
#             for line in lines:
#                 self.assertTrue(line.startswith("test_product: "), f"Line does not start with 'test_product: ': {line}")
#
#         self.assertEqual(total_records_exported, total_processes * total_records_per_process)
#
#     def test_empty_records_and_missing_fields(self):
#         """Test exporting data with empty records and missing fields."""
#         data_with_missing_fields = [
#             {"id": "1", "title": "Title 1", "year": 2020},
#             {"id": "2", "title": "Title 2"},  # Missing 'year'
#             {},  # Empty record
#             {"id": "3", "year": 2022},  # Missing 'title'
#         ]
#         product = ("test_product", data_with_missing_fields)
#         # For TXTExporter, missing fields are handled as per _write_data_to_buffer implementation
#         self.exporter.consume(product)
#         self.exporter.finalize_chunks()
#         self.exporter.upload_to_storage(bucket="test_bucket", name=self.exporter.product_name)
#
#         self.assertEqual(len(self.storage.write_calls), 1)
#         write_call = self.storage.write_calls[0]
#         content_bytes = write_call['content_bytes']
#         content = content_bytes.decode(self.exporter.encoding)
#         lines = content.strip().split(self.exporter.line_terminator)
#         self.assertEqual(len(lines), 4)  # 4 records
#
#         # Verify TXT content
#         expected_lines = [
#             f"test_product: {record}" for record in data_with_missing_fields
#         ]
#         for expected_line, actual_line in zip(expected_lines, lines):
#             self.assertEqual(actual_line, expected_line)
#
#     def test_consume_invalid_product(self):
#         """Test that consuming an invalid product raises ValueError."""
#         with self.assertRaises(ValueError):
#             self.exporter.consume("invalid_product")
#
#     def test_chunk_rotation_without_remainder(self):
#         """Test exporting data where total records are a multiple of chunk size."""
#         total_records = 5000
#         self.exporter.chunk_size = 1000
#         original_data = generate_mock_data(total_records)
#         product = ("test_product", original_data)
#         self.exporter.consume(product)
#         self.exporter.finalize_chunks()
#         self.exporter.upload_to_storage(bucket="test_bucket", name=self.exporter.product_name)
#
#         self.assertEqual(len(self.storage.write_calls), 5)
#         total_records_exported = 0
#         for write_call in self.storage.write_calls:
#             content_bytes = write_call['content_bytes']
#             content = content_bytes.decode(self.exporter.encoding)
#             lines = content.strip().split(self.exporter.line_terminator)
#             total_records_exported += len(lines)  # Each line corresponds to a record
#
#             # Verify TXT content
#             for line in lines:
#                 if not line.strip():
#                     continue  # Skip empty lines
#                 self.assertTrue(line.startswith("test_product: "), f"Line does not start with 'test_product: ': {line}")
#
#         self.assertEqual(total_records_exported, total_records)
#
#     def test_chunk_rotation_with_remainder(self):
#         """Test exporting data where total records are not a multiple of chunk size."""
#         total_records = 5500
#         self.exporter.chunk_size = 1000
#         original_data = generate_mock_data(total_records)
#         product = ("test_product", original_data)
#         self.exporter.consume(product)
#         self.exporter.finalize_chunks()
#         self.exporter.upload_to_storage(bucket="test_bucket", name=self.exporter.product_name)
#
#         expected_chunks = (total_records + self.exporter.chunk_size - 1) // self.exporter.chunk_size
#         self.assertEqual(len(self.storage.write_calls), expected_chunks)
#         total_records_exported = 0
#         for write_call in self.storage.write_calls:
#             content_bytes = write_call['content_bytes']
#             content = content_bytes.decode(self.exporter.encoding)
#             lines = content.strip().split(self.exporter.line_terminator)
#             total_records_exported += len(lines)  # Each line corresponds to a record
#
#             # Verify TXT content
#             for line in lines:
#                 if not line.strip():
#                     continue  # Skip empty lines
#                 self.assertTrue(line.startswith("test_product: "), f"Line does not start with 'test_product: ': {line}")
#
#         self.assertEqual(total_records_exported, total_records)
#
#     def test_no_name_provided(self):
#         """Test exporting when the product name is not provided."""
#         # Modify consume method to handle missing name appropriately
#         # Since the current consume method expects a tuple with (name, data), this test ensures proper error handling
#         with self.assertRaises(ValueError):
#             self.exporter.consume((None, generate_mock_data(10)))
#
#     def test_export_with_custom_line_terminator(self):
#         """Test exporting data with a custom line terminator."""
#         self.setUp(line_terminator='|')
#
#         data = generate_mock_data(5)
#         product = ("test_product", data)
#         self.exporter.consume(product)
#         self.exporter.finalize_chunks()
#         self.exporter.upload_to_storage(bucket="test_bucket", name=self.exporter.product_name)
#         self.assertEqual(len(self.storage.write_calls), 1)
#
#         write_call = self.storage.write_calls[0]
#         content_bytes = write_call['content_bytes']
#         content = content_bytes.decode(self.exporter.encoding)
#         lines = content.split('|')  # Split using custom line terminator
#
#         # Remove the last empty element if split by terminator
#         if lines and not lines[-1]:
#             lines.pop()
#
#         self.assertEqual(len(lines), 5)
#
#         # Verify TXT content
#         for record, line in zip(data, lines):
#             expected_line = f"test_product: {record}"
#             self.assertEqual(line, expected_line)
#
#     def test_export_with_different_quoting_options(self):
#         """Test exporting data with different quoting options."""
#         # Since TXTExporter does not handle quoting, this test might not be relevant.
#         # If you plan to handle quoting in TXTExporter, implement accordingly.
#         pass  # Placeholder for potential future tests
#
#     def test_export_empty_data_list(self):
#         """Test exporting when data list is empty."""
#         product = ("test_product", [])
#         self.exporter.consume(product)
#         self.exporter.finalize_chunks()
#         self.exporter.upload_to_storage(bucket="test_bucket", name=self.exporter.product_name)
#         # Should not write any files
#         self.assertEqual(len(self.storage.write_calls), 0)
#
#
# if __name__ == '__main__':
#     unittest.main()

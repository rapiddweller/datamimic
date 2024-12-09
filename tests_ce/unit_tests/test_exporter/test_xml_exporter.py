# # test_xml_exporter.py
#
# import multiprocessing
# import os
# import tempfile
# import unittest
# import uuid
# import xml.etree.ElementTree as ET
# from pathlib import Path
#
# from datamimic_ce.exporters.xml_exporter import XMLExporter  # Adjust the import path as necessary
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
#         self.default_separator = ','
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
#     exporter = XMLExporter(
#         setup_context=setup_context,
#         product_name="test_product",
#         storage_id="minio",
#         target_uri="test_path",
#         chunk_size=1000,
#         root_element=properties.get('root_element', 'list'),
#         item_element=properties.get('item_element', 'item'),
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
# class TestXMLExporter(unittest.TestCase):
#     def setUp(self, encoding='utf-8', root_element='list', item_element='item'):
#         """Set up for each test."""
#         self.setup_context = MockSetupContext(task_id=f"test_task_{uuid.uuid4().hex}", descriptor_dir="test_dir")
#         self.tmp_dir = tempfile.TemporaryDirectory()
#         self.tmp_dir_path = Path(self.tmp_dir.name)
#         self.setup_context.descriptor_dir = self.tmp_dir_path
#         self.setup_context.properties = {}
#         self.storage = StorageMock()
#         self.exporter = XMLExporter(
#             setup_context=self.setup_context,
#             product_name="test_product",
#             storage_id="minio",
#             target_uri="test_path",
#             chunk_size=1000,
#             root_element=root_element,
#             item_element=item_element,
#             encoding=encoding
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
#             content_bytes = write_call['content_bytes']
#             content = content_bytes.decode(self.exporter.encoding)
#             content_type = write_call['content_type']
#
#             # Verify bucket and URI
#             self.assertEqual(bucket, "test_bucket")
#             self.assertTrue(uri.startswith(f"{self.exporter._task_id}"))
#             # Verify content type
#             self.assertEqual(content_type, self.exporter._get_content_type())
#
#             # Parse XML and count records
#             root = ET.fromstring(content)
#             records = root.findall(f".//{self.exporter.item_element}")
#             total_records_exported += len(records)
#
#         self.assertEqual(total_records_exported, 3000)
#
#     def test_export_with_custom_root_and_item_elements(self):
#         """Test exporting data with custom root and item element names."""
#         self.setUp(root_element='movies', item_element='movie')
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
#         root = ET.fromstring(content)
#
#         # Verify root element
#         self.assertEqual(root.tag, 'movies')
#
#         # Verify number of items
#         records = root.findall(".//movie")
#         self.assertEqual(len(records), 5)
#
#         # Verify each record's content
#         for record, data in zip(records, data):
#             for key, value in data.items():
#                 self.assertEqual(record.find(key).text, str(value))
#
#     def test_invalid_product_handling(self):
#         """Test that consuming an invalid product raises ValueError."""
#         # Product is not a tuple
#         with self.assertRaises(ValueError):
#             self.exporter.consume("invalid_product")
#
#         # Product tuple has less than two elements
#         with self.assertRaises(ValueError):
#             self.exporter.consume(("test_product",))
#
#         # Product name is None
#         with self.assertRaises(ValueError):
#             self.exporter.consume((None, generate_mock_data(10)))
#
#     def test_special_characters_in_data(self):
#         """Test exporting data containing special characters."""
#         special_data = [
#             {"id": "1", "title": 'Title with <tag>', "year": 2020},
#             {"id": "2", "title": 'Title with & ampersand', "year": 2021},
#             {"id": "3", "title": 'Title with "quotes"', "year": 2022},
#             {"id": "4", "title": "Title with 'apostrophe'", "year": 2023},
#         ]
#         product = ("test_product", special_data)
#         self.exporter.consume(product)
#         self.exporter.finalize_chunks()
#         self.exporter.upload_to_storage(bucket="test_bucket", name=self.exporter.product_name)
#         self.assertEqual(len(self.storage.write_calls), 1)
#
#         write_call = self.storage.write_calls[0]
#         content_bytes = write_call['content_bytes']
#         content = content_bytes.decode(self.exporter.encoding)
#         root = ET.fromstring(content)
#
#         # Verify number of items
#         records = root.findall(f".//{self.exporter.item_element}")
#         self.assertEqual(len(records), 4)
#
#         # Verify each record's content
#         for record, data in zip(records, special_data):
#             for key, value in data.items():
#                 self.assertEqual(record.find(key).text, str(value))
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
#         # Each process has 5000 records with chunk_size=1000, so 5 chunks per process
#         expected_write_calls = total_processes * (total_records_per_process // self.exporter.chunk_size)
#         self.assertEqual(len(shared_storage_list), expected_write_calls,
#                          f"Expected {expected_write_calls} write calls, but got {len(shared_storage_list)}")
#
#         # Verify total records exported
#         total_records_exported = 0
#         for write_call in shared_storage_list:
#             content_bytes = write_call['content_bytes']
#             content = content_bytes.decode('utf-8')  # Assuming utf-8
#             root = ET.fromstring(content)
#             records = root.findall(f".//{self.exporter.item_element}")
#             total_records_exported += len(records)
#
#             # Optionally, verify each record's content
#             # This can be expensive for large datasets; consider limiting checks
#             for record in records[:10]:  # Check first 10 records as a sample
#                 self.assertTrue(record.find("id") is not None)
#                 self.assertTrue(record.find("title") is not None)
#                 self.assertTrue(record.find("year") is not None)
#
#         self.assertEqual(total_records_exported, total_processes * total_records_per_process)
#
#     def test_empty_data_handling(self):
#         """Test exporting when data list is empty."""
#         product = ("test_product", [])
#         self.exporter.consume(product)
#         self.exporter.finalize_chunks()
#         self.exporter.upload_to_storage(bucket="test_bucket", name=self.exporter.product_name)
#         # Should not write any files
#         self.assertEqual(len(self.storage.write_calls), 0)
#
#     def test_custom_root_element(self):
#         """Test exporting data with a custom root element."""
#         self.setUp(root_element='catalog', item_element='movie')
#
#         data = generate_mock_data(3)
#         product = ("test_product", data)
#         self.exporter.consume(product)
#         self.exporter.finalize_chunks()
#         self.exporter.upload_to_storage(bucket="test_bucket", name=self.exporter.product_name)
#         self.assertEqual(len(self.storage.write_calls), 1)
#
#         write_call = self.storage.write_calls[0]
#         content_bytes = write_call['content_bytes']
#         content = content_bytes.decode(self.exporter.encoding)
#         root = ET.fromstring(content)
#
#         # Verify root element
#         self.assertEqual(root.tag, 'catalog')
#
#         # Verify number of items
#         records = root.findall(".//movie")
#         self.assertEqual(len(records), 3)
#
#         # Verify each record's content
#         for record, data in zip(records, data):
#             for key, value in data.items():
#                 self.assertEqual(record.find(key).text, str(value))
#
#
# if __name__ == '__main__':
#     unittest.main()

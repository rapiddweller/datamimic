import unittest

from datamimic_ce.exporters.exporter_util import ExporterUtil


class TestExporterUtil(unittest.TestCase):
    def test_single_function_without_params(self):
        # Test single function without parameters (dotted name)
        result = ExporterUtil.parse_function_string("mongodb.delete")
        expected = [{"function_name": "mongodb.delete", "params": None}]
        self.assertEqual(result, expected)

    def test_single_function_simple_name(self):
        # Test single simple function name without parameters
        result = ExporterUtil.parse_function_string("CSV")
        expected = [{"function_name": "CSV", "params": None}]
        self.assertEqual(result, expected)

    def test_multiple_functions_without_params(self):
        # Test multiple functions without parameters
        result = ExporterUtil.parse_function_string("CSV, JSON")
        expected = [
            {"function_name": "CSV", "params": None},
            {"function_name": "JSON", "params": None},
        ]
        self.assertEqual(result, expected)

    def test_function_with_single_param(self):
        # Test function with a single keyword parameter
        result = ExporterUtil.parse_function_string("JSON(chunk_size=2)")
        expected = [{"function_name": "JSON", "params": {"chunk_size": 2}}]
        self.assertEqual(result, expected)

    def test_function_with_multiple_params(self):
        # Test function with multiple parameters
        result = ExporterUtil.parse_function_string("mongodb.upsert(data={'key': 'value'}, overwrite=True)")
        expected = [
            {
                "function_name": "mongodb.upsert",
                "params": {"data": {"key": "value"}, "overwrite": True},
            }
        ]
        self.assertEqual(result, expected)

    def test_mixed_functions_with_and_without_params(self):
        # Test multiple functions, some with parameters and some without
        result = ExporterUtil.parse_function_string("mongodb.update, CSV, JSON(chunk_size=2)")
        expected = [
            {"function_name": "mongodb.update", "params": None},
            {"function_name": "CSV", "params": None},
            {"function_name": "JSON", "params": {"chunk_size": 2}},
        ]
        self.assertEqual(result, expected)

    def test_mongodb_delete_with_complex_param(self):
        # Test complex nested parameter
        result = ExporterUtil.parse_function_string("mongodb.delete(criteria={'age': {'$gt': 18}})")
        expected = [
            {
                "function_name": "mongodb.delete",
                "params": {"criteria": {"age": {"$gt": 18}}},
            }
        ]
        self.assertEqual(result, expected)

    def test_dotted_names_without_params(self):
        # Test multiple dotted names without parameters
        result = ExporterUtil.parse_function_string("mongodb.find, SQL.load")
        expected = [
            {"function_name": "mongodb.find", "params": None},
            {"function_name": "SQL.load", "params": None},
        ]
        self.assertEqual(result, expected)

    def test_function_with_nested_dictionary_param(self):
        # Test function with nested dictionary parameters
        result = ExporterUtil.parse_function_string(
            "mongodb.upsert(document={'id': 1, 'data': {'key': 'value', 'status': 'active'}})"
        )
        expected = [
            {
                "function_name": "mongodb.upsert",
                "params": {"document": {"id": 1, "data": {"key": "value", "status": "active"}}},
            }
        ]
        self.assertEqual(result, expected)

    def test_unsupported_expression_lambda(self):
        # Test unsupported lambda expression
        with self.assertRaises(ValueError):
            ExporterUtil.parse_function_string("lambda x: x + 1")

    def test_unsupported_expression_arithmetic(self):
        # Test unsupported arithmetic expression
        with self.assertRaises(ValueError):
            ExporterUtil.parse_function_string("1 + 2")

    def test_empty_string(self):
        # Test empty string input
        result = ExporterUtil.parse_function_string("")
        expected = []
        self.assertEqual(result, expected)

    def test_spaces_and_commas_only(self):
        # Test spaces and commas only, should return empty
        result = ExporterUtil.parse_function_string(" , , ")
        expected = []
        self.assertEqual(result, expected)

    def test_function_with_non_literal_param(self):
        # Test function with a non-literal parameter (unsupported)
        with self.assertRaises(ValueError):
            ExporterUtil.parse_function_string("JSON(chunk_size=my_variable)")

    def test_function_with_mixed_types(self):
        # Test function with mixed types in parameters
        result = ExporterUtil.parse_function_string("JSON(chunk_size=2, enabled=True, name='sample')")
        expected = [
            {
                "function_name": "JSON",
                "params": {"chunk_size": 2, "enabled": True, "name": "sample"},
            }
        ]
        self.assertEqual(result, expected)

    def test_large_nested_data_structure(self):
        # Test function with a large and complex nested data structure
        result = ExporterUtil.parse_function_string(
            "mongodb.upsert(data={'key': {'subkey': [1, 2, {'deepkey': 'deepvalue'}]}})"
        )
        expected = [
            {
                "function_name": "mongodb.upsert",
                "params": {"data": {"key": {"subkey": [1, 2, {"deepkey": "deepvalue"}]}}},
            }
        ]
        self.assertEqual(result, expected)

    def test_check_path_format_file(self):
        # Test valid file path
        path = "valid/file/path.txt"
        assert ExporterUtil.check_path_format(path) == "file"

    def test_check_path_format_directory(self):
        # Test valid directory path
        path = "valid/directory/path"
        assert ExporterUtil.check_path_format(path) == "directory"

    def test_check_path_format_invalid_ending_dot(self):
        # Test invalid path ending with a dot
        path = "invalid/path/ending/with/dot."
        with self.assertRaises(ValueError):
            ExporterUtil.check_path_format(path)

    def test_check_path_format_invalid_characters(self):
        # Test invalid path with special characters
        path = "invalid/path/with/special*chars"
        with self.assertRaises(ValueError):
            ExporterUtil.check_path_format(path)

    def test_check_path_format_empty_string(self):
        # Test empty string path
        path = ""
        with self.assertRaises(ValueError):
            ExporterUtil.check_path_format(path)

    def test_check_path_format_only_dots(self):
        # Test path with only dots
        path = "..."
        with self.assertRaises(ValueError):
            ExporterUtil.check_path_format(path)

    def test_check_path_format_only_slashes(self):
        # Test path with only slashes
        path = "///"
        with self.assertRaises(ValueError):
            ExporterUtil.check_path_format(path)

    def test_check_path_format_file_with_multiple_dots(self):
        # Test valid file path with multiple dots
        path = "valid/file/path.with.multiple.dots.txt"
        assert ExporterUtil.check_path_format(path) == "file"

    def test_check_path_format_directory_with_dashes_underscores(self):
        # Test valid directory path with dashes and underscores
        path = "valid-directory/with_underscores"
        assert ExporterUtil.check_path_format(path) == "directory"

    def test_check_path_format_file_with_numbers(self):
        # Test valid file path with numbers
        path = "valid/file/path123.txt"
        assert ExporterUtil.check_path_format(path) == "file"

    def test_check_path_format_directory_with_numbers(self):
        # Test valid directory path with numbers
        path = "valid/directory123"
        assert ExporterUtil.check_path_format(path) == "directory"


if __name__ == "__main__":
    unittest.main()

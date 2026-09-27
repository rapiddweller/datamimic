import unittest

from datamimic_ce.engine.io.api import parse_function_string


class TestExporterUtil(unittest.TestCase):
    def test_single_function_without_params(self):
        # Test single function without parameters (dotted name)
        result = parse_function_string("mongodb.delete")
        expected = [{"function_name": "mongodb.delete", "params": None}]
        self.assertEqual(result, expected)

    def test_single_function_simple_name(self):
        # Test single simple function name without parameters
        result = parse_function_string("CSV")
        expected = [{"function_name": "CSV", "params": None}]
        self.assertEqual(result, expected)

    def test_multiple_functions_without_params(self):
        # Test multiple functions without parameters
        result = parse_function_string("CSV, JSON")
        expected = [
            {"function_name": "CSV", "params": None},
            {"function_name": "JSON", "params": None},
        ]
        self.assertEqual(result, expected)

    def test_function_with_single_param(self):
        # Test function with a single keyword parameter
        result = parse_function_string("JSON(chunk_size=2)")
        expected = [{"function_name": "JSON", "params": {"chunk_size": 2}}]
        self.assertEqual(result, expected)

    def test_function_with_multiple_params(self):
        # Test function with multiple parameters
        result = parse_function_string("mongodb.upsert(data={'key': 'value'}, overwrite=True)")
        expected = [
            {
                "function_name": "mongodb.upsert",
                "params": {"data": {"key": "value"}, "overwrite": True},
            }
        ]
        self.assertEqual(result, expected)

    def test_mixed_functions_with_and_without_params(self):
        # Test multiple functions, some with parameters and some without
        result = parse_function_string("mongodb.update, CSV, JSON(chunk_size=2)")
        expected = [
            {"function_name": "mongodb.update", "params": None},
            {"function_name": "CSV", "params": None},
            {"function_name": "JSON", "params": {"chunk_size": 2}},
        ]
        self.assertEqual(result, expected)

    def test_mongodb_delete_with_complex_param(self):
        # Test complex nested parameter
        result = parse_function_string("mongodb.delete(criteria={'age': {'$gt': 18}})")
        expected = [
            {
                "function_name": "mongodb.delete",
                "params": {"criteria": {"age": {"$gt": 18}}},
            }
        ]
        self.assertEqual(result, expected)

    def test_dotted_names_without_params(self):
        # Test multiple dotted names without parameters
        result = parse_function_string("mongodb.find, SQL.load")
        expected = [
            {"function_name": "mongodb.find", "params": None},
            {"function_name": "SQL.load", "params": None},
        ]
        self.assertEqual(result, expected)

    def test_function_with_nested_dictionary_param(self):
        # Test function with nested dictionary parameters
        result = parse_function_string(
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
            parse_function_string("lambda x: x + 1")

    def test_unsupported_expression_arithmetic(self):
        # Test unsupported arithmetic expression
        with self.assertRaises(ValueError):
            parse_function_string("1 + 2")

    def test_empty_string(self):
        # Test empty string input
        result = parse_function_string("")
        expected = []
        self.assertEqual(result, expected)

    def test_spaces_and_commas_only(self):
        # Test spaces and commas only, should return empty
        result = parse_function_string(" , , ")
        expected = []
        self.assertEqual(result, expected)

    def test_function_with_non_literal_param(self):
        # Test function with a non-literal parameter (unsupported)
        with self.assertRaises(ValueError):
            parse_function_string("JSON(chunk_size=my_variable)")

    def test_function_with_mixed_types(self):
        # Test function with mixed types in parameters
        result = parse_function_string("JSON(chunk_size=2, enabled=True, name='sample')")
        expected = [
            {
                "function_name": "JSON",
                "params": {"chunk_size": 2, "enabled": True, "name": "sample"},
            }
        ]
        self.assertEqual(result, expected)

    def test_large_nested_data_structure(self):
        # Test function with a large and complex nested data structure
        result = parse_function_string(
            "mongodb.upsert(data={'key': {'subkey': [1, 2, {'deepkey': 'deepvalue'}]}})"
        )
        expected = [
            {
                "function_name": "mongodb.upsert",
                "params": {"data": {"key": {"subkey": [1, 2, {"deepkey": "deepvalue"}]}}},
            }
        ]
        self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()

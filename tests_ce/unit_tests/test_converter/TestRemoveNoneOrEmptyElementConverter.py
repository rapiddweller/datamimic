import unittest
from typing import Any, Dict, List

from datamimic_ce.converter.remove_none_or_empty_element_converter import RemoveNoneOrEmptyElementConverter


class TestRemoveNoneOrEmptyElementConverter(unittest.TestCase):

    def setUp(self):
        self.converter = RemoveNoneOrEmptyElementConverter()

    def test_primitive_types(self):
        test_cases = [
            (42, 42),
            (3.14, 3.14),
            ("test", "test"),
            ("", ""),
            (True, True),
            (None, None),
        ]
        for input_val, expected in test_cases:
            with self.subTest(input_val=input_val):
                self.assertEqual(self.converter.convert(input_val), expected)

    def test_list_handling(self):
        test_cases = [
            ([1, None, [], "", {}, "test"], [1, "test"]),
            ([], []),
            ([None, [], {}, ""], []),
            ([[[[]]]], []),
        ]
        for input_val, expected in test_cases:
            with self.subTest(input_val=input_val):
                self.assertEqual(self.converter.convert(input_val), expected)

    def test_dict_handling(self):
        test_cases = [
            ({"a": 1, "b": None, "c": [], "d": ""}, {"a": 1}),
            ({}, {}),
            ({"a": None, "b": [], "c": {}}, {}),
            ({"a": {"b": {"c": []}}}, {}),
        ]
        for input_val, expected in test_cases:
            with self.subTest(input_val=input_val):
                self.assertEqual(self.converter.convert(input_val), expected)

    def test_nested_structures(self):
        input_data = {
            "list": [1, None, {"a": None, "b": 2}],
            "dict": {"x": [], "y": [1, None, ""]},
            "empty": {}
        }
        expected = {
            "list": [1, {"b": 2}],
            "dict": {"y": [1]}
        }
        self.assertEqual(self.converter.convert(input_data), expected)

    def test_complex_mixed_types(self):
        input_data = [
            1,
            ["nested", None, []],
            {"a": 1, "b": None, "c": {"d": [], "e": 2}},
            None,
            [],
            [[], {}, None]
        ]
        expected = [
            1,
            ["nested"],
            {"a": 1, "c": {"e": 2}}
        ]
        self.assertEqual(self.converter.convert(input_data), expected)

    def test_large_structure_performance(self):
        large_input = {
            str(i): [None, [], {}] if i % 2 else [1, {"x": i}]
            for i in range(1000)
        }
        result = self.converter.convert(large_input)
        for v in result.values():
            self.assertIsInstance(v, list)
            self.assertGreater(len(v), 0)

    def test_circular_reference(self):
        circular_list = [1, 2]
        circular_list.append(circular_list)

        with self.assertRaises(RecursionError):
            self.converter.convert(circular_list)

    def test_deep_structures(self):
        test_cases = [
            [1, [2, [3, [4, [5]]]]],  # Deep nesting
            {"a": {"b": {"c": {"d": {"e": 1}}}}},  # Deep dict
            [{"a": [{"b": []}]}, [{"c": {1}}]],  # Mixed deep structure
        ]
        for input_val in test_cases:
            with self.subTest(input_val=input_val):
                result = self.converter.convert(input_val)
                self.assertTrue(result)  # Ensure non-empty result

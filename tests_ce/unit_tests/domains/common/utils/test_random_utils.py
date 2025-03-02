# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import random
import unittest
from unittest.mock import patch

from datamimic_ce.domains.common.utils.random_utils import (
    random_bool,
    random_element_with_exclusions,
    random_float_in_range,
    random_int_in_range,
    random_subset,
    shuffle_list,
    weighted_choice,
)


class TestRandomUtils(unittest.TestCase):
    """Test cases for the random_utils module."""

    def test_weighted_choice_with_weights(self):
        """Test weighted_choice with weighted items."""
        items = [("a", 10), ("b", 1), ("c", 1)]

        with patch("random.choices", return_value=["a"]):
            result = weighted_choice(items)
            self.assertEqual(result, "a")
            random.choices.assert_called_once()

    def test_weighted_choice_without_weights(self):
        """Test weighted_choice with unweighted items."""
        items = ["a", "b", "c"]

        with patch("random.choice", return_value="b"):
            result = weighted_choice(items)
            self.assertEqual(result, "b")
            random.choice.assert_called_once_with(items)

    def test_weighted_choice_empty_list(self):
        """Test weighted_choice with an empty list."""
        with self.assertRaises(ValueError):
            weighted_choice([])

    def test_random_subset(self):
        """Test random_subset function."""
        items = [1, 2, 3, 4, 5]

        # Test with default parameters
        with patch("random.randint", return_value=3), patch("random.sample", return_value=[2, 3, 5]):
            result = random_subset(items)
            self.assertEqual(result, [2, 3, 5])
            random.randint.assert_called_once_with(1, 5)
            random.sample.assert_called_once_with(items, 3)

        # Test with custom min_size and max_size
        with patch("random.randint", return_value=2), patch("random.sample", return_value=[1, 4]):
            result = random_subset(items, min_size=2, max_size=3)
            self.assertEqual(result, [1, 4])
            random.randint.assert_called_once_with(2, 3)
            random.sample.assert_called_once_with(items, 2)

        # Test with empty list
        self.assertEqual(random_subset([]), [])

    def test_random_bool(self):
        """Test random_bool function."""
        # Test with default probability
        with patch("random.random", return_value=0.4):
            self.assertTrue(random_bool())

        with patch("random.random", return_value=0.6):
            self.assertFalse(random_bool())

        # Test with custom probability
        with patch("random.random", return_value=0.7):
            self.assertTrue(random_bool(true_probability=0.8))
            self.assertFalse(random_bool(true_probability=0.6))

    def test_random_int_in_range(self):
        """Test random_int_in_range function."""
        with patch("random.randint", return_value=42):
            result = random_int_in_range(1, 100)
            self.assertEqual(result, 42)
            random.randint.assert_called_once_with(1, 100)

    def test_random_float_in_range(self):
        """Test random_float_in_range function."""
        with patch("random.uniform", return_value=3.14):
            result = random_float_in_range(0.0, 10.0)
            self.assertEqual(result, 3.14)
            random.uniform.assert_called_once_with(0.0, 10.0)

    def test_random_element_with_exclusions(self):
        """Test random_element_with_exclusions function."""
        items = [1, 2, 3, 4, 5]
        exclusions = [2, 4]

        with patch("random.choice", return_value=3):
            result = random_element_with_exclusions(items, exclusions)
            self.assertEqual(result, 3)
            random.choice.assert_called_once_with([1, 3, 5])

        # Test with empty list
        with self.assertRaises(ValueError):
            random_element_with_exclusions([], [])

        # Test with all items excluded
        with self.assertRaises(ValueError):
            random_element_with_exclusions([1, 2, 3], [1, 2, 3])

    def test_shuffle_list(self):
        """Test shuffle_list function."""
        items = [1, 2, 3, 4, 5]
        shuffled_items = [3, 1, 5, 2, 4]

        def side_effect(lst):
            # Modify the list in-place to match shuffled_items
            lst.clear()
            lst.extend(shuffled_items)

        with patch("random.shuffle", side_effect=side_effect):
            result = shuffle_list(items)
            self.assertEqual(result, shuffled_items)
            self.assertEqual(items, [1, 2, 3, 4, 5])  # Original list should be unchanged


if __name__ == "__main__":
    unittest.main()

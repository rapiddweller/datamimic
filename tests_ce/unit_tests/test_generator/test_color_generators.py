# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import re
import unittest

from datamimic_ce.generators.color_generators import ColorGenerator


class TestColorGenerators(unittest.TestCase):
    """Test suite for color-related generators."""

    def test_color_generator_hex(self):
        """Test hex color generation."""
        generator = ColorGenerator(format_type="hex")
        color = generator.generate()
        self.assertIsInstance(color, str)
        self.assertTrue(re.match(r"^#[0-9a-f]{6}$", color))

    def test_color_generator_rgb(self):
        """Test RGB color generation."""
        generator = ColorGenerator(format_type="rgb")
        color = generator.generate()
        self.assertIsInstance(color, str)
        self.assertTrue(re.match(r"^rgb\(\d{1,3},\d{1,3},\d{1,3}\)$", color))
        # Verify RGB values are in valid range
        rgb_values = [int(x) for x in color[4:-1].split(",")]
        for value in rgb_values:
            self.assertTrue(0 <= value <= 255)

    def test_color_generator_name(self):
        """Test color name generation."""
        generator = ColorGenerator(format_type="name")
        color = generator.generate()
        self.assertIsInstance(color, str)
        self.assertIn(color, generator._color_names)

    def test_color_generator_default(self):
        """Test default color generation (hex)."""
        generator = ColorGenerator()
        color = generator.generate()
        self.assertIsInstance(color, str)
        self.assertTrue(re.match(r"^#[0-9a-f]{6}$", color))

    def test_color_generator_invalid_format(self):
        """Test color generation with invalid format."""
        generator = ColorGenerator(format_type="invalid")
        color = generator.generate()
        # Should default to hex format
        self.assertTrue(re.match(r"^#[0-9a-f]{6}$", color))


if __name__ == "__main__":
    unittest.main()

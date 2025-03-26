# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import random

from datamimic_ce.domain_core.base_literal_generator import BaseLiteralGenerator


class ColorGenerator(BaseLiteralGenerator):
    """Generate color values in different formats."""

    def __init__(self, format_type: str = "hex"):
        """
        Initialize ColorGenerator.

        Args:
            format_type (str): The color format to generate. Options: 'hex', 'rgb', 'name'
        """
        self._format = format_type.lower()
        self._color_names = [
            "red",
            "green",
            "blue",
            "yellow",
            "purple",
            "orange",
            "black",
            "white",
            "brown",
            "gray",
            "pink",
            "cyan",
            "magenta",
            "silver",
            "gold",
            "navy",
            "olive",
            "maroon",
            "lime",
            "teal",
            "indigo",
            "violet",
            "coral",
            "crimson",
        ]

    def generate(self) -> str:
        """Generate a color value.

        Returns:
            str: Generated color in specified format
        """
        if self._format == "rgb":
            # Generate random RGB values
            r = random.randint(0, 255)
            g = random.randint(0, 255)
            b = random.randint(0, 255)
            return f"rgb({r},{g},{b})"
        elif self._format == "name":
            return random.choice(self._color_names)
        else:  # hex format
            # Generate hex color manually
            r = random.randint(0, 255)
            g = random.randint(0, 255)
            b = random.randint(0, 255)
            return f"#{r:02x}{g:02x}{b:02x}"

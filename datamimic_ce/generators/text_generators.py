# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from mimesis import Text

from datamimic_ce.generators.generator import Generator


class ParagraphGenerator(Generator):
    """Generate text paragraphs with configurable length (by max number of characters) or word count."""

    def __init__(self, locale: str = "en", length: int | None = None, word_count: int | None = None):
        """
        Initialize ParagraphGenerator.

        Args:
            locale (str): Locale for text generation
            length (int): Optional maximum length in characters
            word_count (int): Optional number of words
        """
        self._text = Text(locale)
        self._length = length
        self._word_count = word_count

    def generate(self) -> str:
        """Generate a text paragraph.

        Returns:
            str: Generated text paragraph
        """
        if self._length:
            # Generate text and ensure exact length by truncating
            txt = self._text.text()
            return txt[: self._length]
        elif self._word_count:
            return " ".join(self._text.words(quantity=self._word_count))
        return self._text.text()

# # DATAMIMIC
# # Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# # This software is licensed under the MIT License.
# # See LICENSE file for the full text of the license.
# # For questions and support, contact: info@rapiddweller.com

# import unittest

# from datamimic_ce.generators.text_generators import ParagraphGenerator


# class TestTextGenerators(unittest.TestCase):
#     """Test suite for text-related generators."""

#     def test_paragraph_generator(self):
#         """Test paragraph generation."""
#         # Test default
#         generator = ParagraphGenerator()
#         text = generator.generate()
#         self.assertIsInstance(text, str)
#         self.assertTrue(len(text) > 0)

#         # Test with length constraint
#         max_length = 100
#         generator = ParagraphGenerator(length=max_length)
#         text = generator.generate()
#         self.assertLessEqual(len(text), max_length)

#         # Test with word count
#         word_count = 10
#         generator = ParagraphGenerator(word_count=word_count)
#         text = generator.generate()
#         self.assertEqual(len(text.split()), word_count)

#         # Test with different locales
#         for locale in ["en", "es", "de"]:
#             generator = ParagraphGenerator(locale=locale)
#             text = generator.generate()
#             self.assertIsInstance(text, str)
#             self.assertTrue(len(text) > 0)

#         # Test with both length and word count (length should take precedence)
#         generator = ParagraphGenerator(length=50, word_count=100)
#         text = generator.generate()
#         self.assertLessEqual(len(text), 50)


# if __name__ == "__main__":
#     unittest.main()

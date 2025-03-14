# # DATAMIMIC
# # Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# # This software is licensed under the MIT License.
# # See LICENSE file for the full text of the license.
# # For questions and support, contact: info@rapiddweller.com

# import unittest

# from datamimic_ce.generators.business_generators import (
#     CreditCardGenerator,
#     CurrencyGenerator,
#     JobTitleGenerator,
# )


# class TestBusinessGenerators(unittest.TestCase):
#     """Test suite for business-related generators."""

#     def test_credit_card_generator(self):
#         """Test credit card number generation."""
#         generator = CreditCardGenerator()
#         number = generator.generate()
#         self.assertIsInstance(number, str)
#         self.assertTrue(number.isdigit())
#         self.assertTrue(13 <= len(number) <= 19)  # Valid credit card length range

#         # Test with specific card type (not implemented yet)
#         generator = CreditCardGenerator(card_type="visa")
#         number = generator.generate()
#         self.assertTrue(number.isdigit())

#     def test_currency_generator(self):
#         """Test currency generation."""
#         # Test code only
#         generator = CurrencyGenerator(code_only=True)
#         code = generator.generate()
#         self.assertIsInstance(code, str)
#         self.assertEqual(len(code), 3)  # ISO currency codes are 3 characters
#         self.assertTrue(code.isupper())

#         # Test with symbol and amount
#         generator = CurrencyGenerator(code_only=False)
#         value = generator.generate()
#         self.assertIsInstance(value, str)
#         self.assertTrue(any(char.isdigit() for char in value))  # Contains numbers
#         self.assertTrue(any(not char.isdigit() for char in value))  # Contains non-digits (symbol)

#     def test_job_title_generator(self):
#         """Test job title generation."""
#         # Test default
#         generator = JobTitleGenerator()
#         title = generator.generate()
#         self.assertIsInstance(title, str)
#         self.assertTrue(len(title) > 0)

#         # Test with different locales
#         for locale in ["en", "es", "de"]:
#             generator = JobTitleGenerator(locale=locale)
#             title = generator.generate()
#             self.assertIsInstance(title, str)
#             self.assertTrue(len(title) > 0)

#         # Test different levels
#         levels = {
#             "junior": "Junior",
#             "senior": "Senior",
#             "manager": "Manager",
#             "executive": "Chief",
#         }
#         for level, prefix in levels.items():
#             generator = JobTitleGenerator(level=level)
#             title = generator.generate()
#             self.assertTrue(
#                 prefix in title,
#                 f"Expected '{prefix}' in job title for level '{level}', got: {title}",
#             )


# if __name__ == "__main__":
#     unittest.main()

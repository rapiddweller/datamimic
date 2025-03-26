# # DATAMIMIC
# # Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# # This software is licensed under the MIT License.
# # See LICENSE file for the full text of the license.
# # For questions and support, contact: info@rapiddweller.com

# import re
# import unittest
# import uuid

# from datamimic_ce.generators.security_generators import (
#     HashGenerator,
#     MnemonicPhraseGenerator,
#     PasswordGenerator,
#     TokenGenerator,
#     UUIDGenerator,
# )


# class TestSecurityGenerators(unittest.TestCase):
#     """Test suite for security-related generators."""

#     def test_uuid_generator(self):
#         """Test UUID generation."""
#         # Test string output
#         generator = UUIDGenerator(as_string=True)
#         uuid_str = generator.generate()
#         self.assertIsInstance(uuid_str, str)
#         self.assertTrue(re.match(r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$", uuid_str))

#         # Test UUID object output
#         generator = UUIDGenerator(as_string=False)
#         uuid_obj = generator.generate()
#         self.assertIsInstance(uuid_obj, uuid.UUID)
#         self.assertEqual(uuid_obj.version, 4)

#     def test_hash_generator(self):
#         """Test hash generation with different algorithms."""
#         # Test SHA-256 (default)
#         generator = HashGenerator()
#         hash_value = generator.generate()
#         self.assertIsInstance(hash_value, str)
#         self.assertEqual(len(hash_value), 64)  # SHA-256 produces 64 hex chars

#         # Test SHA-512
#         generator = HashGenerator(algorithm="sha512")
#         hash_value = generator.generate()
#         self.assertEqual(len(hash_value), 128)  # SHA-512 produces 128 hex chars

#         # Test MD5
#         generator = HashGenerator(algorithm="md5")
#         hash_value = generator.generate()
#         self.assertEqual(len(hash_value), 32)  # MD5 produces 32 hex chars

#         # Test invalid algorithm
#         with self.assertRaises(ValueError):
#             HashGenerator(algorithm="invalid")

#     def test_token_generator(self):
#         """Test token generation in different formats."""
#         # Test hex token
#         generator = TokenGenerator(token_type="hex", entropy=16)
#         token = generator.generate()
#         self.assertIsInstance(token, str)
#         self.assertEqual(len(token), 32)  # 16 bytes = 32 hex chars
#         self.assertTrue(all(c in "0123456789abcdef" for c in token))

#         # Test bytes token
#         generator = TokenGenerator(token_type="bytes", entropy=16)
#         token = generator.generate()
#         self.assertIsInstance(token, bytes)
#         self.assertEqual(len(token), 16)

#         # Test URL-safe token
#         generator = TokenGenerator(token_type="urlsafe", entropy=16)
#         token = generator.generate()
#         self.assertIsInstance(token, str)
#         self.assertTrue(all(c in "-_0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ" for c in token))

#         # Test invalid token type
#         with self.assertRaises(ValueError):
#             TokenGenerator(token_type="invalid")

#     def test_mnemonic_phrase_generator(self):
#         """Test mnemonic phrase generation."""
#         # Test 12-word phrase
#         generator = MnemonicPhraseGenerator(word_count=12)
#         phrase = generator.generate()
#         self.assertIsInstance(phrase, str)
#         self.assertEqual(len(phrase.split()), 12)
#         # Verify all words are from wordlist
#         for word in phrase.split():
#             self.assertIn(word, generator._wordlist)

#         # Test 24-word phrase
#         generator = MnemonicPhraseGenerator(word_count=24)
#         phrase = generator.generate()
#         self.assertEqual(len(phrase.split()), 24)

#         # Test invalid word count
#         with self.assertRaises(ValueError):
#             MnemonicPhraseGenerator(word_count=16)

#     def test_password_generator(self):
#         """Test password generation with different configurations."""
#         # Test default settings
#         generator = PasswordGenerator()
#         password = generator.generate()
#         self.assertIsInstance(password, str)
#         self.assertEqual(len(password), 16)  # Default length
#         # Check for presence of all character types
#         self.assertTrue(any(c.islower() for c in password))
#         self.assertTrue(any(c.isupper() for c in password))
#         self.assertTrue(any(c.isdigit() for c in password))
#         self.assertTrue(any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password))

#         # Test minimum length enforcement
#         generator = PasswordGenerator(length=4)  # Should be raised to 8
#         password = generator.generate()
#         self.assertEqual(len(password), 8)

#         # Test without special characters
#         generator = PasswordGenerator(include_special=False)
#         password = generator.generate()
#         self.assertFalse(any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password))

#         # Test without numbers
#         generator = PasswordGenerator(include_numbers=False)
#         password = generator.generate()
#         self.assertFalse(any(c.isdigit() for c in password))

#         # Test without uppercase
#         generator = PasswordGenerator(include_uppercase=False)
#         password = generator.generate()
#         self.assertFalse(any(c.isupper() for c in password))

#         # Test all options disabled except lowercase (minimum requirement)
#         generator = PasswordGenerator(include_special=False, include_numbers=False, include_uppercase=False)
#         password = generator.generate()
#         self.assertTrue(all(c.islower() for c in password))


# if __name__ == "__main__":
#     unittest.main()

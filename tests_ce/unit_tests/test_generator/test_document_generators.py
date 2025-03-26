# # DATAMIMIC
# # Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# # This software is licensed under the MIT License.
# # See LICENSE file for the full text of the license.
# # For questions and support, contact: info@rapiddweller.com

# import unittest

# from datamimic_ce.domains.common.literal_generators.document_generators import (
#     FilePathGenerator,
#     ISBNGenerator,
#     MIMETypeGenerator,
# )


# class TestDocumentGenerators(unittest.TestCase):
#     """Test suite for document-related generators."""

#     def test_isbn_generator(self):
#         """Test ISBN generation."""
#         # Test ISBN-13
#         generator = ISBNGenerator(isbn_13=True)
#         isbn = generator.generate()
#         self.assertIsInstance(isbn, str)
#         self.assertEqual(len(isbn), 13)
#         self.assertTrue(isbn.isdigit())

#         # Test ISBN-10
#         generator = ISBNGenerator(isbn_13=False)
#         isbn = generator.generate()
#         self.assertIsInstance(isbn, str)
#         self.assertEqual(len(isbn), 10)
#         self.assertTrue(isbn.isdigit() or isbn[-1] in "0123456789X")

#     def test_file_path_generator(self):
#         """Test file path generation."""
#         # Test Unix path
#         generator = FilePathGenerator(file_type="text", platform="unix")
#         path = generator.generate()
#         self.assertIsInstance(path, str)
#         self.assertIn("/", path)
#         self.assertNotIn("\\", path)

#         # Test Windows path
#         generator = FilePathGenerator(file_type="text", platform="windows")
#         path = generator.generate()
#         self.assertIsInstance(path, str)
#         self.assertIn("\\", path)
#         self.assertNotIn("/", path)

#         # Test depth
#         generator = FilePathGenerator(depth=3, platform="unix")
#         path = generator.generate()
#         self.assertEqual(path.count("/"), 3)  # Root counts as one

#         # Test different file types
#         for file_type in ["image", "audio", "video", "data"]:
#             generator = FilePathGenerator(file_type=file_type)
#             path = generator.generate()
#             self.assertTrue(any(ext in path.lower() for ext in [".jpg", ".mp3", ".mp4", ".csv", ".txt"]))

#     def test_mime_type_generator(self):
#         """Test MIME type generation."""
#         # Test default
#         generator = MIMETypeGenerator()
#         mime = generator.generate()
#         self.assertIsInstance(mime, str)
#         self.assertTrue("/" in mime)

#         # Test specific categories
#         categories = {
#             "application": "application/",
#             "audio": "audio/",
#             "image": "image/",
#             "text": "text/",
#             "video": "video/",
#         }
#         for category, prefix in categories.items():
#             generator = MIMETypeGenerator(category=category)
#             mime = generator.generate()
#             self.assertTrue(mime.startswith(prefix))


# if __name__ == "__main__":
#     unittest.main()

# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import random

from mimesis import File
from mimesis.enums import MimeType

from datamimic_ce.generators.generator import Generator


class ISBNGenerator(Generator):
    """Generate ISBN (International Standard Book Number) codes."""

    def __init__(self, isbn_13: bool = True):
        """
        Initialize ISBNGenerator.

        Args:
            isbn_13 (bool): Whether to generate ISBN-13 (True) or ISBN-10 (False)
        """
        self._isbn_13 = isbn_13
        # List of valid ISBN prefixes
        self._isbn13_prefixes = ["978", "979"]
        self._isbn10_prefixes = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]

    def _generate_isbn13(self) -> str:
        # Generate ISBN-13
        prefix = random.choice(self._isbn13_prefixes)
        # Generate 9 random digits
        body = "".join(str(random.randint(0, 9)) for _ in range(9))
        # Calculate check digit (simplified)
        isbn = f"{prefix}{body}"
        total = sum((13 - i) * int(d) for i, d in enumerate(isbn))
        check = (10 - (total % 10)) % 10
        return f"{isbn}{check}"

    def _generate_isbn10(self) -> str:
        # Generate ISBN-10
        prefix = random.choice(self._isbn10_prefixes)
        # Generate 8 random digits
        body = "".join(str(random.randint(0, 9)) for _ in range(8))
        # Calculate check digit (simplified)
        isbn = f"{prefix}{body}"
        total = sum((10 - i) * int(d) for i, d in enumerate(isbn))
        check = (11 - (total % 11)) % 11
        check_char = "X" if check == 10 else str(check)
        return f"{isbn}{check_char}"

    def generate(self) -> str:
        """Generate an ISBN.

        Returns:
            str: Generated ISBN-13 or ISBN-10
        """
        if self._isbn_13:
            return self._generate_isbn13()
        return self._generate_isbn10()


class FilePathGenerator(Generator):
    """Generate file paths with specific extensions and directory depth."""

    def __init__(self, file_type: str = "text", depth: int = 2, platform: str = "unix"):
        """
        Initialize FilePathGenerator.

        Args:
            file_type (str): Type of file ('text', 'image', 'audio', 'video', 'data')
            depth (int): Directory depth
            platform (str): Platform style for paths ('unix', 'windows')
        """
        self._file = File()
        self._type = file_type.lower()
        self._depth = max(1, min(depth, 5))  # Limit depth between 1 and 5
        self._platform = platform.lower()
        # Map file_type to an extension
        self._ext_map = {
            "text": "txt",
            "image": "jpg",
            "audio": "mp3",
            "video": "mp4",
            "data": "csv",
        }
        self._extension = self._ext_map.get(self._type, "txt")

    def generate(self) -> str:
        """Generate a file path.

        Returns:
            str: Generated file path with appropriate separators and extension
        """
        # Simulate a file path: create directory names and use a file name
        dirs = [f"dir{i}" for i in range(1, self._depth + 1)]
        # Generate filename and manually add extension
        base_name = self._file.file_name()
        file_name = f"{base_name}.{self._extension}"
        path = "/".join(dirs + [file_name])
        if self._platform == "windows":
            return path.replace("/", "\\")
        return path


class MIMETypeGenerator(Generator):
    """Generate MIME type strings."""

    def __init__(self, category: str | None = None):
        """
        Initialize MIMETypeGenerator.

        Args:
            category (str): Optional MIME type category ('application', 'audio', 'image', 'text', 'video')
        """
        self._file = File()
        self._category = category.lower() if category else None
        self._mime_map = {
            "application": MimeType.APPLICATION,
            "audio": MimeType.AUDIO,
            "image": MimeType.IMAGE,
            "text": MimeType.TEXT,
            "video": MimeType.VIDEO,
        }

    def generate(self) -> str:
        """Generate a MIME type.

        Returns:
            str: Generated MIME type string
        """
        if self._category and self._category in self._mime_map:
            return self._file.mime_type(type_=self._mime_map[self._category])
        return self._file.mime_type()

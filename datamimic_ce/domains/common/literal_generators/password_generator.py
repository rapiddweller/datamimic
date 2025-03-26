# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import random
import secrets

from datamimic_ce.domain_core.base_literal_generator import BaseLiteralGenerator


class PasswordGenerator(BaseLiteralGenerator):
    """Generate secure passwords with configurable complexity."""

    def __init__(
        self,
        length: int = 16,
        include_special: bool = True,
        include_numbers: bool = True,
        include_uppercase: bool = True,
    ):
        """
        Initialize PasswordGenerator.

        Args:
            length (int): Length of the password (minimum 8)
            include_special (bool): Include special characters
            include_numbers (bool): Include numbers
            include_uppercase (bool): Include uppercase letters
        """
        self._length = max(8, length)  # Minimum length of 8
        self._include_special = include_special
        self._include_numbers = include_numbers
        self._include_uppercase = include_uppercase

        # Define character sets
        self._lowercase = "abcdefghijklmnopqrstuvwxyz"
        self._uppercase = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        self._numbers = "0123456789"
        self._special = "!@#$%^&*()_+-=[]{}|;:,.<>?"

    def generate(self) -> str:
        """Generate a secure password.

        Returns:
            str: Generated password meeting specified requirements
        """
        # Start with lowercase letters
        char_sets = [self._lowercase]

        # Add other character sets based on configuration
        if self._include_uppercase:
            char_sets.append(self._uppercase)
        if self._include_numbers:
            char_sets.append(self._numbers)
        if self._include_special:
            char_sets.append(self._special)

        # Ensure at least one character from each enabled set
        password = []
        for char_set in char_sets:
            password.append(secrets.choice(char_set))

        # Fill the rest randomly
        all_chars = "".join(char_sets)
        password.extend(secrets.choice(all_chars) for _ in range(self._length - len(password)))

        # Shuffle the password
        random.shuffle(password)
        return "".join(password)

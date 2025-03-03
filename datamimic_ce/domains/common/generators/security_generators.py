# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import hashlib
import random
import secrets
import uuid

from datamimic_ce.core.interfaces import Generator


class UUIDGenerator(Generator):
    """Generate UUID4 strings or objects."""

    def __init__(self, as_string: bool = True):
        """
        Initialize UUIDGenerator.

        Args:
            as_string (bool): Whether to return UUID as string (True) or UUID object (False)
        """
        self._as_string = as_string

    def generate(self) -> str | uuid.UUID:
        """Generate a UUID4.

        Returns:
            str | uuid.UUID: UUID4 as string or UUID object based on as_string parameter
        """
        uuid_obj = uuid.uuid4()
        return str(uuid_obj) if self._as_string else uuid_obj


class HashGenerator(Generator):
    """Generate cryptographic hashes using various algorithms."""

    def __init__(self, algorithm: str = "sha256"):
        """
        Initialize HashGenerator.

        Args:
            algorithm (str): Hash algorithm to use ('md5', 'sha1', 'sha256', 'sha512')
        """
        self._algorithm = algorithm.lower()
        if self._algorithm not in hashlib.algorithms_guaranteed:
            raise ValueError(f"Unsupported hash algorithm: {algorithm}")

    def generate(self) -> str:
        """Generate a cryptographic hash.

        Returns:
            str: Hexadecimal string of the hash
        """
        # Generate random data to hash
        data = secrets.token_bytes(32)
        # Get the hash function
        hash_func = getattr(hashlib, self._algorithm)
        # Calculate and return the hash
        return hash_func(data).hexdigest()


class TokenGenerator(Generator):
    """Generate various types of secure tokens."""

    def __init__(self, token_type: str = "hex", entropy: int = 32):
        """
        Initialize TokenGenerator.

        Args:
            token_type (str): Type of token to generate ('hex', 'bytes', 'urlsafe')
            entropy (int): Number of bytes of entropy (default: 32)
        """
        self._token_type = token_type.lower()
        self._entropy = entropy
        if self._token_type not in ["hex", "bytes", "urlsafe"]:
            raise ValueError(f"Unsupported token type: {token_type}")

    def generate(self) -> str | bytes:
        """Generate a secure token.

        Returns:
            str | bytes: Generated token
        """
        if self._token_type == "hex":
            return secrets.token_hex(self._entropy)
        elif self._token_type == "bytes":
            return secrets.token_bytes(self._entropy)
        else:  # urlsafe
            return secrets.token_urlsafe(self._entropy)


class MnemonicPhraseGenerator(Generator):
    """Generate BIP-39 style mnemonic phrases."""

    def __init__(self, word_count: int = 12):
        """
        Initialize MnemonicPhraseGenerator.

        Args:
            word_count (int): Number of words in the phrase (12 or 24)
        """
        if word_count not in [12, 24]:
            raise ValueError("Word count must be either 12 or 24")
        self._word_count = word_count
        # Common BIP-39 wordlist (simplified version)
        self._wordlist = [
            "abandon",
            "ability",
            "able",
            "about",
            "above",
            "absent",
            "absorb",
            "abstract",
            "absurd",
            "abuse",
            "access",
            "accident",
            "account",
            "accuse",
            "achieve",
            "acid",
            "acoustic",
            "acquire",
            "across",
            "act",
            "action",
            "actor",
            "actress",
            "actual",
            "adapt",
            "add",
            "addict",
            "address",
            "adjust",
            "admit",
            "adult",
            "advance",
            "advice",
            "aerobic",
            "affair",
            "afford",
            "afraid",
            "again",
            "age",
            "agent",
            "agree",
            "ahead",
            "aim",
            "air",
            "airport",
            "aisle",
            "alarm",
            "album",
            "alcohol",
            "alert",
            "alien",
            "all",
            "alley",
            "allow",
            "almost",
            "alone",
            "alpha",
            "already",
            "also",
            "alter",
            "always",
            "amateur",
            "amazing",
            "among",
            "amount",
            "amused",
            "analyst",
            "anchor",
            "ancient",
            "anger",
            "angle",
            "angry",
            "animal",
            "ankle",
            "announce",
            "annual",
            "another",
            "answer",
            "antenna",
            "antique",
            "anxiety",
            "any",
            "apart",
            "apology",
            "appear",
            "apple",
            "approve",
            "april",
            "arch",
            "arctic",
            "area",
            "arena",
            "argue",
            "arm",
            "armed",
            "armor",
        ]

    def generate(self) -> str:
        """Generate a mnemonic phrase.

        Returns:
            str: Space-separated list of random words
        """
        return " ".join(random.choices(self._wordlist, k=self._word_count))


class PasswordGenerator(Generator):
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

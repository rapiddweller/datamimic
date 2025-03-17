import hashlib
import secrets

from datamimic_ce.domain_core.base_literal_generator import BaseLiteralGenerator


class HashGenerator(BaseLiteralGenerator):
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

import hashlib
import random

from datamimic_ce.domains.domain_core.base_literal_generator import BaseLiteralGenerator


class HashGenerator(BaseLiteralGenerator):
    """Generate hashes of random data using various algorithms."""

    def __init__(self, algorithm: str = "sha256", rng: random.Random | None = None):
        """
        Initialize HashGenerator.

        Args:
            algorithm (str): Hash algorithm to use ('md5', 'sha1', 'sha256', 'sha512')
            rng: random generator; <setup rngSeed> passes a seeded one
        """
        super().__init__(rng=rng)
        self._algorithm = algorithm.lower()
        if self._algorithm not in hashlib.algorithms_guaranteed:
            raise ValueError(f"Unsupported hash algorithm: {algorithm}")

    def generate(self) -> str:
        """Generate a cryptographic hash.

        Returns:
            str: Hexadecimal string of the hash
        """
        data = self.rng.randbytes(32)
        return hashlib.new(self._algorithm, data).hexdigest()

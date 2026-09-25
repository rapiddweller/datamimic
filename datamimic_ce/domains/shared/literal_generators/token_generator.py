import base64
import random

from datamimic_ce.domains.domain_core.base_literal_generator import BaseLiteralGenerator


class TokenGenerator(BaseLiteralGenerator):
    """Generate hex, bytes or URL-safe tokens."""

    def __init__(self, token_type: str = "hex", entropy: int = 32, rng: random.Random | None = None):
        """
        Initialize TokenGenerator.

        Args:
            token_type (str): Type of token to generate ('hex', 'bytes', 'urlsafe')
            entropy (int): Number of bytes of entropy (default: 32)
            rng: random generator; <setup rngSeed> passes a seeded one
        """
        super().__init__(rng=rng)
        self._token_type = token_type.lower()
        self._entropy = entropy
        if self._token_type not in ["hex", "bytes", "urlsafe"]:
            raise ValueError(f"Unsupported token type: {token_type}")

    def generate(self):
        """Generate a secure token.

        Returns:
            str | bytes: Generated token
        """
        token = self.rng.randbytes(self._entropy)
        if self._token_type == "hex":
            return token.hex()
        if self._token_type == "bytes":
            return token
        return base64.urlsafe_b64encode(token).rstrip(b"=").decode("ascii")

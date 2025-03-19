import secrets

from datamimic_ce.domain_core.base_literal_generator import BaseLiteralGenerator


class TokenGenerator(BaseLiteralGenerator):
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

    def generate(self):
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

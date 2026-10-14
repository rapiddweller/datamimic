import hmac

import pytest

from datamimic_ce.domains.shared.converters.privacy.hash_converter import HashConverter


@pytest.mark.parametrize("key", [b"", b"short", b"a" * 31])
def test_short_hash_key_cannot_be_padded_with_public_salt(key: bytes) -> None:
    with pytest.raises(ValueError, match="at least 32 bytes"):
        HashConverter("sha256", "hex", salt="public" * 20, key=key)


def test_external_hash_key_preserves_standard_hmac() -> None:
    key = b"example-test-material-32-bytes-long"
    converter = HashConverter("sha256", "hex", key=key)
    assert converter.convert("known-input") == hmac.new(key, b"known-input", "sha256").hexdigest()

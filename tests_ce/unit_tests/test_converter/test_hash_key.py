import base64
import hmac
import os
import pickle

import pytest

from datamimic_ce.domains.shared.converters.privacy.hash_converter import HashConverter, derive_field_key
from datamimic_ce.engine.runtime.contracts import PseudonymizationKey
from datamimic_ce.engine.runtime.lifecycle.pseudonymization import resolve_pseudonymization_key


@pytest.mark.parametrize("key", [b"", b"short", b"a" * 31])
def test_short_hash_key_cannot_be_padded_with_public_salt(key: bytes) -> None:
    with pytest.raises(ValueError, match="at least 32 bytes"):
        HashConverter("sha256", "hex", salt="public" * 20, key=key)


def test_external_hash_key_preserves_standard_hmac() -> None:
    key = b"example-test-material-32-bytes-long"
    converter = HashConverter("sha256", "hex", key=key)
    assert converter.convert("known-input") == hmac.new(key, b"known-input", "sha256").hexdigest()


def test_field_key_matches_shared_edition_vector() -> None:
    key = bytes(range(32))
    assert derive_field_key(key, "customers|email") == bytes.fromhex(
        "b41a454f257443c90681a69d8190f4b7da7effc237df69fd11bb0e5852a8dc89"
    )
    converter = HashConverter("sha256", "hex", key=derive_field_key(key, "customers|email"))
    assert converter.convert("known-input") == "cff97023c416b4840c33b6d8baa8983f2bef10527a2f8e606351a414c040d976"


def test_environment_key_is_strict_and_does_not_mutate_environment(monkeypatch) -> None:
    key = bytes(range(32))
    encoded = base64.b64encode(key).decode("ascii")
    monkeypatch.setenv("DM_KEY", encoded)
    before = dict(os.environ)
    resolved = resolve_pseudonymization_key({"pseudonymization_key_env": "DM_KEY"}, None)
    assert resolved == PseudonymizationKey(key)
    assert dict(os.environ) == before


def test_environment_key_lookup_uses_runtime_config_owner(monkeypatch) -> None:
    key = bytes(range(32))
    lookups = []

    def read_environment_value(name: str) -> str | None:
        lookups.append(name)
        return base64.b64encode(key).decode("ascii")

    monkeypatch.setattr(
        "datamimic_ce.engine.runtime.lifecycle.pseudonymization.get_environment_value",
        read_environment_value,
    )

    resolved = resolve_pseudonymization_key({"pseudonymization_key_env": "DM_KEY"}, None)

    assert resolved == PseudonymizationKey(key)
    assert lookups == ["DM_KEY"]


@pytest.mark.parametrize(
    "encoded", ["bad base64", base64.b64encode(b"short").decode(), " " + base64.b64encode(b"x" * 32).decode()]
)
def test_environment_key_rejects_malformed_or_short_value(monkeypatch, encoded: str) -> None:
    monkeypatch.setenv("DM_KEY", encoded)
    with pytest.raises(ValueError):
        resolve_pseudonymization_key({"pseudonymization_key_env": "DM_KEY"}, None)


def test_environment_reference_and_typed_key_cannot_be_combined() -> None:
    with pytest.raises(ValueError, match="either"):
        resolve_pseudonymization_key({"pseudonymization_key_env": "DM_KEY"}, PseudonymizationKey(b"x" * 32))


def test_key_representation_is_redacted() -> None:
    key = PseudonymizationKey(b"SENTINEL" + b"x" * 24)
    assert "SENTINEL" not in repr(key)


def test_key_value_round_trips_through_private_worker_pickle() -> None:
    key = PseudonymizationKey(bytes(range(32)))
    assert pickle.loads(pickle.dumps(key)) == key

# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Hash converter (#226): a keyed HMAC with a host-provided external key."""

import base64
import hashlib
import hmac
from pathlib import Path

import pytest

from datamimic_ce.domains.shared.converters.privacy.hash_converter import derive_field_key
from datamimic_ce.engine.runtime.pseudonymization import PseudonymizationKey
from datamimic_ce.errors import IssueCode, RuntimeConfigError
from datamimic_ce.interfaces.python.data_mimic_test import DataMimicTest

_TEST_DIR = Path(__file__).resolve().parent
_UNKEYED = hashlib.sha256(b"max.mustermann@example.com").hexdigest()


_KEY = bytes(range(32))


def _tokens(filename: str, key: bytes = _KEY) -> list[dict]:
    engine = DataMimicTest(
        test_dir=_TEST_DIR,
        filename=filename,
        capture_test_result=True,
        pseudonymization_key=PseudonymizationKey(key),
    )
    engine.test_with_timer()
    return engine.capture_result()["hashed"]


def _single_token(rows: list[dict]) -> str:
    tokens = {row["token"] for row in rows}
    assert len(tokens) == 1, "the same value must give the same token within a run"
    return tokens.pop()


def test_rng_seed_does_not_affect_external_hash_key() -> None:
    first = _single_token(_tokens("hash_seeded.xml"))
    assert first == _single_token(_tokens("hash_seeded.xml"))
    assert first == _single_token(_tokens("hash_seeded_other.xml"))
    assert first != _UNKEYED
    rows = _tokens("hash_seeded.xml")
    assert len({row["token"] for row in rows}) == 1
    assert len({row["token_again"] for row in rows}) == 1
    assert rows[0]["token"] != rows[0]["token_again"]
    token_base64_key = derive_field_key(_KEY, "hashed|token_base64")
    expected_base64 = hmac.new(token_base64_key, b"max.mustermann@example.com", "sha256").digest()
    assert base64.b64decode(rows[0]["token_base64"]) == expected_base64


def test_external_key_rotation_changes_tokens() -> None:
    assert _single_token(_tokens("hash_unseeded.xml")) != _single_token(_tokens("hash_unseeded.xml", b"R" * 32))


def test_unseeded_workers_share_the_run_key() -> None:
    rows = _tokens("hash_unseeded_workers.xml")
    assert len(rows) == 10
    assert _single_token(rows) != _UNKEYED
    assert len({row["token_base64"] for row in rows}) == 1


def test_environment_reference_resolves_for_unseeded_run(monkeypatch) -> None:
    monkeypatch.setenv("DM_TEST_KEY", base64.b64encode(_KEY).decode("ascii"))
    engine = DataMimicTest(
        test_dir=_TEST_DIR,
        filename="hash_unseeded_workers.xml",
        capture_test_result=True,
        platform_configs={"pseudonymization_key_env": "DM_TEST_KEY"},
    )
    engine.test_with_timer()
    rows = engine.capture_result()["hashed"]
    assert len(rows) == 10
    assert len({row["token"] for row in rows}) == 1


def test_hash_requires_external_key(monkeypatch) -> None:
    monkeypatch.delenv("DATAMIMIC_PSEUDONYMIZATION_KEY", raising=False)
    with pytest.raises(RuntimeConfigError) as error:
        DataMimicTest(test_dir=_TEST_DIR, filename="hash_unseeded.xml", capture_test_result=True).test_with_timer()
    assert error.value.issue_code is IssueCode.RUNTIME_PSEUDONYMIZATION_KEY_INVALID

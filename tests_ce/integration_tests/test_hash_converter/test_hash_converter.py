# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Hash converter (#226): a keyed hash (HMAC). <setup rngSeed> is the key; without a seed each run gets a
random key. Never the plain, recomputable digest of the value."""

import hashlib
from pathlib import Path

import pytest

from datamimic_ce.data_mimic_test import DataMimicTest
from datamimic_ce.datamimic import DataMimic
from datamimic_ce.domains.domain_core.runtime import RunSeed

_TEST_DIR = Path(__file__).resolve().parent
_UNKEYED = hashlib.sha256(b"max.mustermann@example.com").hexdigest()


def _tokens(filename: str) -> list[dict]:
    engine = DataMimicTest(test_dir=_TEST_DIR, filename=filename, capture_test_result=True)
    engine.test_with_timer()
    return engine.capture_result()["hashed"]


def _external_tokens(filename: str, key: str | None = None) -> list[dict]:
    engine = DataMimic(
        descriptor_path=_TEST_DIR / filename,
        platform_props={"secrets": {"pseudonymization_key": key}} if key is not None else {},
        test_mode=True,
    )
    engine.parse_and_execute()
    return engine.capture_test_result()["hashed"]


def _single_token(rows: list[dict], *fields: str) -> str:
    fields = fields or ("token", "token_again")
    tokens = {row[field] for field in fields for row in rows}
    assert len(tokens) == 1, "the same value must give the same token within a run"
    return tokens.pop()


def test_seed_is_the_key() -> None:
    first = _single_token(_tokens("hash_seeded.xml"))
    assert first == _single_token(_tokens("hash_seeded.xml"))
    assert first != _single_token(_tokens("hash_seeded_other.xml"))
    assert first != _UNKEYED


def test_unseeded_runs_get_a_random_key() -> None:
    first = _single_token(_tokens("hash_unseeded.xml"))
    assert first != _single_token(_tokens("hash_unseeded.xml"))
    assert first != _UNKEYED


def test_unseeded_workers_share_the_run_key() -> None:
    rows = _tokens("hash_unseeded_workers.xml")
    assert len(rows) == 10
    assert _single_token(rows) != _UNKEYED
    assert len({row["token_base64"] for row in rows}) == 1


def test_external_key_is_independent_of_generation_seed() -> None:
    key = "external pseudonymization key with 32+ bytes"
    first = _external_tokens("hash_external.xml", key)
    second = _external_tokens("hash_external_other_seed.xml", key)
    assert _single_token(first, "token") == _single_token(second, "token")
    assert [row["generated"] for row in first] != [row["generated"] for row in second]


def test_external_key_rotation_changes_tokens() -> None:
    first = _external_tokens("hash_external.xml", "external pseudonymization key with 32+ bytes")
    rotated = _external_tokens("hash_external.xml", "rotated pseudonymization key with 32+ bytes")
    assert _single_token(first, "token") != _single_token(rotated, "token")


def test_external_key_does_not_change_seeded_generation() -> None:
    baseline = _tokens("hash_generation_seeded.xml")
    external = _external_tokens("hash_external.xml", "external pseudonymization key with 32+ bytes")
    assert [row["generated"] for row in baseline] == [row["generated"] for row in external]


def test_external_key_is_shared_by_workers() -> None:
    rows = _external_tokens("hash_external_workers.xml", "external pseudonymization key with 32+ bytes")
    assert len(rows) == 10
    assert _single_token(rows, "token")


def test_external_key_is_not_in_run_seed_repr() -> None:
    seed = RunSeed.create(None, "external pseudonymization key with 32+ bytes")
    assert "external pseudonymization key" not in repr(seed)


@pytest.mark.parametrize(
    ("filename", "properties", "message"),
    [
        ("hash_external.xml", {}, "pseudonymizationKey property"),
        ("hash_external.xml", {"secrets": {"pseudonymization_key": "too short"}}, "32 UTF-8 bytes"),
        ("hash_external_literal.xml", {}, "must reference a property"),
    ],
)
def test_external_key_fails_before_output(filename: str, properties: dict, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        engine = DataMimic(
            descriptor_path=_TEST_DIR / filename,
            platform_props=properties,
            test_mode=True,
        )
        engine.parse_and_execute()

# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Hash converter (#226): a keyed hash (HMAC). <setup rngSeed> is the key; without a seed each run gets a
random key. Never the plain, recomputable digest of the value."""

import hashlib
from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest

_TEST_DIR = Path(__file__).resolve().parent
_UNKEYED = hashlib.sha256(b"max.mustermann@example.com").hexdigest()


def _tokens(filename: str) -> list[dict]:
    engine = DataMimicTest(test_dir=_TEST_DIR, filename=filename, capture_test_result=True)
    engine.test_with_timer()
    return engine.capture_result()["hashed"]


def _single_token(rows: list[dict]) -> str:
    tokens = {row["token"] for row in rows} | {row["token_again"] for row in rows}
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

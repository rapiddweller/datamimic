# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Proof for the README CE pseudonymization claim.

The README documents seeded pseudonymization as: read a controlled export in
stable order (``distribution="ordered"``) and overwrite each PII field with a
seeded synthetic stand-in via ``<variable entity=...>``. This pins that the
documented model actually runs, replaces the original PII, and replays
identically across runs (the "same source record -> same pseudonymized output"
contract).
"""

from __future__ import annotations

from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest

_TEST_DIR = Path(__file__).resolve().parent
_ORIGINAL_FIRST_NAMES = {"User1", "User2", "User3", "User4", "User5"}


def _run() -> list[dict]:
    engine = DataMimicTest(test_dir=_TEST_DIR, filename="pseudonymize_seeded.xml", capture_test_result=True)
    engine.test_with_timer()
    return engine.capture_result()["customers"]


def test_seeded_pseudonymization_replays_identically_and_replaces_pii() -> None:
    first = _run()
    second = _run()

    assert first, "expected pseudonymized customer rows"
    assert first == second, "seeded pseudonymization must replay identically"

    # The PII columns must be replaced by synthetic stand-ins, not the originals.
    assert all(row["first_name"] not in _ORIGINAL_FIRST_NAMES for row in first), "first_name must be replaced"
    assert all("@acme.com" not in row["email"] for row in first), "email must be replaced"
    assert all(row["iban"].startswith("DE") and "0000000000" not in row["iban"] for row in first), (
        "iban must be a synthetic valid IBAN, not the source placeholder"
    )

# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

from datamimic_ce.authoring.domain.build_verification import compare_captures
from datamimic_ce.authoring.domain.capture import CapturedProduct, CapturedProducts
from datamimic_ce.authoring.projection.evidence import sample_evidence


def test_binary_evidence_identity_and_replay():
    def capture(value):
        return CapturedProducts((CapturedProduct("rows", ({"data": value}, {"data": b""})),), 2)

    first = capture(b"\x00\xff")
    assert sample_evidence(first, 2)[0].rows == (
        {"data": {"type": "binary", "base64": "AP8="}},
        {"data": {"type": "binary", "base64": ""}},
    )
    assert not compare_captures(first, capture(b"\x00\xff"))
    assert compare_captures(first, capture(b"\x00\xfe"))
    assert compare_captures(first, capture("AP8="))

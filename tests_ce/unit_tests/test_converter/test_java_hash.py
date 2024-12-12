# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


import pytest

from datamimic_ce.converter.java_hash_converter import JavaHashConverter


@pytest.mark.parametrize(
    "input, expected_output", [("example text to hash", "c393b696"), ("example text hash", "654e98eb")]
)
def test_java_hash_converter(input, expected_output):
    output = JavaHashConverter().convert(value=input)

    assert output == expected_output, f"should output {expected_output} but got: {output}"

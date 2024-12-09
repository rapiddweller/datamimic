# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/



import pytest

from datamimic_ce.converter.java_hash_converter import JavaHashConverter


@pytest.mark.parametrize(
    "input, expected_output", [("example text to hash", "c393b696"), ("example text hash", "654e98eb")]
)
def test_java_hash_converter(input, expected_output):
    output = JavaHashConverter().convert(value=input)

    assert output == expected_output, f"should output {expected_output} but got: {output}"

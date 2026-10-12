import pytest

from datamimic_ce.domains.api import MaskConverter, MiddleMaskConverter


class _MaskChar(str):
    pass


@pytest.mark.parametrize(
    "make_converter",
    [lambda mask_char: MaskConverter(mask_char), lambda mask_char: MiddleMaskConverter(1, 1, mask_char)],
)
@pytest.mark.parametrize("mask_char", [["*"], b"*", 7, None, "", "**"])
def test_mask_constructors_reject_non_single_character_strings(make_converter, mask_char):
    with pytest.raises(ValueError):
        make_converter(mask_char)


def test_mask_converters_preserve_valid_outputs_and_payload_contract():
    assert MaskConverter().convert("abcd") == "****"
    assert MaskConverter("*").convert("abcd") == "****"
    assert MaskConverter("#").convert("abcd") == "####"
    assert MiddleMaskConverter(1, 1).convert("abcd") == "a**d"
    assert MiddleMaskConverter(1, 1, "#").convert("abcd") == "a##d"
    assert MaskConverter(_MaskChar("#")).convert("abcd") == "####"
    assert MiddleMaskConverter(1, 1, _MaskChar("#")).convert("abcd") == "a##d"
    assert MaskConverter().convert("") == ""
    assert MiddleMaskConverter(1, 1).convert("") == ""
    with pytest.raises(ValueError):
        MaskConverter().convert(7)
    with pytest.raises(ValueError):
        MiddleMaskConverter(1, 1).convert(7)

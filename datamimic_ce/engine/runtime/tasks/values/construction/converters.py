# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import functools

from datamimic_ce.domains.api import (
    AppendConverter,
    Converter,
    CustomConverter,
    CutLengthConverter,
    Date2TimestampConverter,
    DateFormatConverter,
    HashConverter,
    JavaHashConverter,
    LowerCaseConverter,
    MaskConverter,
    MiddleMaskConverter,
    RemoveNoneOrEmptyElementConverter,
    SubstringConverter,
    Timestamp2DateConverter,
    UpperCaseConverter,
)
from datamimic_ce.engine.dsl.api import ConverterEnum
from datamimic_ce.engine.runtime.contexts.context import Context


def _create_converter_from_constructor_str(
    context: Context, constructor_str: str, class_dict: dict[str, object]
) -> Converter:
    class_name = constructor_str.partition("(")[0]
    converter_class = class_dict.get(class_name)
    if converter_class is None:
        converter_class = context.root.get_dynamic_class(class_name)
        if converter_class is None:
            raise ValueError(f"Cannot find converter '{class_name}'")

    if class_name != constructor_str:
        converter = context.evaluate_python_expression(constructor_str, class_dict)
        if isinstance(converter, Converter):
            return converter
        raise TypeError(f"Converter expression '{constructor_str}' did not create a Converter")
    if isinstance(converter_class, type) and issubclass(converter_class, CustomConverter):
        return converter_class(context)
    if callable(converter_class):
        converter = converter_class()
        if isinstance(converter, Converter):
            return converter
    raise TypeError(f"Converter '{class_name}' is not callable")


def create_converter_list(context: Context, converter_str: str | None) -> list[Converter]:
    """Create converters in descriptor order from the semicolon-separated attribute."""
    if converter_str is None or converter_str == "":
        return []
    converters: list[Converter] = []
    for constructor_str in converter_str.split(";"):
        class_dict: dict[str, object] = {
            ConverterEnum.LowerCase.value: LowerCaseConverter,
            ConverterEnum.UpperCase.value: UpperCaseConverter,
            ConverterEnum.DateFormat.value: DateFormatConverter,
            ConverterEnum.Mask.value: MaskConverter,
            ConverterEnum.MiddleMask.value: MiddleMaskConverter,
            ConverterEnum.CutLength.value: CutLengthConverter,
            ConverterEnum.Substring.value: SubstringConverter,
            ConverterEnum.Append.value: AppendConverter,
            ConverterEnum.Hash.value: functools.partial(
                HashConverter, key=context.root.run_seed.key_for("hash-converter")
            ),
            ConverterEnum.JavaHash.value: JavaHashConverter,
            ConverterEnum.Timestamp2Date.value: Timestamp2DateConverter,
            ConverterEnum.Date2Timestamp.value: Date2TimestampConverter,
            ConverterEnum.RemoveNoneOrEmptyElement.value: RemoveNoneOrEmptyElementConverter,
        }
        converters.append(_create_converter_from_constructor_str(context, constructor_str.strip(), class_dict))
    return converters

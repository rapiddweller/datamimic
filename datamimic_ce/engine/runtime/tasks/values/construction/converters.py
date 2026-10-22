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
    derive_field_key,
)
from datamimic_ce.engine.dsl.api import ConverterEnum, Statement
from datamimic_ce.engine.runtime.contexts.context import Context
from datamimic_ce.errors import DomainError, IssueCode, UserErrorBase, task_config_error


def _create_converter_from_constructor_str(
    context: Context, constructor_str: str, class_dict: dict[str, object]
) -> Converter:
    class_name = constructor_str.partition("(")[0]
    converter_class = class_dict.get(class_name)
    diagnostic_name = class_name if converter_class is not None else "converter"
    if converter_class is None:
        converter_class = context.root.get_dynamic_class(class_name)
        if converter_class is None:
            raise task_config_error(
                code=IssueCode.TASK_UNKNOWN_CONVERTER, class_name="(unregistered)", element_label="converter"
            )
        if isinstance(converter_class, type) and issubclass(converter_class, Converter):
            diagnostic_name = converter_class.__name__

    try:
        if class_name != constructor_str:
            converter = context.evaluate_python_expression(
                constructor_str, class_dict, diagnostic_expression=diagnostic_name
            )
        elif isinstance(converter_class, type) and issubclass(converter_class, CustomConverter):
            converter = converter_class(context)
        elif callable(converter_class):
            converter = converter_class()
        else:
            raise TypeError("Configured converter must be callable")
        if isinstance(converter, Converter):
            return converter
        raise TypeError("Converter expression did not create a Converter")
    except (UserErrorBase, DomainError):
        raise
    except (ValueError, TypeError, OverflowError) as error:
        raise task_config_error(
            code=IssueCode.TASK_CONVERTER_FAILED,
            element_tag="converter",
            name=diagnostic_name,
            error=f"{type(error).__name__}; use constructor parameters that create a Converter",
        ) from error


def create_converter_list(context: Context, statement: Statement, converter_str: str | None) -> list[Converter]:
    """Create converters in descriptor order from the semicolon-separated attribute."""
    if converter_str is None or converter_str == "":
        return []
    field_identity = statement.full_name or statement.name or ""
    master_key = context.root.pseudonymization_key
    field_key = derive_field_key(master_key.value, field_identity) if master_key is not None else None
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
            ConverterEnum.Hash.value: functools.partial(HashConverter, key=field_key),
            ConverterEnum.JavaHash.value: JavaHashConverter,
            ConverterEnum.Timestamp2Date.value: Timestamp2DateConverter,
            ConverterEnum.Date2Timestamp.value: Date2TimestampConverter,
            ConverterEnum.RemoveNoneOrEmptyElement.value: RemoveNoneOrEmptyElementConverter,
        }
        converters.append(_create_converter_from_constructor_str(context, constructor_str.strip(), class_dict))
    return converters

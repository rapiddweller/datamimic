# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import re

from pydantic import TypeAdapter, ValidationError

from datamimic_ce.constants.attribute_constants import (
    ATTR_COUNT,
    ATTR_CYCLIC,
    ATTR_DATASET,
    ATTR_DEFAULT_VALUE,
    ATTR_DISTRIBUTION,
    ATTR_ENTITY,
    ATTR_GENERATOR,
    ATTR_IN_DATE_FORMAT,
    ATTR_LOCALE,
    ATTR_MAX_COUNT,
    ATTR_MIN_COUNT,
    ATTR_OUT_DATE_FORMAT,
    ATTR_RNG_SEED,
    ATTR_SCRIPT,
    ATTR_SELECTOR,
    ATTR_SEPARATOR,
    ATTR_SOURCE,
    ATTR_SOURCE_SCRIPTED,
    ATTR_TYPE,
    ATTR_UNIQUE,
    ATTR_VALUES,
    ATTR_WEIGHT_COLUMN,
    ATTR_WEIGHTS,
)
from datamimic_ce.constants.data_type_constants import DATA_TYPE_STRING
from datamimic_ce.enums.distribution_enums import SourceDistribution
from datamimic_ce.utils.string_util import StringUtil

# Parse XML bool attributes exactly like the pydantic bool fields do, so a "before"
# cross-field check can never disagree with the coerced value (e.g. unique="yes").
_BOOL_ADAPTER = TypeAdapter(bool)


def _attr_true(value: object) -> bool:
    if value is None:
        return False
    try:
        return _BOOL_ADAPTER.validate_python(value)
    except ValidationError:
        return False


class ModelUtil:
    @staticmethod
    def check_valid_attributes(values: dict, valid_attributes: set[str]) -> dict:
        """
        Check if element's attributes are in valid attributes set
        :param values:
        :param valid_attributes:
        :return:
        """
        for key in values:
            if key not in valid_attributes:
                raise ValueError(f"invalid attribute '{key}', expect: {list(valid_attributes)}")
        return values

    @staticmethod
    def check_exist_count(values: dict) -> dict:
        """
        Check if 'count' is defined in case 'source' and 'script' are not defined
        :param values:
        :return:
        """
        if all(attr not in values for attr in [ATTR_SOURCE, ATTR_SCRIPT, ATTR_COUNT, ATTR_MIN_COUNT, ATTR_MAX_COUNT]):
            raise ValueError(
                f"Missing attribute '{ATTR_COUNT}' ('{ATTR_COUNT}' might be optional "
                f"in case '{ATTR_SOURCE} and {ATTR_SCRIPT} are not defined')"
            )
        return values

    @staticmethod
    def check_weights_require_values(values: dict) -> dict:
        """'weights' is the companion of 'values' — it is meaningless on its own."""
        if ATTR_WEIGHTS in values and ATTR_VALUES not in values:
            raise ValueError(f"'{ATTR_WEIGHTS}' is only allowed together with '{ATTR_VALUES}'")
        return values

    @staticmethod
    def check_unique_constraints(values: dict) -> dict:
        """'unique' draws distinct values without replacement from a finite pool — an inline
        'values' set or a 'source'. It implies distinct random order, so it only combines with
        distribution='random' (the default) and is incompatible with 'weights' (no weighted
        sampling without replacement), 'cyclic' and ordered/cumulated (no-repeat vs repeat/bell)."""
        if not _attr_true(values.get(ATTR_UNIQUE)):
            return values
        if ATTR_VALUES not in values and ATTR_SOURCE not in values:
            raise ValueError(f"'{ATTR_UNIQUE}' requires '{ATTR_VALUES}' or '{ATTR_SOURCE}' (a finite pool)")
        if ATTR_WEIGHTS in values:
            raise ValueError(f"'{ATTR_UNIQUE}' cannot be combined with '{ATTR_WEIGHTS}'")
        if _attr_true(values.get(ATTR_CYCLIC)):
            raise ValueError(f"'{ATTR_UNIQUE}' cannot be combined with '{ATTR_CYCLIC}' (no-repeat vs repeat)")
        distribution = SourceDistribution.coerce(values.get(ATTR_DISTRIBUTION))
        if distribution is not SourceDistribution.RANDOM:
            raise ValueError(
                f"'{ATTR_UNIQUE}' only combines with distribution='{SourceDistribution.RANDOM.value}' "
                f"(it implies distinct random order), not '{distribution.value}'"
            )
        return values

    @staticmethod
    def check_min_max_count(values: dict, element_tag: str) -> dict:
        """count and minCount/maxCount are mutually exclusive; minCount must not exceed maxCount.
        Shared by <generate> and <nestedKey>."""
        key_set = set(values.keys())
        if ATTR_COUNT in key_set:
            if ATTR_MIN_COUNT in key_set or ATTR_MAX_COUNT in key_set:
                raise ValueError(
                    f"'{ATTR_MIN_COUNT}' and '{ATTR_MAX_COUNT}' must not be defined "
                    f"when '{ATTR_COUNT}' exists in <{element_tag}>"
                )
        elif (
            ATTR_MIN_COUNT in key_set and ATTR_MAX_COUNT in key_set and values[ATTR_MIN_COUNT] > values[ATTR_MAX_COUNT]
        ):
            raise ValueError(
                f"'{ATTR_MIN_COUNT}' value ({values[ATTR_MIN_COUNT]}) "
                f"must be less than or equal to '{ATTR_MAX_COUNT}' value ({values[ATTR_MAX_COUNT]})"
            )
        return values

    @staticmethod
    def _check_valid_additional_attributes(
        values: dict, main_attributes: tuple, additional_attributes: list[str]
    ) -> dict:
        """
        Check if valid additional attributes are defined with main attribute
        :param values:
        :return:
        """
        key_set = set(values.keys())
        if any(attr in key_set for attr in main_attributes):
            return values
        for key in additional_attributes:
            if key in key_set:
                raise ValueError(f"'{key}' is only allowed when one of '{main_attributes}' is defined")
        return values

    @staticmethod
    def check_valid_additional_source_attributes(values: dict) -> dict:
        """
        Check if additional attributes (cyclic, selector,...) are defined with 'source'
        :param values:
        :return:
        """
        return ModelUtil._check_valid_additional_attributes(
            values=values,
            main_attributes=tuple([ATTR_SOURCE]),
            additional_attributes=[
                ATTR_CYCLIC,
                ATTR_SELECTOR,
                ATTR_SEPARATOR,
                ATTR_SOURCE_SCRIPTED,
                ATTR_WEIGHT_COLUMN,
            ],
        )

    @staticmethod
    def check_valid_additional_source_attributes_without_cyclic(values: dict) -> dict:
        """
        Check if additional attributes (selector, separator...) are defined with 'source',
        except cyclic can define without 'source'
        :param values:
        :return:
        """
        return ModelUtil._check_valid_additional_attributes(
            values=values,
            main_attributes=tuple([ATTR_SOURCE]),
            additional_attributes=[
                ATTR_SELECTOR,
                ATTR_SEPARATOR,
                ATTR_SOURCE_SCRIPTED,
                ATTR_WEIGHT_COLUMN,
            ],
        )

    @staticmethod
    def check_valid_additional_generator_entity_attributes(values: dict) -> dict:
        """
        Check if additional attributes (locale, dataset,...) are defined with 'generator'
        :param values:
        :return:
        """
        return ModelUtil._check_valid_additional_attributes(
            values=values,
            main_attributes=(ATTR_GENERATOR, ATTR_ENTITY),
            additional_attributes=[
                ATTR_DATASET,
                ATTR_LOCALE,
                # Demographic and RNG addons
                "ageMin",
                "ageMax",
                "conditionsInclude",
                "conditionsExclude",
                ATTR_RNG_SEED,
            ],
        )

    @staticmethod
    def check_not_empty(value) -> str:
        """
        Check if value is not None
        :param value:
        :return:
        """
        if value == "":
            raise ValueError("must be not empty")
        return value

    @staticmethod
    def check_is_digit(value) -> str:
        """
        Check if value is string of digits
        :param value:
        :return:
        """
        if not value.isdigit():
            raise ValueError(f"must be string of digits, but get: '{value}'")
        return value

    @staticmethod
    def check_valid_data_value(value: str, valid_values: set[str]) -> str:
        """
        Check if data type is in valid set
        :param value:
        :param valid_values:
        :return:
        """
        if value not in valid_values:
            raise ValueError(f"must be one of following values {valid_values}, get unexpected value: '{value}'")
        return value

    @staticmethod
    def check_valid_data_constructor(value: str, valid_values: set[str]) -> str:
        """
        Check if data type is in valid set for constructor class
        :param value:
        :param valid_values:
        :return:
        """
        converter_name = StringUtil.get_class_name_from_constructor_string(value)
        if converter_name not in valid_values:
            raise ValueError(f"must be one of following values {valid_values}, get unexpected value: '{value}'")
        return value

    @staticmethod
    def check_valid_pattern(value: str) -> str:
        """
        Check if attribute "pattern" is valid regex pattern
        :param value:
        :return:
        """
        if value is None:
            return value

        if not isinstance(value, str):
            raise ValueError(f"must be string, but got '{value}' with datatype {type(value).__name__}")
        if value == "" or value.isspace():
            raise ValueError("must be not empty string")
        try:
            re.compile(value)
        except re.error:
            raise ValueError(f"invalid regex pattern: '{value}'") from None

        return value

    @staticmethod
    def check_valid_in_out_date_format(values: dict) -> dict:
        """
        Check whether the attributes 'inDateFormat' and 'outDateFormat' are valid.
        :param values:
        :return:
        """
        key_set = set(values.keys())
        if ATTR_IN_DATE_FORMAT in key_set:
            in_date_value = values.get(ATTR_IN_DATE_FORMAT)
            # inDateFormat value must be string
            if not isinstance(in_date_value, str):
                raise ValueError(
                    f"'{ATTR_IN_DATE_FORMAT}' value type must be string, but got {type(in_date_value).__name__}"
                )
            if in_date_value == "" or in_date_value.isspace():
                raise ValueError(f"'{ATTR_IN_DATE_FORMAT}' value is empty")
        if ATTR_OUT_DATE_FORMAT in key_set:
            out_date_value = values.get(ATTR_OUT_DATE_FORMAT)
            # outDateFormat value must be string
            if not isinstance(out_date_value, str):
                raise ValueError(
                    f"'{ATTR_OUT_DATE_FORMAT}' value type must be string, but got {type(out_date_value).__name__}"
                )
            if out_date_value == "" or out_date_value.isspace():
                raise ValueError(f"'{ATTR_OUT_DATE_FORMAT}' value is empty")
            # generate output data type when outDateFormat is defined must be string
            if ATTR_TYPE in key_set and values.get(ATTR_TYPE) != DATA_TYPE_STRING:
                raise ValueError(
                    f"When '{ATTR_OUT_DATE_FORMAT}' is defined, '{ATTR_TYPE}' "
                    f"must be ignore (implicitly str) or must be '{DATA_TYPE_STRING}'"
                )
        return values

    @staticmethod
    def check_generation_mode_of_source(values: dict) -> dict:
        """
        Check if at most "selector" or "type" is used when using "source"

        :param values:
        :return:
        """
        key_set = set(values.keys())
        if ATTR_SOURCE in key_set and ATTR_TYPE in key_set and ATTR_SELECTOR in key_set:
            raise ValueError(f'Only one "{ATTR_TYPE}" or "{ATTR_SELECTOR}" can be defined in "{ATTR_SOURCE}"')
        return values

    @staticmethod
    def check_valid_default_value(values: dict) -> dict:
        key_set = set(values.keys())
        if ATTR_DEFAULT_VALUE in key_set and ATTR_SCRIPT not in key_set:
            raise ValueError(f"Attribute '{ATTR_DEFAULT_VALUE}' must be defined along with '{ATTR_SCRIPT}'")
        return values

    @staticmethod
    def check_is_digit_or_script(value) -> str:
        """
        Check if value is a string of digits or a {script} expression. The runtime evaluates any
        python expression inside the braces (statement_util.get_int_count), so a computed count like
        ``{customers * orders_per_customer}`` is as valid as a bare ``{var}`` reference.
        """
        if not value.isdigit() and re.match(r"^\{.+\}$", value) is None:
            raise ValueError(f"must be string of digits or script, but get: '{value}'")
        return value

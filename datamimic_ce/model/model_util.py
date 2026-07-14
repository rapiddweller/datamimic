# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import re
from collections.abc import Set as AbstractSet
from typing import TYPE_CHECKING

from pydantic import TypeAdapter, ValidationError

from datamimic_ce.constants.attribute_constants import (
    ATTR_COUNT,
    ATTR_IN_DATE_FORMAT,
    ATTR_ITERATION_SELECTOR,
    ATTR_MAX_COUNT,
    ATTR_MIN_COUNT,
    ATTR_OUT_DATE_FORMAT,
    ATTR_SOURCE,
    ATTR_STORAGE,
    ATTR_TYPE,
)
from datamimic_ce.constants.data_type_constants import DATA_TYPE_STRING
from datamimic_ce.utils.string_util import StringUtil

if TYPE_CHECKING:
    from datamimic_ce.model.constraints import Constraint

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
    def normalize_export_uri(value: str | None) -> str | None:
        """Validate + normalize an exportUri into a safe local output-directory prefix.

        Mirrors DATAMIMIC EE's exportUri policy (prefix only, never a full path/URL): a string,
        no surrounding whitespace, not empty, no URL scheme, no backslash, no control chars - plus a
        traversal guard ('..'), since CE resolves it under the local output/ directory and it must not
        escape. Leading/trailing slashes are stripped. Returns None when unset.
        """
        if value is None:
            return None
        if value != value.strip() or not value.strip():
            raise ValueError("exportUri must not be empty or padded with whitespace")
        cleaned = value.strip()
        if "://" in cleaned:
            raise ValueError(f"exportUri must be a path prefix, not a URL: '{cleaned}'")
        if "\\" in cleaned:
            raise ValueError(f"exportUri must use '/' separators, not backslashes: '{cleaned}'")
        if any(ord(ch) < 32 for ch in cleaned):
            raise ValueError("exportUri must not contain control characters")
        if ".." in cleaned.split("/"):
            raise ValueError(f"exportUri must not traverse with '..': '{cleaned}'")
        return cleaned.strip("/")

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
        """Check if 'count' is defined in case 'source' and 'script' are not defined.

        Delegate to declared constraint: EXIST_COUNT.
        """
        from datamimic_ce.model.constraints import EXIST_COUNT
        return ModelUtil.check_constraints(values, (EXIST_COUNT,))

    @staticmethod
    def check_weights_require_values(values: dict) -> dict:
        """'weights' is the companion of 'values' — it is meaningless on its own.

        Delegate to declared constraint: WEIGHTS_REQUIRE_VALUES.
        """
        from datamimic_ce.model.constraints import WEIGHTS_REQUIRE_VALUES
        return ModelUtil.check_constraints(values, (WEIGHTS_REQUIRE_VALUES,))

    @staticmethod
    def check_unique_constraints(
        values: dict,
        constraints: tuple["Constraint", ...] | None = None,
    ) -> dict:
        """'unique' draws distinct values without replacement from a finite pool — an inline
        'values' set or a 'source'. It implies distinct random order, so it only combines with
        distribution='random' (the default) and is incompatible with 'weights' (no weighted
        sampling without replacement), 'cyclic' and ordered/cumulated (no-repeat vs repeat/bell).

        Delegate entirely to the model's declared unique constraints. Source-backed
        models default to the shared source-selection facts; <key> passes its numeric-
        distribution-specific fact tuple explicitly.
        """
        from datamimic_ce.model.constraints import (
            UNIQUE_DISTRIBUTION_RANDOM,
            UNIQUE_FORBIDS_CYCLIC,
            UNIQUE_FORBIDS_WEIGHTS,
            UNIQUE_REQUIRES_POOL,
        )

        declared = (
            (
                UNIQUE_REQUIRES_POOL,
                UNIQUE_FORBIDS_WEIGHTS,
                UNIQUE_FORBIDS_CYCLIC,
                UNIQUE_DISTRIBUTION_RANDOM,
            )
            if constraints is None
            else constraints
        )
        return ModelUtil.check_constraints(values, declared)

    @staticmethod
    def check_storage_constraints(values: dict) -> dict:
        """'storage' (value/data/iterator) exposes a materialized source POOL - it only makes
        sense on a source-backed <variable> (not entity=/constant=/values=/script=/pattern=/
        string=/generator=, none of which produce a pool). It's also incompatible with
        iterationSelector (per-row dynamic re-query, no stable pool to index into - matches the
        existing precedent that iterationSelector already ignores cyclic=/unique= too) and with a
        weighted-entity source (.wgt.ent.csv - a distribution-sampling source, not a pool to
        expose verbatim)."""
        if ATTR_STORAGE not in values:
            return values
        if ATTR_SOURCE not in values:
            raise ValueError(f"'{ATTR_STORAGE}' requires '{ATTR_SOURCE}' (it exposes a loaded source pool)")
        if values.get(ATTR_ITERATION_SELECTOR) is not None:
            raise ValueError(
                f"'{ATTR_STORAGE}' cannot be combined with '{ATTR_ITERATION_SELECTOR}' "
                "(no stable pool to index into - a fresh query runs per row)"
            )
        source = values.get(ATTR_SOURCE)
        if isinstance(source, str) and source.endswith(".wgt.ent.csv"):
            raise ValueError(f"'{ATTR_STORAGE}' cannot be combined with a weighted-entity source ('{source}')")
        return values

    @staticmethod
    def check_min_max_count(values: dict, element_tag: str) -> dict:
        """count and minCount/maxCount are mutually exclusive; minCount must not exceed maxCount.
        Shared by <generate> and <nestedKey>.

        Facts COUNT_XOR_MIN and COUNT_XOR_MAX are declared for schema, but this method keeps
        the full imperative logic for the element_tag-parameterized message and min>max ordering
        check (value-gated, per review R1).
        """
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
    def check_valid_additional_source_attributes(values: dict) -> dict:
        """Check if additional attributes (cyclic, selector,...) are defined with 'source'.

        Delegate to declared constraints: SOURCE_COMPANIONS_WITH_CYCLIC.
        """
        from datamimic_ce.model.constraints import SOURCE_COMPANIONS_WITH_CYCLIC
        return ModelUtil.check_constraints(values, SOURCE_COMPANIONS_WITH_CYCLIC)

    @staticmethod
    def check_valid_additional_source_attributes_without_cyclic(values: dict) -> dict:
        """Check if additional attributes (selector, separator...) are defined with 'source',
        except cyclic can define without 'source'.

        Delegate to declared constraints: SOURCE_COMPANIONS_WITHOUT_CYCLIC.
        """
        from datamimic_ce.model.constraints import SOURCE_COMPANIONS_WITHOUT_CYCLIC
        return ModelUtil.check_constraints(values, SOURCE_COMPANIONS_WITHOUT_CYCLIC)

    @staticmethod
    def check_valid_additional_generator_entity_attributes(values: dict) -> dict:
        """Check if additional attributes (locale, dataset,...) are defined with 'generator' or 'entity'.

        Delegate to declared constraints: GENERATOR_ENTITY_ADDONS.
        """
        from datamimic_ce.model.constraints import GENERATOR_ENTITY_ADDONS
        return ModelUtil.check_constraints(values, GENERATOR_ENTITY_ADDONS)

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
    def check_valid_data_value(value: str, valid_values: AbstractSet[str]) -> str:
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
        """Delegate the source-gated type/selector XOR to its central fact."""
        from datamimic_ce.model.constraints import SOURCE_MODE_EXCLUSIVE

        return ModelUtil.check_constraints(values, (SOURCE_MODE_EXCLUSIVE,))

    @staticmethod
    def check_valid_default_value(values: dict) -> dict:
        """Default value requires script to be defined.

        Delegate to declared constraint: DEFAULT_VALUE_REQUIRES_SCRIPT.
        """
        from datamimic_ce.model.constraints import DEFAULT_VALUE_REQUIRES_SCRIPT
        return ModelUtil.check_constraints(values, (DEFAULT_VALUE_REQUIRES_SCRIPT,))

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

    @staticmethod
    def check_constraints(values: dict, constraints: tuple["Constraint", ...]) -> dict:
        """Generic executor for declarative constraint facts.

        Walks the constraints tuple; for each fact:
        - SKIPS it if lint_only=True
        - Enforces the fact's semantics, honoring when_true gates via _attr_true()
        - Raises ValueError with the fact's message (if set), else a sensible default

        Returns values unchanged on success (matching every existing ModelUtil check's contract).
        Keys in values are raw XML attribute names — exactly what mode="before" validators receive.

        Args:
            values: Dict of attribute name -> value (raw XML attributes, not coerced)
            constraints: Tuple of Constraint objects

        Returns:
            values (unchanged)

        Raises:
            ValueError: On constraint violation, with the fact's message or a generated default
        """
        from datamimic_ce.model.constraints import (
            AllOrNone,
            AllowedValuesWhen,
            Forbids,
            ForbidsWhenValue,
            MutuallyExclusive,
            MutuallyExclusiveWhen,
            RequiredOneOf,
            Requires,
            RequiresWhenValue,
            ValidValues,
        )

        for fact in constraints:
            # Skip lint-only facts; they are not engine-enforced
            if fact.lint_only:
                continue

            if isinstance(fact, RequiredOneOf):
                if all(attr not in values for attr in fact.attrs):
                    attrs_str = ", ".join(sorted(fact.attrs))
                    msg = fact.message or f"must define one of: {attrs_str}"
                    raise ValueError(msg)

            elif isinstance(fact, MutuallyExclusive):
                present = [attr for attr in fact.attrs if attr in values]
                if len(present) > 1:
                    attrs_str = ", ".join(sorted(fact.attrs))
                    msg = fact.message or f"at most one of [{attrs_str}] may be present, but got: {present}"
                    raise ValueError(msg)

            elif isinstance(fact, MutuallyExclusiveWhen):
                gate_value = values.get(fact.when_attr)
                should_check = (
                    (not fact.when_true and fact.when_attr in values)
                    or (fact.when_true and _attr_true(gate_value))
                )
                present = [attr for attr in fact.attrs if attr in values]
                if should_check and len(present) > 1:
                    attrs_str = ", ".join(sorted(fact.attrs))
                    msg = fact.message or (
                        f"when '{fact.when_attr}' is present, at most one of "
                        f"[{attrs_str}] may be present, but got: {present}"
                    )
                    raise ValueError(msg)

            elif isinstance(fact, Requires):
                # Gate on presence; if when_true=True, gate on truthiness
                attr_value = values.get(fact.attr)
                should_check = (
                    (not fact.when_true and fact.attr in values) or
                    (fact.when_true and _attr_true(attr_value))
                )

                if should_check and all(need not in values for need in fact.needs):
                    needs_str = ", ".join(sorted(fact.needs))
                    msg = fact.message or (
                        f"when '{fact.attr}' is present, at least one of "
                        f"[{needs_str}] must be present"
                    )
                    raise ValueError(msg)

            elif isinstance(fact, RequiresWhenValue):
                if values.get(fact.when_attr) in fact.when_values:
                    escaped = any(attr in values for attr in fact.unless)
                    if not escaped and all(need not in values for need in fact.needs):
                        needs_str = ", ".join(sorted(fact.needs))
                        values_str = ", ".join(sorted(fact.when_values))
                        msg = fact.message or (
                            f"when '{fact.when_attr}' is one of [{values_str}], at least one of "
                            f"[{needs_str}] must be present"
                        )
                        raise ValueError(msg)

            elif isinstance(fact, AllOrNone):
                present = [attr for attr in fact.attrs if attr in values]
                if present and len(present) != len(fact.attrs):
                    attrs_str = ", ".join(sorted(fact.attrs))
                    msg = fact.message or f"either all of [{attrs_str}] must be present, or none"
                    raise ValueError(msg)

            elif isinstance(fact, Forbids):
                # Gate on presence; if when_true=True, gate on truthiness
                attr_value = values.get(fact.attr)
                should_check = (
                    (not fact.when_true and fact.attr in values) or
                    (fact.when_true and _attr_true(attr_value))
                )

                if should_check:
                    # If excludes_when_true=True, excluded attr must also be truthy for violation
                    if fact.excludes_when_true:
                        present_excludes = [attr for attr in fact.excludes if _attr_true(values.get(attr))]
                    else:
                        present_excludes = [attr for attr in fact.excludes if attr in values]
                    if present_excludes:
                        excludes_str = ", ".join(sorted(fact.excludes))
                        msg = fact.message or (
                            f"when '{fact.attr}' is present, none of "
                            f"[{excludes_str}] may be present, but got: "
                            f"{present_excludes}"
                        )
                        raise ValueError(msg)

            elif isinstance(fact, ForbidsWhenValue):
                if values.get(fact.when_attr) in fact.when_values:
                    present_excludes = [attr for attr in fact.excludes if attr in values]
                    if present_excludes:
                        excludes_str = ", ".join(sorted(fact.excludes))
                        values_str = ", ".join(sorted(fact.when_values))
                        msg = fact.message or (
                            f"when '{fact.when_attr}' is one of [{values_str}], none of "
                            f"[{excludes_str}] may be present, but got: {present_excludes}"
                        )
                        raise ValueError(msg)

            elif isinstance(fact, ValidValues) and fact.attr in values:
                # Only validate if the attribute is present
                attr_value = values[fact.attr]
                # Resolve values set (may be callable)
                valid_set = fact.values() if callable(fact.values) else fact.values
                if attr_value not in valid_set:
                    valid_str = ", ".join(sorted(str(v) for v in valid_set))
                    msg = fact.message or (
                        f"'{fact.attr}' value must be one of [{valid_str}], "
                        f"but got: '{attr_value}'"
                    )
                    raise ValueError(msg)

            elif isinstance(fact, AllowedValuesWhen):
                # Gate on when_attr's presence or truthiness
                when_value = values.get(fact.when_attr)
                should_check = (
                    (not fact.when_true and fact.when_attr in values) or
                    (fact.when_true and _attr_true(when_value))
                )

                # Only validate if attr is also present
                if should_check and fact.attr in values:
                    attr_value = values[fact.attr]
                    # Resolve allowed set (may be callable)
                    allowed_set = fact.allowed() if callable(fact.allowed) else fact.allowed
                    if attr_value not in allowed_set:
                        allowed_str = ", ".join(sorted(str(v) for v in allowed_set))
                        msg = (
                            fact.message.replace("{actual_value}", str(attr_value))
                            if fact.message is not None
                            else f"when '{fact.when_attr}' is present, '{fact.attr}' value must be one of "
                            f"[{allowed_str}], but got: '{attr_value}'"
                        )
                        raise ValueError(msg)

        return values

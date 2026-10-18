# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.

from datamimic_ce.errors.catalog.definition import IssueDefinition
from datamimic_ce.errors.codes import IssueCode

ISSUES: list[IssueDefinition] = [
    IssueDefinition(
        code=IssueCode.DATETIME_INVALID_RANGE,
        name="DATETIME_INVALID_RANGE",
        title="Datetime Invalid Range",
        template="Invalid range '{range}' in spec '{spec}'",
        cause="The configuration provides an invalid range '{range}' in spec '{spec}'.",
        resolution="Correct the configuration to a valid value or configuration.",
    ),
    IssueDefinition(
        code=IssueCode.DATETIME_VALUE_OUT_OF_BOUNDS,
        name="DATETIME_VALUE_OUT_OF_BOUNDS",
        title="Datetime Value Out Of Bounds",
        template="Value {value} out of bounds [{low},{high}] in spec '{spec}'",
        cause="A value is outside the allowed bounds for the generator configuration.",
        resolution="Provide values within the allowed bounds or range.",
    ),
    IssueDefinition(
        code=IssueCode.DATETIME_INVALID_VALUE,
        name="DATETIME_INVALID_VALUE",
        title="Datetime Invalid Value",
        template="Invalid value '{value}' in spec '{spec}'",
        cause="The configuration provides an invalid value '{value}' in spec '{spec}'.",
        resolution="Correct the configuration to a valid value or configuration.",
    ),
    IssueDefinition(
        code=IssueCode.DATETIME_MONTHS_ENTRIES_RANGE,
        name="DATETIME_MONTHS_ENTRIES_RANGE",
        title="Datetime Months Entries Range",
        template="months entries must be 1..12",
        cause="The configuration violates the requirement that months entries must be 1..12.",
        resolution="Provide values within the allowed bounds or range.",
    ),
    IssueDefinition(
        code=IssueCode.DATETIME_WEEKDAY_RANGE_INVALID,
        name="DATETIME_WEEKDAY_RANGE_INVALID",
        title="Datetime Weekday Range Invalid",
        template="Invalid weekday range '{token}'",
        cause="The configuration provides an invalid weekday range '{token}'.",
        resolution="Correct the configuration to a valid value or configuration.",
    ),
    IssueDefinition(
        code=IssueCode.DATETIME_WEEKDAY_TOKEN_INVALID,
        name="DATETIME_WEEKDAY_TOKEN_INVALID",
        title="Datetime Weekday Token Invalid",
        template="Invalid weekday token '{token}'",
        cause="The configuration provides an invalid weekday token '{token}'.",
        resolution="Correct the configuration to a valid value or configuration.",
    ),
    IssueDefinition(
        code=IssueCode.DATETIME_WEEKDAY_INDEX_BOUNDS,
        name="DATETIME_WEEKDAY_INDEX_BOUNDS",
        title="Datetime Weekday Index Bounds",
        template="Weekday index {value} out of bounds [0,6]",
        cause="An error occurred during generator configuration.",
        resolution="Review the configuration and retry.",
    ),
    IssueDefinition(
        code=IssueCode.DATETIME_WEEKDAY_LIST_RANGE,
        name="DATETIME_WEEKDAY_LIST_RANGE",
        title="Datetime Weekday List Range",
        template="weekday list values must be 0..6",
        cause="The configuration violates the requirement that weekday list values must be 0..6.",
        resolution="Provide values within the allowed bounds or range.",
    ),
    IssueDefinition(
        code=IssueCode.DATETIME_WEEKDAY_LIST_INVALID,
        name="DATETIME_WEEKDAY_LIST_INVALID",
        title="Datetime Weekday List Invalid",
        template="weekday list values must be ints or weekday names",
        cause=("The configuration violates the requirement that weekday list values must be ints or weekday names."),
        resolution="Correct the configuration to a valid value or configuration.",
    ),
    IssueDefinition(
        code=IssueCode.DATETIME_DOM_VALUE_RANGE,
        name="DATETIME_DOM_VALUE_RANGE",
        title="Datetime Dom Value Range",
        template="dom values must be 1..31 or 'last'",
        cause="The configuration violates the requirement that dom values must be 1..31 or 'last'.",
        resolution="Provide values within the allowed bounds or range.",
    ),
    IssueDefinition(
        code=IssueCode.DATETIME_DOM_LIST_INVALID,
        name="DATETIME_DOM_LIST_INVALID",
        title="Datetime Dom List Invalid",
        template="dom list values must be ints or 'last'",
        cause=("The configuration violates the requirement that dom list values must be ints or 'last'."),
        resolution="Correct the configuration to a valid value or configuration.",
    ),
    IssueDefinition(
        code=IssueCode.DATETIME_DOM_RANGE_INVALID,
        name="DATETIME_DOM_RANGE_INVALID",
        title="Datetime Dom Range Invalid",
        template="Invalid dom range '{token}'",
        cause="The configuration provides an invalid dom range '{token}'.",
        resolution="Correct the configuration to a valid value or configuration.",
    ),
    IssueDefinition(
        code=IssueCode.DATETIME_DOM_TOKEN_INVALID,
        name="DATETIME_DOM_TOKEN_INVALID",
        title="Datetime Dom Token Invalid",
        template="Invalid dom token '{token}'",
        cause="The configuration provides an invalid dom token '{token}'.",
        resolution="Correct the configuration to a valid value or configuration.",
    ),
    IssueDefinition(
        code=IssueCode.DATETIME_HOURS_PRESET_UNKNOWN,
        name="DATETIME_HOURS_PRESET_UNKNOWN",
        title="Datetime Hours Preset Unknown",
        template="Unknown hours_preset '{preset}' (supported: office, night, flat)",
        cause=("The configuration references an unknown hours_preset '{preset}' (supported: office, night, flat)."),
        resolution="Correct the configuration to a valid value or configuration.",
    ),
    IssueDefinition(
        code=IssueCode.DATETIME_GRANULARITY_RANGE,
        name="DATETIME_GRANULARITY_RANGE",
        title="Datetime Granularity Range",
        template="granularity must be in 1..{limit}",
        cause="The configuration violates the requirement that granularity must be in 1..{limit}.",
        resolution="Provide values within the allowed bounds or range.",
    ),
    IssueDefinition(
        code=IssueCode.DATETIME_WEIGHTS_LENGTH,
        name="DATETIME_WEIGHTS_LENGTH",
        title="Datetime Weights Length",
        template="{name} must have length {expected_len}",
        cause=("The configuration violates the requirement that {name} must have length {expected_len}."),
        resolution="Review the configuration and retry.",
    ),
    IssueDefinition(
        code=IssueCode.DATETIME_WEIGHTS_NEGATIVE,
        name="DATETIME_WEIGHTS_NEGATIVE",
        title="Datetime Weights Negative",
        template="{name} must be non-negative",
        cause="The configuration violates the requirement that {name} must be non-negative.",
        resolution="Review the configuration and retry.",
    ),
    IssueDefinition(
        code=IssueCode.DATETIME_WEIGHTS_SUM_ZERO,
        name="DATETIME_WEIGHTS_SUM_ZERO",
        title="Datetime Weights Sum Zero",
        template="{name} must not sum to zero",
        cause="The configuration violates the requirement that {name} must not sum to zero.",
        resolution="Review the configuration and retry.",
    ),
    IssueDefinition(
        code=IssueCode.DATETIME_MAX_BEFORE_MIN,
        name="DATETIME_MAX_BEFORE_MIN",
        title="Datetime Max Before Min",
        template="max_datetime must be greater than or equal to min_datetime",
        cause=(
            "The configuration violates the requirement that max_datetime must be greater than or "
            "equal to min_datetime."
        ),
        resolution="Review the configuration and retry.",
    ),
    IssueDefinition(
        code=IssueCode.DATETIME_NO_ELIGIBLE_DATES,
        name="DATETIME_NO_ELIGIBLE_DATES",
        title="Datetime No Eligible Dates",
        template="No eligible dates within the range after applying month/weekday/dom weights.",
        cause="An error occurred during generator configuration.",
        resolution="Review the configuration and retry.",
    ),
    IssueDefinition(
        code=IssueCode.GENERATOR_CREATE_FAILED,
        name="GENERATOR_CREATE_FAILED",
        title="Generator Create Failed",
        template=("Cannot create generator '{class_name}' for element '{element_name}'{descriptor}: {error}"),
        cause=(
            "The system could not create generator '{class_name}' for element '{element_name}'{descriptor}: {error}."
        ),
        resolution="Review the configuration and retry.",
    ),
]

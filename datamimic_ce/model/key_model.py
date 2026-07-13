# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from datamimic_ce.constants.attribute_constants import (
    ATTR_CONDITION,
    ATTR_CONSTANT,
    ATTR_CONVERTER,
    ATTR_DATABASE,
    ATTR_DEFAULT_VALUE,
    ATTR_DISTRIBUTION,
    ATTR_GENERATOR,
    ATTR_GRANULARITY,
    ATTR_IN_DATE_FORMAT,
    ATTR_MAX,
    ATTR_MAX_LENGTH,
    ATTR_MIME_TYPE,
    ATTR_MIN,
    ATTR_MIN_LENGTH,
    ATTR_NAME,
    ATTR_NULL_QUOTA,
    ATTR_OUT_DATE_FORMAT,
    ATTR_PATTERN,
    ATTR_SCRIPT,
    ATTR_SELECTOR,
    ATTR_SEPARATOR,
    ATTR_SOURCE,
    ATTR_STRING,
    ATTR_TYPE,
    ATTR_UNIQUE,
    ATTR_VALUES,
    ATTR_VARIABLE_PREFIX,
    ATTR_VARIABLE_SUFFIX,
    ATTR_WEIGHTS,
)
from datamimic_ce.constants.data_type_constants import (
    DATA_TYPE_BINARY,
    DATA_TYPE_BOOL,
    DATA_TYPE_DECIMAL,
    DATA_TYPE_FLOAT,
    DATA_TYPE_INT,
    DATA_TYPE_STRING,
)
from datamimic_ce.model.constraints import (
    SOURCE_COMPANIONS_WITH_CYCLIC,
    UNIQUE_FORBIDS_WEIGHTS,
    UNIQUE_REQUIRES_POOL,
    WEIGHTS_REQUIRE_VALUES,
    Constraint,
    MutuallyExclusive,
    RequiredOneOf,
    ValidValues,
    constraints_schema_extra,
)
from datamimic_ce.model.model_util import ModelUtil

# Declared facts (SPOT): each set lives ONCE here, consumed by BOTH __constraints__
# and the enforcing validator body. Dynamic messages (interpolating the clashing
# attrs/value) stay in the validator, so these facts carry message=None.
_GENERATION_REQUIRED = RequiredOneOf(
    frozenset((
        ATTR_TYPE,
        ATTR_SOURCE,
        ATTR_VALUES,
        ATTR_SCRIPT,
        ATTR_GENERATOR,
        ATTR_CONSTANT,
        ATTR_PATTERN,
        ATTR_STRING,
    )),
)
_GENERATION_EXCLUSIVE = MutuallyExclusive(
    frozenset((
        ATTR_SOURCE,
        ATTR_VALUES,
        ATTR_SCRIPT,
        ATTR_GENERATOR,
        ATTR_CONSTANT,
        ATTR_PATTERN,
    )),
)
_TYPE_VALUES = ValidValues(
    ATTR_TYPE,
    frozenset((
        DATA_TYPE_STRING,
        DATA_TYPE_INT,
        DATA_TYPE_FLOAT,
        DATA_TYPE_DECIMAL,
        DATA_TYPE_BOOL,
        DATA_TYPE_BINARY,
    )),
)


class KeyModel(BaseModel):
    # Declared cross-field constraints (read by validators and exposed to schema via json_schema_extra)
    __constraints__: ClassVar[tuple[Constraint, ...]] = (
        # Shared constraints (used by KeyModel, VariableModel, GenerateModel)
        WEIGHTS_REQUIRE_VALUES,
        UNIQUE_REQUIRES_POOL,
        UNIQUE_FORBIDS_WEIGHTS,
        # Source companions (cyclic/selector/separator/sourceScripted/weightColumn require source)
        *SOURCE_COMPANIONS_WITH_CYCLIC,
        # Two-tier generation-mode facts + type valid-values (enforced by in-model validators,
        # which read these same constants; their messages are dynamic, so message=None here)
        _GENERATION_REQUIRED,
        _GENERATION_EXCLUSIVE,
        _TYPE_VALUES,
    )
    model_config = ConfigDict(json_schema_extra=constraints_schema_extra)

    name: str = Field(
        ...,
        description="Field name in the generated record/export (the JSON/CSV/XML column or key name).",
        examples=["id", "email", "status"],
    )
    type: str | None = Field(
        None,
        description="Data type of the key's generated value. Combine with min/max (numeric range), "
        "minLength/maxLength (string or binary length), or mimeType (binary).",
        examples=["string", "int", "float", "decimal", "bool", "binary"],
    )
    min: str | None = Field(
        None,
        description="Minimum value for a numeric range key (type=\"int\"/\"float\"/\"decimal\"); combine "
        "with max and optionally granularity/distribution to shape an IntegerGenerator/FloatGenerator.",
        examples=["0", "18"],
    )
    max: str | None = Field(
        None,
        description="Maximum value for a numeric range key (type=\"int\"/\"float\"/\"decimal\"); combine "
        "with min and optionally granularity/distribution to shape an IntegerGenerator/FloatGenerator.",
        examples=["99", "1000"],
    )
    granularity: str | None = Field(
        None,
        description="Step width of the numeric grid for a type=\"float\"/\"decimal\" range key (e.g. "
        "0.5); ignored for type=\"int\".",
        examples=["0.1", "0.5"],
    )
    # NumberDistribution for numeric range keys (type=int/float/decimal with min/max),
    # e.g. distribution="cumulated" - the native form of IntegerGenerator(..., distribution=...)
    distribution: str | None = Field(
        None,
        description="NumberDistribution for numeric range keys (type=\"int\"/\"float\"/\"decimal\" with "
        "min/max) - the native form of IntegerGenerator(..., distribution=...). Requires type to be a "
        "numeric type and min and/or max to be set.",
        examples=["uniform", "cumulated", "step", "shuffle"],
    )
    min_length: str | None = Field(
        None,
        alias=ATTR_MIN_LENGTH,
        description="Minimum length for a type=\"string\" (StringGenerator) or type=\"binary\" "
        "(BinaryGenerator) payload.",
        examples=["5", "1"],
    )
    mime_type: str | None = Field(
        None,
        alias=ATTR_MIME_TYPE,
        description="MIME signature to prefix a type=\"binary\" payload with a real magic-number "
        "header (MIME-sniffable); must be a supported signature.",
        examples=["image/png", "application/pdf"],
    )
    max_length: str | None = Field(
        None,
        alias=ATTR_MAX_LENGTH,
        description="Maximum length for a type=\"string\" (StringGenerator) or type=\"binary\" "
        "(BinaryGenerator) payload.",
        examples=["12", "16"],
    )
    source: str | None = Field(
        None,
        description="Weighted CSV data source for this key (must end in 'wgt.csv'); rows are drawn "
        "with replacement, weighted by the file's weight column. Not supported together with unique.",
        examples=["segments.wgt.csv"],
    )
    selector: str | None = Field(
        None,
        description="Selector used when reading 'source'. Requires 'source'.",
        examples=["SELECT * FROM table"],
    )
    separator: str | None = Field(
        None,
        description="Field separator for the weighted CSV 'source' (defaults to the project's default "
        "separator).",
        examples=[",", ";", "|"],
    )
    values: str | None = Field(
        None,
        description="Comma-separated list of literal values to pick from for the key.",
        examples=["1,2,3", "'A','B','C'"],
    )
    weights: str | None = Field(
        None,
        description="Comma-separated relative weights, one per 'values' entry, for weighted random "
        "selection. Requires 'values'.",
        examples=["0.7,0.2,0.1", "5,3,2"],
    )
    unique: bool | None = Field(
        None,
        description="Emit each picked value at most once (distinct selection without replacement). "
        "Requires 'values' or 'source', cannot combine with 'weights', and only combines with the "
        "default random distribution.",
        examples=[True, False],
    )
    script: str | None = Field(
        None,
        description="Python expression evaluated to compute the key's value.",
        examples=["random.randint(1, 100)", "fake.name()"],
    )
    generator: str | None = Field(
        None,
        description="Predefined generator constructor used to produce the key's value; validated "
        "against the generator registry.",
        examples=["IncrementGenerator", "DateTimeGenerator(random=True)"],
    )
    constant: str | None = Field(
        None,
        description="Constant, literal value for the key (same value every record).",
        examples=["Constant Value"],
    )
    condition: str | None = Field(
        None,
        description="Python condition expression gating whether this key is generated for the current "
        "record (default: always generated). Evaluated per record; the key is omitted when false.",
        examples=["is_active is True", "value == 5 or value == 10"],
    )
    converter: str | None = Field(
        None,
        description="Converter(s) applied to transform the generated key value before export; "
        "validated against the converter registry.",
        examples=["UpperCase", "LowerCase", "DateFormat", "Mask", "MiddleMask", "CutLength", "Append", "Hash"],
    )
    pattern: str | None = Field(
        None,
        description="Regular-expression pattern used to generate the key's string value.",
        examples=["[A-Z][a-z]{5,12}", "[0-9]{5}"],
    )
    in_date_format: str | None = Field(
        None,
        alias=ATTR_IN_DATE_FORMAT,
        description="Input date format used to parse a source/script date value before converting it "
        "to outDateFormat.",
        examples=["%Y-%m-%d", "%d-%b-%Y", "%d.%m.%Y %H:%M:%S.%f", "epoch"],
    )
    out_date_format: str | None = Field(
        None,
        alias=ATTR_OUT_DATE_FORMAT,
        description="Output date format the key's date value is rendered in.",
        examples=["%Y-%m-%d", "%d-%b-%Y", "%d.%m.%Y %H:%M:%S.%f", "epoch"],
    )
    default_value: str | None = Field(
        None,
        alias=ATTR_DEFAULT_VALUE,
        description="Fallback value used when 'script' evaluates to None/fails. Requires 'script'.",
        examples=["None", "unknown"],
    )
    null_quota: float | None = Field(
        None,
        alias=ATTR_NULL_QUOTA,
        description="Probability in [0, 1] that this key is assigned a null value instead of a "
        "generated one. Default is 0 (never null).",
        examples=[0, 0.5, 1],
    )
    database: str | None = Field(
        None,
        description="Database client id, e.g. for a SequenceTableGenerator that reads a real DB "
        "sequence.",
        examples=["db"],
    )
    string: str | None = Field(
        None,
        alias=ATTR_STRING,
        description="String for the variable data generation.",
        examples=["find: __key_name__, __key_name_2__ "],
    )
    variable_prefix: str | None = Field(
        None,
        alias=ATTR_VARIABLE_PREFIX,
        description="Prefix before field's name for string in key generation.",
        examples=["${", "++", "--", "@", "{"],
    )
    variable_suffix: str | None = Field(
        None,
        alias=ATTR_VARIABLE_SUFFIX,
        description="Suffix after field's name for string in key generation.",
        examples=["++", "--", "@", "}"],
    )

    @model_validator(mode="before")
    @classmethod
    def check_attribute_valid_attributes(cls, values: dict):
        return ModelUtil.check_valid_attributes(
            values=values,
            valid_attributes={
                ATTR_NAME,
                ATTR_TYPE,
                ATTR_MIN,
                ATTR_MAX,
                ATTR_GRANULARITY,
                ATTR_DISTRIBUTION,
                ATTR_MIME_TYPE,
                ATTR_MIN_LENGTH,
                ATTR_MAX_LENGTH,
                ATTR_SOURCE,
                ATTR_SELECTOR,
                ATTR_SEPARATOR,
                ATTR_VALUES,
                ATTR_WEIGHTS,
                ATTR_UNIQUE,
                ATTR_SCRIPT,
                ATTR_GENERATOR,
                ATTR_CONSTANT,
                ATTR_CONDITION,
                ATTR_CONVERTER,
                ATTR_PATTERN,
                ATTR_IN_DATE_FORMAT,
                ATTR_OUT_DATE_FORMAT,
                ATTR_DEFAULT_VALUE,
                ATTR_NULL_QUOTA,
                ATTR_DATABASE,
                ATTR_STRING,
                ATTR_VARIABLE_PREFIX,
                ATTR_VARIABLE_SUFFIX,
            },
        )

    @model_validator(mode="before")
    @classmethod
    def validate_weights_require_values(cls, values: dict):
        return ModelUtil.check_weights_require_values(values)

    @model_validator(mode="before")
    @classmethod
    def validate_unique_constraints(cls, values: dict):
        return ModelUtil.check_unique_constraints(values)

    @model_validator(mode="before")
    @classmethod
    def validate_additional_source_attributes(cls, values: dict):
        return ModelUtil.check_valid_additional_source_attributes(values=values)

    @model_validator(mode="before")
    @classmethod
    def validate_distribution_requires_numeric_range(cls, values: dict):
        """distribution= on a <key> shapes a NUMERIC RANGE draw (the native form of
        IntegerGenerator/FloatGenerator's distribution kwarg) - anything else is a config
        error to fail loudly on, never to silently ignore."""
        if ATTR_DISTRIBUTION not in values:
            return values
        from datamimic_ce.enums.distribution_enums import NumberDistribution

        value = values[ATTR_DISTRIBUTION]
        valid = sorted(member.value for member in NumberDistribution)
        if value not in valid:
            raise ValueError(
                f"unknown distribution '{value}' on <key> - numeric range keys support: {', '.join(valid)}"
            )
        if values.get(ATTR_TYPE) not in (DATA_TYPE_INT, DATA_TYPE_FLOAT, DATA_TYPE_DECIMAL):
            raise ValueError(
                f"'distribution' on a <key> shapes a numeric range and needs type=\"int\"/\"float\"/\"decimal\" "
                f"with min/max, but got type=\"{values.get(ATTR_TYPE)}\""
            )
        if ATTR_MIN not in values and ATTR_MAX not in values:
            raise ValueError(
                "'distribution' on a <key> needs a range to shape - add min= and/or max="
            )
        return values

    @model_validator(mode="before")
    @classmethod
    def validate_generator_mode(cls, values: dict):
        """
        Check if <key> define only one valid generation option.

        Reads the declared facts _GENERATION_REQUIRED / _GENERATION_EXCLUSIVE;
        message construction stays here (it interpolates the clashing modes).
        """
        key_set = set(values.keys())
        generator_option = set(_GENERATION_REQUIRED.attrs)
        # Check if at least one of following attribute is existed to generate <key> value
        if all(key not in key_set for key in generator_option):
            raise ValueError(f"Must defined one of following attributes {generator_option}")
        # Check if at most one generation mode is defined
        generation_mode = set(_GENERATION_EXCLUSIVE.attrs)
        first_mode = None
        for mode in generation_mode:
            if mode in key_set:
                if first_mode is None:
                    # Set first found mode
                    first_mode = mode
                else:
                    # Raise error if finding 2 modes in same element
                    raise ValueError(
                        f"Must defined only one of following attributes {generation_mode}, "
                        f"but got: {first_mode} & {mode}"
                    )
        return values

    @model_validator(mode="before")
    @classmethod
    def validate_in_out_date_format(cls, values: dict):
        """
        Validate attribute "inDateFormat" and "outDateFormat"
        :param values:
        :return:
        """
        return ModelUtil.check_valid_in_out_date_format(values=values)

    @model_validator(mode="before")
    @classmethod
    def validate_default_value(cls, values: dict):
        """
        Validate attribute "fallback"
        :param values:
        :return:
        """
        return ModelUtil.check_valid_default_value(values)

    @field_validator("type")
    @classmethod
    def validate_data_type(cls, value):
        """
        Validate attribute "type" — reads the declared _TYPE_VALUES fact.
        :param value:
        :return:
        """
        return ModelUtil.check_valid_data_value(
            value=value,
            valid_values=set(_TYPE_VALUES.values),
        )

    @field_validator("name")
    @classmethod
    def validate_name(cls, value):
        return ModelUtil.check_not_empty(value=value)

    @field_validator("null_quota")
    @classmethod
    def validate_null_quota(cls, value):
        if value > 1 or value < 0:
            raise ValueError(f"must be in range [0, 1], but get invalid value: {value}")
        return value

    @field_validator("pattern")
    @classmethod
    def validate_pattern(cls, value):
        """
        Validate attribute "pattern"
        :param value:
        :return:
        """
        return ModelUtil.check_valid_pattern(value)

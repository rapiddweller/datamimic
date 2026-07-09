# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pydantic import BaseModel, Field, field_validator, model_validator

from datamimic_ce.constants.attribute_constants import (
    ATTR_CONVERTER,
    ATTR_COUNT,
    ATTR_CYCLIC,
    ATTR_DISTRIBUTION,
    ATTR_END,
    ATTR_EXPORT_URI,
    ATTR_INTERVAL,
    ATTR_MAX_COUNT,
    ATTR_MIN_COUNT,
    ATTR_MP_PLATFORM,
    ATTR_MULTIPROCESSING,
    ATTR_NAME,
    ATTR_NUM_PROCESS,
    ATTR_OFFSET,
    ATTR_PAGE_SIZE,
    ATTR_SCRIPT,
    ATTR_SELECTOR,
    ATTR_SEPARATOR,
    ATTR_SOURCE,
    ATTR_SOURCE_ENTITY,
    ATTR_SOURCE_SCRIPTED,
    ATTR_START,
    ATTR_TARGET,
    ATTR_TARGET_ENTITY,
    ATTR_TYPE,
    ATTR_UNIQUE,
    ATTR_VARIABLE_PREFIX,
    ATTR_VARIABLE_SUFFIX,
)
from datamimic_ce.constants.element_constants import EL_GENERATE
from datamimic_ce.model.model_util import ModelUtil

_TIMESERIES_ATTRS: frozenset[str] = frozenset({ATTR_START, ATTR_END, ATTR_INTERVAL})


class GenerateModel(BaseModel):
    name: str
    count: str | None = None
    min_count: int | None = Field(None, alias=ATTR_MIN_COUNT)
    max_count: int | None = Field(None, alias=ATTR_MAX_COUNT)
    source: str | None = None
    cyclic: bool | None = None
    # Skip the first N source rows before any windowing (Benerator parity). File sources only;
    # count default, cyclic wrap and page windows all operate on the post-offset region.
    offset: int | None = None
    unique: bool | None = None
    type: str | None = None
    selector: str | None = None
    separator: str | None = None
    source_scripted: bool | None = Field(None, alias=ATTR_SOURCE_SCRIPTED)
    target: str | None = None
    # Explicit physical entity to read/write (table/collection). Precedence: sourceEntity/targetEntity
    # -> type -> name; absent -> existing behaviour. See StatementUtil.resolve_source/target_entity.
    source_entity: str | None = Field(None, alias=ATTR_SOURCE_ENTITY)
    target_entity: str | None = Field(None, alias=ATTR_TARGET_ENTITY)
    page_size: int | None = Field(None, alias=ATTR_PAGE_SIZE)
    multiprocessing: bool | None = None
    export_uri: str | None = Field(None, alias=ATTR_EXPORT_URI)
    distribution: str | None = None
    variable_prefix: str | None = Field(None, alias=ATTR_VARIABLE_PREFIX)
    variable_suffix: str | None = Field(None, alias=ATTR_VARIABLE_SUFFIX)
    converter: str | None = None
    num_process: int | None = Field(None, alias=ATTR_NUM_PROCESS)
    script: str | None = Field(None, alias=ATTR_SCRIPT)
    mp_platform: str | None = Field(None, alias=ATTR_MP_PLATFORM)
    # Time-series iterator (ISO 8601 start/end/interval). See _TIMESERIES_ATTRS.
    start: str | None = None
    end: str | None = None
    interval: str | None = None

    @model_validator(mode="before")
    @classmethod
    def check_generate_valid_attributes(cls, values: dict):
        return ModelUtil.check_valid_attributes(
            values=values,
            valid_attributes={
                ATTR_TARGET,
                ATTR_COUNT,
                ATTR_MIN_COUNT,
                ATTR_MAX_COUNT,
                ATTR_CYCLIC,
                ATTR_OFFSET,
                ATTR_UNIQUE,
                ATTR_NAME,
                ATTR_SELECTOR,
                ATTR_SEPARATOR,
                ATTR_SOURCE,
                ATTR_SOURCE_ENTITY,
                ATTR_TARGET_ENTITY,
                ATTR_SOURCE_SCRIPTED,
                ATTR_TYPE,
                ATTR_PAGE_SIZE,
                ATTR_MULTIPROCESSING,
                ATTR_EXPORT_URI,
                ATTR_DISTRIBUTION,
                ATTR_VARIABLE_PREFIX,
                ATTR_VARIABLE_SUFFIX,
                ATTR_CONVERTER,
                ATTR_NUM_PROCESS,
                ATTR_SCRIPT,
                ATTR_MP_PLATFORM,
                ATTR_START,
                ATTR_END,
                ATTR_INTERVAL,
            },
        )

    @model_validator(mode="before")
    @classmethod
    def validate_unique_constraints(cls, values: dict):
        return ModelUtil.check_unique_constraints(values)

    @model_validator(mode="before")
    @classmethod
    def validate_offset_requires_source(cls, values: dict):
        if ATTR_OFFSET in values and ATTR_SOURCE not in values:
            raise ValueError("'offset' requires a 'source' - it skips the first N source rows")
        return values

    @field_validator("offset")
    @classmethod
    def validate_offset_non_negative(cls, value):
        if value is not None and value < 0:
            raise ValueError(f"'offset' must be >= 0, but got: {value}")
        return value

    @field_validator("source_entity", "target_entity")
    @classmethod
    def _entity_not_blank(cls, value: str | None) -> str | None:
        """A physical entity name must be meaningful: strip it, and reject blank (a real user error -
        an empty sourceEntity/targetEntity means the user forgot the value, not "use the default")."""
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            raise ValueError("sourceEntity/targetEntity must not be blank")
        # targetEntity becomes a file basename for file exporters; path separators would escape the
        # output directory. An entity is a single table/collection/basename, never a path.
        if "/" in stripped or "\\" in stripped or ".." in stripped:
            raise ValueError(f"sourceEntity/targetEntity must be a plain entity name, not a path: '{stripped}'")
        return stripped

    @field_validator("export_uri")
    @classmethod
    def _normalize_export_uri(cls, value: str | None) -> str | None:
        """exportUri is a safe local output-directory prefix (see ModelUtil.normalize_export_uri)."""
        return ModelUtil.normalize_export_uri(value)

    @model_validator(mode="before")
    @classmethod
    def validate_timeseries_window(cls, values: dict):
        """`start`/`end`/`interval` must be set together — all or none."""
        present = _TIMESERIES_ATTRS & values.keys()
        if present and present != _TIMESERIES_ATTRS:
            missing = _TIMESERIES_ATTRS - present
            raise ValueError(f"Time-series attributes must be set together; missing: {sorted(missing)}")
        return values

    @model_validator(mode="before")
    @classmethod
    def validate_count_and_source(cls, values: dict):
        # In time-series mode count is optional (default 1 series); otherwise enforce the
        # existing rule that count is required unless source/script supplies the length.
        if _TIMESERIES_ATTRS & values.keys():
            return values
        return ModelUtil.check_exist_count(values=values)

    @model_validator(mode="before")
    @classmethod
    def validate_min_max_count(cls, values: dict):
        return ModelUtil.check_min_max_count(values, EL_GENERATE)

    @model_validator(mode="before")
    @classmethod
    def validate_additional_source_attributes(cls, values: dict):
        return ModelUtil.check_valid_additional_source_attributes(values=values)

    @model_validator(mode="before")
    @classmethod
    def validate_count_and_source_and_script(cls, values: dict):
        """
        Validate at most "type" or "selector" can be defined with "source"
        :param value:
        :return:
        """
        return ModelUtil.check_generation_mode_of_source(values)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value):
        return ModelUtil.check_not_empty(value=value)

    @field_validator("count")
    @classmethod
    def validate_count(cls, value):
        return ModelUtil.check_is_digit_or_script(value=value)

    # NOTE: no distribution validator — GenerateStatement validates via
    # SourceDistribution.coerce (random/ordered/cumulated) at construction.

# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

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
from datamimic_ce.model.constraints import (
    GENERATE_OFFSET_REQUIRES_SOURCE,
    GENERATE_UNIQUE_CONSTRAINTS,
    SOURCE_DISTRIBUTION_VALUES,
    TIMESERIES_ALL_OR_NONE,
    Constraint,
    constraints_schema_extra,
    element_constraints,
    resolved_values,
)
from datamimic_ce.model.model_util import ModelUtil

_TIMESERIES_ATTRS: frozenset[str] = TIMESERIES_ALL_OR_NONE.attrs


class GenerateModel(BaseModel):
    # Declared cross-field constraints
    __constraints__: ClassVar[tuple[Constraint, ...]] = element_constraints(EL_GENERATE)
    model_config = ConfigDict(json_schema_extra=constraints_schema_extra(__constraints__))

    name: str = Field(
        ...,
        description="Statement name — the product/table name generated records are grouped and "
        "exported under, and the name other statements reference it by (e.g. generator=\"<name>\").",
        examples=["customers", "orders"],
    )
    count: str | None = Field(
        None,
        description="Number of records to generate: a literal digit string or a '{script}' expression "
        "evaluated at runtime. Required unless source/script supplies the rows, or minCount/maxCount is "
        "used instead (count is mutually exclusive with minCount/maxCount).",
        examples=["100", "{customer_count}"],
    )
    min_count: int | None = Field(
        None,
        alias=ATTR_MIN_COUNT,
        description="Minimum number of records to generate. Mutually exclusive with count; combine with "
        "maxCount for a randomized row count range (minCount must not exceed maxCount).",
        examples=[1, 10],
    )
    max_count: int | None = Field(
        None,
        alias=ATTR_MAX_COUNT,
        description="Maximum number of records to generate. Mutually exclusive with count; combine with "
        "minCount for a randomized row count range (minCount must not exceed maxCount).",
        examples=[10, 100],
    )
    source: str | None = Field(
        None,
        description="Source of data to read for generation: a file path (.csv/.json/.xlsx/.xml/"
        ".dbunit.xml), a <memstore> id, or a <database>/<mongodb> client id.",
        examples=["customers.csv", "mem", "db"],
    )
    cyclic: bool | None = Field(
        None,
        description="Wrap around and re-read the source from the start once exhausted, instead of "
        "silently capping at the source length when count exceeds it.",
        examples=[True, False],
    )
    # Skip the first N source rows before any windowing (migration parity). File sources only;
    # count default, cyclic wrap and page windows all operate on the post-offset region.
    offset: int | None = Field(
        None,
        ge=0,
        description="Skip the first N source rows before any windowing (migration parity). File sources "
        "only; count default, cyclic wrap and page windows all operate on the post-offset region. "
        "Requires 'source'.",
        examples=[0, 100],
    )
    unique: bool | None = Field(
        None,
        description="Emit each source row at most once (distinct selection without replacement). "
        "Requires a finite pool ('source'), only combines with distribution='random' (the default), and "
        "is incompatible with 'cyclic' and weighted distributions.",
        examples=[True, False],
    )
    type: str | None = Field(
        None,
        description="Explicit physical entity/producer to read or write, used as a fallback in the "
        "sourceEntity/targetEntity -> type -> name precedence chain (e.g. selects which producing "
        "<generate>'s rows to read back from a <memstore> source). At most one of type or selector may "
        "be combined with source.",
        examples=["orders"],
    )
    selector: str | None = Field(
        None,
        description="Query/selector used to read from source (e.g. SQL for a database client, or a "
        "MongoDB find/aggregate expression). At most one of type or selector may be combined with source.",
        examples=["SELECT * FROM customers", "find: orders, filter: {status: 'open'}"],
    )
    separator: str | None = Field(
        None,
        description="Field separator for delimited file sources (default '|'); set separator=\",\" to "
        "read a comma-separated CSV.",
        examples=[",", ";", "|"],
    )
    source_scripted: bool | None = Field(
        None,
        alias=ATTR_SOURCE_SCRIPTED,
        description="Evaluate 'source' as a Python script expression rather than a literal path/id "
        "(advanced; requires source).",
        examples=[True, False],
    )
    target: str | None = Field(
        None,
        description="Target output(s) for generated data: a file exporter (CSV, JSON, XML, XLSX, TXT, "
        "DbUnit), ConsoleExporter, a <memstore> id, a database/mongodb client id, or "
        "clientId.upsert/update/delete. Comma-separate multiple targets.",
        examples=["CSV", "JSON", "mem", "db.upsert", "mem,JSON"],
    )
    # Explicit physical entity to read/write (table/collection). Precedence: sourceEntity/targetEntity
    # -> type -> name; absent -> existing behaviour. See StatementUtil.resolve_source/target_entity.
    source_entity: str | None = Field(
        None,
        alias=ATTR_SOURCE_ENTITY,
        description="Explicit physical entity to read/write (table/collection). Precedence: "
        "sourceEntity/targetEntity -> type -> name; absent -> existing behaviour. See "
        "StatementUtil.resolve_source/target_entity.",
        examples=["customers", "public.customers"],
    )
    target_entity: str | None = Field(
        None,
        alias=ATTR_TARGET_ENTITY,
        description="Explicit physical entity to read/write (table/collection). Precedence: "
        "sourceEntity/targetEntity -> type -> name; absent -> existing behaviour. See "
        "StatementUtil.resolve_source/target_entity.",
        examples=["customers_out", "public.customers_out"],
    )
    page_size: int | None = Field(
        None,
        alias=ATTR_PAGE_SIZE,
        description="Number of rows processed per page when streaming a source/target; keeps memory "
        "usage roughly O(pageSize) for large datasets.",
        examples=[1000, 5000],
    )
    multiprocessing: bool | None = Field(
        None,
        description="Enable multi-process generation for this statement to use multiple CPU cores. "
        "Incompatible with a seeded run (rngSeed forces single-process for reproducibility) and with "
        "finite positional numeric sequences (worker-local iterator state would duplicate values).",
        examples=[True, False],
    )
    export_uri: str | None = Field(
        None,
        alias=ATTR_EXPORT_URI,
        description="Explicit output-directory prefix for exporters that support file paths (a safe "
        "local path, not a URL; '..' is rejected). See ModelUtil.normalize_export_uri.",
        examples=["output/customers", "output/export"],
    )
    distribution: str | None = Field(
        None,
        description="Distribution/order for reading the source pool: 'random' (default, whole pool "
        "loaded into memory), 'ordered' (source order, streams page by page), or 'cumulated' "
        "(bell-shaped weighted draw; loads the whole pool).",
        examples=["random", "ordered", "cumulated"],
    )
    variable_prefix: str | None = Field(
        None,
        alias=ATTR_VARIABLE_PREFIX,
        description="Prefix before field's name for query select data in selector element",
        examples=["${", "++", "--", "@", "{"],
    )
    variable_suffix: str | None = Field(
        None,
        alias=ATTR_VARIABLE_SUFFIX,
        description="Suffix after field's name for query select data in selector element",
        examples=["++", "--", "@", "}"],
    )
    converter: str | None = Field(
        None,
        description="Converter(s) applied to transform generated element data before export; validated "
        "against the converter registry.",
        examples=["RemoveNoneOrEmptyElement"],
    )
    num_process: int | None = Field(
        None,
        alias=ATTR_NUM_PROCESS,
        description="Number of worker processes to use when multiprocessing is enabled.",
        examples=[2, 4, 8],
    )
    script: str | None = Field(
        None,
        alias=ATTR_SCRIPT,
        description="Python expression evaluated to produce an in-memory iterable of rows for this "
        "generate statement (an alternative to source); its length can satisfy count when count is "
        "omitted.",
        examples=["[{'id': i} for i in range(10)]"],
    )
    mp_platform: str | None = Field(
        None,
        alias=ATTR_MP_PLATFORM,
        description="Multiprocessing start method override (advanced).",
        examples=["fork", "spawn"],
    )
    # Time-series iterator (ISO 8601 start/end/interval). See _TIMESERIES_ATTRS.
    start: str | None = Field(
        None,
        description="Time-series window start (ISO 8601 datetime). Set together with end/interval to "
        "turn this <generate> into a time-series iterator.",
        examples=["2025-01-01T00:00:00"],
    )
    end: str | None = Field(
        None,
        description="Time-series window end (ISO 8601 datetime). Must be strictly after start.",
        examples=["2025-01-02T00:00:00"],
    )
    interval: str | None = Field(
        None,
        description="Time-series tick interval (ISO 8601 duration). Spacing between consecutive ts.now "
        "ticks.",
        examples=["PT1H", "PT15M", "P1D"],
    )

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
        return ModelUtil.check_unique_constraints(values, GENERATE_UNIQUE_CONSTRAINTS)

    @model_validator(mode="before")
    @classmethod
    def validate_offset_requires_source(cls, values: dict):
        # Enforce the declared fact (static message lives on the fact).
        return ModelUtil.check_constraints(values, (GENERATE_OFFSET_REQUIRES_SOURCE,))

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

    @field_validator("distribution")
    @classmethod
    def validate_distribution(cls, value: str | None) -> str | None:
        if value is not None:
            ModelUtil.check_valid_data_value(value, resolved_values(SOURCE_DISTRIBUTION_VALUES))
        return value

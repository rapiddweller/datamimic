# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from dataclasses import dataclass
from typing import Final

from datamimic_ce.engine.dsl.model.values.scalar.key_model import KeyModel
from datamimic_ce.engine.dsl.model.values.variables.variable_model import VariableModel
from datamimic_ce.engine.dsl.statements.base.composite_statement import CompositeStatement
from datamimic_ce.engine.dsl.vocabulary.constants.attribute_constants import (
    ATTR_GRANULARITY,
    ATTR_MAX,
    ATTR_MAX_LENGTH,
    ATTR_MIN,
    ATTR_MIN_LENGTH,
)


@dataclass(frozen=True)
class GeneratorArguments:
    """The generator arguments that <key>, <element> and <variable> write as attributes (#456, #459, #460)."""

    min: str | None
    max: str | None
    granularity: str | None
    min_length: str | None
    max_length: str | None

    @classmethod
    def of(cls, model: KeyModel | VariableModel) -> "GeneratorArguments":
        return GeneratorArguments(model.min, model.max, model.granularity, model.min_length, model.max_length)

    def lengths(self) -> tuple[tuple[str, str, str | None], ...]:
        """minLength/maxLength are the min_len/max_len parameters of StringGenerator and BinaryGenerator, in the
        type= form and in the generator= attribute form."""
        return ((ATTR_MIN_LENGTH, "min_len", self.min_length), (ATTR_MAX_LENGTH, "max_len", self.max_length))

    def written(self) -> list[tuple[str, str, str]]:
        """(attribute, generator parameter, text) of each attribute the element writes."""
        # The range attributes share their names with the generator parameters they set.
        every = (
            (ATTR_MIN, "min", self.min),
            (ATTR_MAX, "max", self.max),
            (ATTR_GRANULARITY, "granularity", self.granularity),
            *self.lengths(),
        )
        return [(attribute, parameter, text) for attribute, parameter, text in every if text is not None]


class KeyStatement(CompositeStatement):
    def __init__(self, model: KeyModel, parent_stmt: CompositeStatement):
        name = model.name
        super().__init__(name, parent_stmt)
        self._name: str = name
        self._condition = model.condition
        self._constant = model.constant
        self._converter = model.converter
        self._generator = model.generator
        self._in_date_format = model.in_date_format
        self._out_date_format = model.out_date_format
        self._script = model.script
        self._source = model.source
        self._separator = model.separator
        self._type = model.type
        self.generator_arguments: Final = GeneratorArguments.of(model)
        self._distribution = model.distribution
        self._mime_type = model.mime_type
        self._values = model.values
        self._weights = model.weights
        self._unique = model.unique
        self._default_value = model.default_value
        self._null_quota = model.null_quota
        self._pattern = model.pattern
        self._database = model.database
        self._variable_prefix = model.variable_prefix
        self._variable_suffix = model.variable_suffix
        self._string = model.string

    @property
    def name(self) -> str:
        return self._name

    @property
    def type(self) -> str | None:
        return self._type

    @property
    def distribution(self) -> str | None:
        return self._distribution

    @property
    def mime_type(self) -> str | None:
        return self._mime_type

    @property
    def values(self) -> str | None:
        return self._values

    @property
    def weights(self) -> str | None:
        return self._weights

    @property
    def unique(self) -> bool | None:
        return self._unique

    @property
    def script(self) -> str | None:
        return self._script

    @property
    def constant(self) -> str | None:
        return self._constant

    @property
    def generator(self) -> str | None:
        return self._generator

    @property
    def source(self) -> str | None:
        return self._source

    @property
    def separator(self) -> str | None:
        return self._separator

    @property
    def condition(self) -> str | None:
        return self._condition

    @property
    def converter(self) -> str | None:
        return self._converter

    @property
    def in_date_format(self) -> str | None:
        return self._in_date_format

    @property
    def out_date_format(self) -> str | None:
        return self._out_date_format

    @property
    def default_value(self) -> str | None:
        return self._default_value

    @property
    def null_quota(self) -> float | None:
        return self._null_quota

    @property
    def pattern(self) -> str | None:
        return self._pattern

    @property
    def database(self) -> str | None:
        return self._database

    @property
    def string(self) -> str | None:
        return self._string

    @property
    def variable_prefix(self) -> str | None:
        return self._variable_prefix

    @property
    def variable_suffix(self) -> str | None:
        return self._variable_suffix

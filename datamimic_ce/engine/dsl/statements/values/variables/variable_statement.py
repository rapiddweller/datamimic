# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import re

from datamimic_ce.engine.dsl.model.values.variables.variable_model import VariableModel
from datamimic_ce.engine.dsl.statements.base.statement import Statement
from datamimic_ce.engine.dsl.vocabulary.constants.attribute_constants import (
    ATTR_ITERATION_SELECTOR,
    ATTR_SELECTOR,
)
from datamimic_ce.engine.dsl.vocabulary.enums.distribution_enums import SourceDistribution


class VariableStatement(Statement):
    def __init__(
        self,
        model: VariableModel,
        parent_stmt: Statement,
        is_global_var: bool | None = False,
    ):
        name = model.name
        super().__init__(name, parent_stmt)
        self._name: str = name
        self._constant = model.constant
        self._converter = model.converter
        self._cyclic = model.cyclic
        self._dataset = model.dataset
        self._entity = model.entity
        self._generator = model.generator
        self._min = model.min
        self._max = model.max
        self._granularity = model.granularity
        self._min_length = model.min_length
        self._max_length = model.max_length
        self._locale = model.locale
        self._in_date_format = model.in_date_format
        self._out_date_format = model.out_date_format
        self._script = model.script
        self._source = model.source
        self._source_script = model.source_script
        self._selector = model.selector
        self._separator = model.separator
        self._type = model.type
        self._source_entity = model.source_entity
        self._values = model.values
        self._weights = model.weights
        self._unique = model.unique
        self._weight_column = model.weight_column
        self._iteration_selector = model.iteration_selector
        self._default_value = model.default_value
        self._is_global_variable = is_global_var
        self._pattern = model.pattern
        # Real type at the boundary (absent = RANDOM); domain logic never sees None.
        self._distribution = SourceDistribution.coerce(model.distribution)
        self._variable_prefix = model.variable_prefix
        self._variable_suffix = model.variable_suffix
        self._string = model.string
        self._storage = model.storage
        # Demographic + RNG extensions
        self._age_min = model.age_min
        self._age_max = model.age_max
        self._conditions_include = model.conditions_include
        self._conditions_exclude = model.conditions_exclude
        self._rng_seed = model.rng_seed

    @property
    def name(self) -> str:
        return self._name

    @property
    def source(self) -> str | None:
        return self._source

    @property
    def selector(self) -> str | None:
        return self._selector

    @property
    def type(self) -> str | None:
        return self._type

    @property
    def source_entity(self) -> str | None:
        return self._source_entity

    @property
    def cyclic(self) -> bool | None:
        return self._cyclic

    @property
    def source_script(self) -> bool | None:
        return self._source_script

    @property
    def entity(self) -> str | None:
        return self._entity

    @property
    def script(self) -> str | None:
        return self._script

    @property
    def weight_column(self) -> str | None:
        return self._weight_column

    @property
    def separator(self) -> str | None:
        return self._separator

    @property
    def dataset(self) -> str | None:
        return self._dataset

    @property
    def locale(self) -> str | None:
        return self._locale

    @property
    def generator(self) -> str | None:
        return self._generator

    @property
    def min(self) -> str | None:
        return self._min

    @property
    def max(self) -> str | None:
        return self._max

    @property
    def granularity(self) -> str | None:
        return self._granularity

    @property
    def min_length(self) -> str | None:
        return self._min_length

    @property
    def max_length(self) -> str | None:
        return self._max_length

    @property
    def in_date_format(self) -> str | None:
        return self._in_date_format

    @property
    def out_date_format(self) -> str | None:
        return self._out_date_format

    @property
    def converter(self) -> str | None:
        return self._converter

    @property
    def constant(self) -> str | None:
        return self._constant

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
    def iteration_selector(self) -> str | None:
        return self._iteration_selector

    @property
    def blank_selector_attribute(self) -> str | None:
        """The selector attribute that is given but blank: it then holds no query (#397)."""
        # re, not str.strip: ArchKeel counts str method calls as unresolved and the budget is fixed; same whitespace.
        if self._selector is not None and re.fullmatch(r"\s*", self._selector):
            return ATTR_SELECTOR
        if self._iteration_selector is not None and re.fullmatch(r"\s*", self._iteration_selector):
            return ATTR_ITERATION_SELECTOR
        return None

    @property
    def default_value(self) -> str | None:
        return self._default_value

    @property
    def is_global_variable(self) -> bool | None:
        return self._is_global_variable

    @property
    def pattern(self) -> str | None:
        return self._pattern

    @property
    def distribution(self) -> SourceDistribution:
        return self._distribution

    @property
    def variable_prefix(self) -> str | None:
        return self._variable_prefix

    @property
    def variable_suffix(self) -> str | None:
        return self._variable_suffix

    @property
    def string(self) -> str | None:
        return self._string

    @property
    def storage(self) -> str | None:
        return self._storage

    # Demographic + RNG getters
    @property
    def age_min(self) -> int | None:
        return self._age_min

    @property
    def age_max(self) -> int | None:
        return self._age_max

    @property
    def conditions_include(self) -> str | None:
        return self._conditions_include

    @property
    def conditions_exclude(self) -> str | None:
        return self._conditions_exclude

    @property
    def rng_seed(self) -> int | None:
        return self._rng_seed

# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.engine.dsl.model.values.structured.nested_key_model import NestedKeyModel
from datamimic_ce.engine.dsl.statements.base.composite_statement import CompositeStatement
from datamimic_ce.engine.dsl.statements.base.statement import Statement
from datamimic_ce.engine.dsl.vocabulary.enums.distribution_enums import SourceDistribution


class NestedKeyStatement(CompositeStatement):
    def __init__(self, model: NestedKeyModel, parent_stmt: Statement):
        name = model.name
        super().__init__(name, parent_stmt)
        self._name: str = name
        self._type = model.type
        self._count = model.count
        self._source = model.source
        self._source_entity = model.source_entity
        self._source_script = model.source_script
        self._cyclic = model.cyclic
        self._separator = model.separator
        self._condition = model.condition
        self._script = model.script
        self._min_count = model.min_count
        self._max_count = model.max_count
        self._default_value = model.default_value
        # Real type at the boundary (absent = RANDOM); domain logic never sees None.
        self._distribution = SourceDistribution.coerce(model.distribution)
        self._converter = model.converter
        self._variable_prefix = model.variable_prefix
        self._variable_suffix = model.variable_suffix

    @property
    def name(self) -> str:
        return self._name

    @property
    def type(self) -> str | None:
        return self._type

    @property
    def count(self) -> str | None:
        return self._count

    @property
    def source(self) -> str | None:
        return self._source

    @property
    def source_entity(self) -> str | None:
        return self._source_entity

    @property
    def source_script(self) -> bool | None:
        return self._source_script

    @property
    def cyclic(self) -> bool | None:
        return self._cyclic

    @property
    def separator(self) -> str | None:
        return self._separator

    @property
    def condition(self) -> str | None:
        return self._condition

    @property
    def script(self) -> str | None:
        return self._script

    @property
    def min_count(self) -> int | None:
        return self._min_count

    @property
    def max_count(self) -> int | None:
        return self._max_count

    @property
    def default_value(self) -> str | None:
        return self._default_value

    @property
    def distribution(self) -> SourceDistribution:
        return self._distribution

    @property
    def converter(self) -> str | None:
        return self._converter

    @property
    def variable_prefix(self) -> str | None:
        return self._variable_prefix

    @property
    def variable_suffix(self) -> str | None:
        return self._variable_suffix

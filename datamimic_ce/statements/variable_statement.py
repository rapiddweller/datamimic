# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from datamimic_ce.model.variable_model import VariableModel
from datamimic_ce.statements.statement import Statement


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
        self._locale = model.locale
        self._in_date_format = model.in_date_format
        self._out_date_format = model.out_date_format
        self._script = model.script
        self._source = model.source
        self._source_script = model.source_script
        self._selector = model.selector
        self._separator = model.separator
        self._type = model.type
        self._values = model.values
        self._weight_column = model.weight_column
        self._iteration_selector = model.iteration_selector
        self._default_value = model.default_value
        self._is_global_variable = is_global_var
        self._pattern = model.pattern
        self._distribution = model.distribution
        self._variable_prefix = model.variable_prefix
        self._variable_suffix = model.variable_suffix
        self._string = model.string

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
    def in_date_format(self) -> str | None:
        return self._in_date_format

    @property
    def out_date_format(self) -> str | None:
        return self._out_date_format

    @property
    def converter(self) -> str | None:
        return self._converter

    @property
    def constant(self):
        return self._constant

    @property
    def values(self):
        return self._values

    @property
    def iteration_selector(self) -> str | None:
        return self._iteration_selector

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
    def distribution(self) -> str | None:
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

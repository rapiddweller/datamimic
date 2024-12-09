# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/

from datamimic_ce.contexts.context import Context
from datamimic_ce.model.nested_key_model import NestedKeyModel
from datamimic_ce.statements.composite_statement import CompositeStatement
from datamimic_ce.statements.statement import Statement
from datamimic_ce.statements.statement_util import StatementUtil


class NestedKeyStatement(CompositeStatement):
    def __init__(self, model: NestedKeyModel, parent_stmt: Statement):
        name = model.name
        super().__init__(name, parent_stmt)
        self._name = name
        self._type = model.type
        self._count = model.count
        self._source = model.source
        self._source_script = model.source_script
        self._cyclic = model.cyclic
        self._separator = model.separator
        self._condition = model.condition
        self._script = model.script
        self._min_count = model.min_count
        self._max_count = model.max_count
        self._default_value = model.default_value
        self._distribution = model.distribution
        self._converter = model.converter
        self._variable_prefix = model.variable_prefix
        self._variable_suffix = model.variable_suffix

    @property
    def type(self):
        return self._type

    @property
    def count(self):
        return self._count

    def get_int_count(self, ctx: Context):
        """
        Get count as int value of NestedKeyStatement

        :param ctx:
        :return:
        """
        return StatementUtil.get_int_count(count=self._count, ctx=ctx)

    @property
    def source(self):
        return self._source

    @property
    def source_script(self) -> bool:
        return self._source_script

    @property
    def cyclic(self) -> bool:
        return self._cyclic

    @property
    def separator(self) -> str:
        return self._separator

    @property
    def condition(self):
        return self._condition

    @property
    def script(self):
        return self._script

    @property
    def min_count(self):
        return self._min_count

    @property
    def max_count(self):
        return self._max_count

    @property
    def default_value(self):
        return self._default_value

    @property
    def distribution(self):
        return self._distribution

    @property
    def converter(self):
        return self._converter

    @property
    def variable_prefix(self):
        return self._variable_prefix

    @property
    def variable_suffix(self):
        return self._variable_suffix

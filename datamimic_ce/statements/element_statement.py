# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/

from datamimic_ce.model.element_model import ElementModel
from datamimic_ce.statements.statement import Statement


class ElementStatement(Statement):
    def __init__(self, model: ElementModel, parent_stmt: Statement):
        name = model.name
        super().__init__(name, parent_stmt)
        self._name = name
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
        self._values = model.values
        self._default_value = model.default_value
        self._string = model.string

    @property
    def type(self):
        return self._type

    @property
    def values(self):
        return self._values

    @property
    def script(self):
        return self._script

    @property
    def constant(self):
        return self._constant

    @property
    def generator(self):
        return self._generator

    @property
    def source(self) -> str:
        return self._source

    @property
    def separator(self) -> str:
        return self._separator

    @property
    def condition(self) -> str:
        return self._condition

    @property
    def converter(self) -> str:
        return self._converter

    @property
    def in_date_format(self) -> str:
        return self._in_date_format

    @property
    def out_date_format(self) -> str:
        return self._out_date_format

    @property
    def default_value(self) -> str:
        return self._default_value

    @property
    def string(self) -> str:
        return self._string

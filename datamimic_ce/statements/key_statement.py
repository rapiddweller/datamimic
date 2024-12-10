# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.model.key_model import KeyModel
from datamimic_ce.statements.composite_statement import CompositeStatement


class KeyStatement(CompositeStatement):
    def __init__(self, model: KeyModel, parent_stmt: CompositeStatement):
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
        self._null_quota = model.null_quota
        self._pattern = model.pattern
        self._database = model.database
        self._variable_prefix = model.variable_prefix
        self._variable_suffix = model.variable_suffix
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
    def null_quota(self) -> float:
        return self._null_quota

    @property
    def pattern(self) -> str:
        return self._pattern

    @property
    def database(self) -> str:
        return self._database

    @property
    def string(self) -> str:
        return self._string

    @property
    def variable_prefix(self) -> str:
        return self._variable_prefix

    @property
    def variable_suffix(self) -> str:
        return self._variable_suffix

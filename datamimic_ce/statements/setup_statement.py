# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import ast

from datamimic_ce.model.setup_model import SetupModel
from datamimic_ce.statements.composite_statement import CompositeStatement


class SetupStatement(CompositeStatement):
    def __init__(self, model: SetupModel):
        super().__init__(None, None)
        self._use_mp = model.multiprocessing  # Default value is False (None)
        self._default_separator = model.default_separator
        self._default_locale = model.default_locale
        self._default_dataset = model.default_dataset
        self._num_process = model.num_process
        self._default_source_scripted = model.default_source_scripted
        self._report_logging = model.report_logging
        # Determine the line separator, cause auto add escape charactor when input to statement (e.g. "\n" -> "\\n")
        if model.default_line_separator is None:
            self._default_line_separator = model.default_line_separator
        else:
            self._default_line_separator = ast.literal_eval(f"'{model.default_line_separator}'")
        self._default_variable_prefix = model.default_variable_prefix
        self._default_variable_suffix = model.default_variable_suffix

    @property
    def use_mp(self) -> bool:
        return self._use_mp

    @property
    def default_separator(self) -> str:
        return self._default_separator

    @property
    def default_locale(self) -> str:
        return self._default_locale

    @property
    def default_dataset(self) -> str:
        return self._default_dataset

    @property
    def num_process(self) -> int:
        return self._num_process

    @property
    def default_line_separator(self) -> str:
        return self._default_line_separator

    @property
    def default_source_scripted(self) -> bool:
        return self._default_source_scripted

    @property
    def report_logging(self) -> bool:
        return self._report_logging

    @property
    def default_variable_prefix(self) -> str:
        return self._default_variable_prefix

    @property
    def default_variable_suffix(self) -> str:
        return self._default_variable_suffix

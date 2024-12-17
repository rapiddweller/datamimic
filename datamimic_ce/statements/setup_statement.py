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
        return bool(self._use_mp) if self._use_mp is not None else False

    @property
    def default_separator(self) -> str:
        return str(self._default_separator) if self._default_separator is not None else "|"

    @property
    def default_locale(self) -> str:
        return str(self._default_locale) if self._default_locale is not None else "en_US"

    @property
    def default_dataset(self) -> str:
        return str(self._default_dataset) if self._default_dataset is not None else "US"

    @property
    def num_process(self) -> int:
        return int(self._num_process) if self._num_process is not None else 1

    @property
    def default_line_separator(self) -> str:
        return str(self._default_line_separator) if self._default_line_separator is not None else "\n"

    @property
    def default_source_scripted(self) -> bool:
        return bool(self._default_source_scripted) if self._default_source_scripted is not None else False

    @property
    def report_logging(self) -> bool:
        return bool(self._report_logging) if self._report_logging is not None else False

    @property
    def default_variable_prefix(self) -> str:
        return str(self._default_variable_prefix) if self._default_variable_prefix is not None else "__"

    @property
    def default_variable_suffix(self) -> str:
        return str(self._default_variable_suffix) if self._default_variable_suffix is not None else "__"

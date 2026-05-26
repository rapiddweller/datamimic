# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from pathlib import Path
from xml.etree.ElementTree import Element

from datamimic_ce.constants.element_constants import EL_GENERATE
from datamimic_ce.model.generate_model import GenerateModel
from datamimic_ce.parsers.statement_parser import StatementParser
from datamimic_ce.statements.generate_statement import GenerateStatement
from datamimic_ce.statements.statement import Statement
from datamimic_ce.statements.variable_statement import VariableStatement

# Name reserved by the time-series iterator for its per-iteration namespace
# (ts.now/ts.step/ts.series). A user-defined <variable name="ts"> would shadow
# it at script-eval time, so we reject it up front when in time-series mode.
_TIMESERIES_RESERVED_NAME = "ts"


class GenerateParser(StatementParser):
    """
    Parse element "generate" into GenerateStatement
    """

    def __init__(
        self,
        element: Element,
        properties: dict,
    ):
        super().__init__(
            element,
            properties,
            valid_element_tag=EL_GENERATE,
        )

    def parse(self, descriptor_dir: Path, parent_stmt: Statement, lazy_parse: bool = False) -> GenerateStatement:
        """
        Parse element "generate" into GenerateStatement
        :return:
        """
        from datamimic_ce.parsers.parser_util import ParserUtil

        model = self.validate_attributes(GenerateModel)

        # Parse sub elements

        gen_stmt = GenerateStatement(model, parent_stmt)
        sub_stmt_list = ParserUtil.parse_sub_elements(
            descriptor_dir,
            self._element,
            self._properties,
            gen_stmt,
        )

        gen_stmt.sub_statements = sub_stmt_list

        if gen_stmt.interval is not None:
            self._check_no_reserved_ts_variable(sub_stmt_list)

        return gen_stmt

    @staticmethod
    def _check_no_reserved_ts_variable(sub_stmt_list: list[Statement]) -> None:
        """Reject ``<variable name="ts">`` inside a time-series ``<generate>``.

        The user's variable would shadow the time-iterator's ``ts`` namespace
        (``ts.now``/``ts.step``/``ts.series``) at script-eval time, so we
        surface this at parse time with a rename hint.
        """
        for sub in sub_stmt_list:
            if isinstance(sub, VariableStatement) and sub.name == _TIMESERIES_RESERVED_NAME:
                raise ValueError(
                    f"<variable name={_TIMESERIES_RESERVED_NAME!r}> is not allowed inside a "
                    f"time-series <generate>: 'ts' is reserved for the time-iterator namespace "
                    f"(ts.now/ts.step/ts.series). Rename the variable, e.g. 'ts_meta'."
                )

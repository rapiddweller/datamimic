# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from pathlib import Path

from datamimic_ce.engine.dsl.model.generation.generate_model import GenerateModel
from datamimic_ce.engine.dsl.parsers.base.client_config import ConnectionProfileLoader
from datamimic_ce.engine.dsl.parsers.base.statement_parser import StatementParser
from datamimic_ce.engine.dsl.parsers.input.xml import XmlElement, xml_tag
from datamimic_ce.engine.dsl.statements.base.statement import Statement
from datamimic_ce.engine.dsl.statements.generation.generate_statement import GenerateStatement
from datamimic_ce.engine.dsl.statements.values.variables.variable_statement import VariableStatement
from datamimic_ce.engine.dsl.vocabulary.constants.element_constants import EL_GENERATE, EL_ITERATE
from datamimic_ce.errors import DescriptorLocation, IssueCode, parser_validation_error

# Name reserved by the time-series iterator for its per-iteration namespace
# (ts.now/ts.step/ts.series). A user-defined <variable name="ts"> would shadow
# it at script-eval time, so we reject it up front when in time-series mode.
_TIMESERIES_RESERVED_NAME = "ts"


class GenerateParser(StatementParser):
    """
    Parse element "generate" (or its alias "iterate") into GenerateStatement
    """

    # <iterate> is a human-readable alias of <generate>: same parser, model, statement
    # and valid sub-elements. The dispatch table routes both tags here.
    _VALID_TAGS = frozenset({EL_GENERATE, EL_ITERATE})

    def __init__(
        self,
        element: XmlElement,
        properties: dict,
    ):
        super().__init__(
            element,
            properties,
            valid_element_tag=EL_GENERATE,  # sub-elements resolve under <generate> for both tags
        )

    def _validate_element_tag(self) -> None:
        """Accept both <generate> and its alias <iterate> (base only checks a single tag)."""
        if self._element.tag not in self._VALID_TAGS:
            raise parser_validation_error(
                code=IssueCode.PARSER_INVALID_TAG,
                expected=f"{EL_GENERATE} or {EL_ITERATE}",
                actual=xml_tag(self._element),
                location=DescriptorLocation(xml_tag(self._element)),
            )

    def parse(
        self,
        descriptor_dir: Path,
        parent_stmt: Statement,
        lazy_parse: bool = False,
        *,
        profile_loader: ConnectionProfileLoader,
    ) -> GenerateStatement:
        """
        Parse element "generate" into GenerateStatement
        :return:
        """
        from datamimic_ce.engine.dsl.parsers.base.dispatch import parse_sub_elements

        model = self.validate_attributes(GenerateModel)

        # <iterate> is the source-driven alias: it must iterate something. Reject a
        # sourceless <iterate> at parse — use <generate> for purely synthetic data.
        if self._element.tag == EL_ITERATE and not model.source:
            raise parser_validation_error(
                code=IssueCode.PARSER_VALIDATION_FAILED,
                details="<iterate> requires a 'source' to iterate over; use <generate> for synthetic data",
                location=DescriptorLocation(EL_ITERATE, attribute="source"),
            )

        # Parse sub elements

        gen_stmt = GenerateStatement(model, parent_stmt)
        sub_stmt_list = parse_sub_elements(
            descriptor_dir,
            self._element,
            self._properties,
            gen_stmt,
            profile_loader=profile_loader,
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
                raise parser_validation_error(
                    code=IssueCode.PARSER_VALIDATION_FAILED,
                    details=(
                        f"<variable name={_TIMESERIES_RESERVED_NAME!r}> is not allowed inside a "
                        "time-series <generate>: 'ts' is reserved for the time-iterator namespace "
                        "(ts.now/ts.step/ts.series). Rename the variable, e.g. 'ts_meta'."
                    ),
                    location=DescriptorLocation("variable", attribute="name"),
                )

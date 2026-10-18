# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.engine.dsl.model.flow.commands.execute_model import ExecuteModel
from datamimic_ce.engine.dsl.parsers.base.statement_parser import StatementParser
from datamimic_ce.engine.dsl.parsers.input.xml import XmlElement
from datamimic_ce.engine.dsl.statements.flow.commands.execute_statement import ExecuteStatement
from datamimic_ce.engine.dsl.vocabulary.constants.element_constants import EL_EXECUTE
from datamimic_ce.errors import IssueCode, parser_validation_error

# uri file extension -> execution language (when `type` is not given explicitly).
_EXT_TYPE = {".py": "python", ".sql": "sql", ".sh": "bash"}


class ExecuteParser(StatementParser):
    """Parse element "execute" to ExecuteStatement (a script file via ``uri`` XOR inline code)."""

    def __init__(self, element: XmlElement, properties: dict):
        super().__init__(element, properties, valid_element_tag=EL_EXECUTE)

    def parse(self) -> ExecuteStatement:
        model = self.validate_attributes(ExecuteModel)
        code = self._element.text
        has_inline = bool(code and code.strip())
        # Exactly one source of code: a script file (uri), inline code, or a script expression.
        if [bool(model.uri), has_inline, bool(model.script)].count(True) != 1:
            raise parser_validation_error(code=IssueCode.PARSER_EXECUTE_INVALID_SOURCE)
        exec_type = self._resolve_type(model)
        return ExecuteStatement(model, exec_type=exec_type, code=code if has_inline else None)

    @staticmethod
    def _resolve_type(model: ExecuteModel) -> str:
        if model.type:
            return model.type
        if model.uri:
            ext = model.uri[model.uri.rfind(".") :].lower() if "." in model.uri else ""
            inferred = _EXT_TYPE.get(ext)
            if inferred is None:
                raise parser_validation_error(code=IssueCode.PARSER_EXECUTE_TYPE_UNRESOLVED, uri=model.uri)
            return inferred
        return "python"  # inline default (flat statements; use <while>/<condition> or a .py file for blocks)

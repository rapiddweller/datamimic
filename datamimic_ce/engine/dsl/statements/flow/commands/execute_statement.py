# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import textwrap

from datamimic_ce.engine.dsl.model.flow.commands.execute_model import ExecuteModel
from datamimic_ce.engine.dsl.statements.base.statement import Statement

# uri file extension -> execution language (when `type` is not given explicitly).
_EXT_TYPE = {".py": "python", ".sql": "sql", ".sh": "bash"}


class ExecuteStatement(Statement):
    @staticmethod
    def language(type_: str | None, uri: str | None) -> str | None:
        """The language an <execute> runs: explicit type, else the uri extension, else python for inline code.
        None when a uri extension names no language."""
        if type_:
            return type_
        if uri:
            return _EXT_TYPE.get(uri[uri.rfind(".") :].lower() if "." in uri else "")
        return "python"  # inline default (flat statements; use <while>/<condition> or a .py file for blocks)

    @staticmethod
    def normalize_python_source(code: str) -> str:
        """Make XML-embedded Python parseable: tabs->spaces, drop blank first/last lines, then dedent the
        common leading indentation (relative block indentation is preserved)."""
        lines = code.replace("\t", "    ").splitlines()
        while lines and not lines[0].strip():
            lines.pop(0)
        while lines and not lines[-1].strip():
            lines.pop()
        return textwrap.dedent("\n".join(lines))

    def __init__(self, model: ExecuteModel, exec_type: str, code: str | None = None):
        super().__init__(name=None, parent_stmt=None)  # setup-level: no name/parent, but honor the base contract
        self._uri = model.uri
        self._target = model.target
        self._type = exec_type  # resolved: python | bash | sql
        self._code = code  # inline code (None when a uri script file is used)
        self._script = model.script  # expression whose evaluated value is the code

    @property
    def uri(self) -> str | None:
        return self._uri

    @property
    def target(self) -> str | None:
        return self._target

    @property
    def type(self) -> str:
        return self._type

    @property
    def code(self) -> str | None:
        return self._code

    @property
    def script(self) -> str | None:
        return self._script

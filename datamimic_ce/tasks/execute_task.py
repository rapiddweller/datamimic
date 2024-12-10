# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import textwrap
from pathlib import Path

from datamimic_ce.contexts.context import Context
from datamimic_ce.contexts.geniter_context import GenIterContext
from datamimic_ce.statements.execute_statement import ExecuteStatement
from datamimic_ce.tasks.task import Task


class ExecuteTask(Task):
    def __init__(self, statement: ExecuteStatement):
        self._statement = statement

    def execute(self, ctx: Context):
        _uri = self.statement.uri
        _target = self.statement.target

        uri_path = ctx.root.descriptor_dir / _uri
        # Check if either URI is a python file
        if _uri.endswith(".py"):
            content = self._get_content_from_uri(uri_path)
            self._eval_python(ctx, content)
        # Check if either URI is a SQL file
        elif _uri.endswith(".sql"):
            content = self._get_content_from_uri(uri_path)
            # if content contain ' or " then add escaped character before it
            escaped_text = content.replace("'", "\\'").replace('"', '\\"')
            # evaluate content value
            evaluated_content = ctx.evaluate_python_expression(f"f'''{escaped_text}'''")
            ctx.root.clients[_target].execute_sql_script(evaluated_content)

    @property
    def statement(self) -> ExecuteStatement:
        return self._statement

    @staticmethod
    def _get_content_from_uri(uri_path: Path) -> str:
        """
        Return file content if URI is provided
        """
        return uri_path.read_text()

    def _eval_python(self, ctx: Context, python_code: str) -> None:
        """
        Evaluate the provided Python code.
        """
        # Execute python code and get updates
        # Re-indent python code defined in descriptor file
        updated_ns = ctx.root.eval_namespace(textwrap.dedent(python_code))

        # Merge updates into shared namespace
        ctx.root.namespace.update(updated_ns)

        # Update current variables with updated namespace fields
        if isinstance(ctx, GenIterContext) and updated_ns and updated_ns is not None:
            ctx.current_variables.update(updated_ns)

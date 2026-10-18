# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import subprocess  # noqa: S404
import textwrap
from pathlib import Path
from typing import cast

from datamimic_ce.engine.dsl.api import ExecuteStatement, read_resource_bytes
from datamimic_ce.engine.io.api import execute_sql_script
from datamimic_ce.engine.io.contracts import SqlScriptClient
from datamimic_ce.engine.runtime.contexts.context import Context
from datamimic_ce.engine.runtime.contexts.geniter_context import GenIterContext
from datamimic_ce.engine.runtime.tasks.base.task import SetupSubTask
from datamimic_ce.errors import DescriptorLocation, IssueCode, task_config_error, task_warning


class ExecuteTask(SetupSubTask):
    def __init__(self, statement: ExecuteStatement):
        self._statement = statement

    @property
    def statement(self) -> ExecuteStatement:
        return self._statement

    def execute(self, ctx: Context):
        code = self._resolve_code(ctx)
        exec_type = self._statement.type
        if exec_type == "python":
            self._eval_python(ctx, code)
        elif exec_type == "sql":
            # script= already produced the final statement - re-interpolating would mangle braces in it
            self._run_sql(ctx, code, interpolate=self._statement.script is None)
        elif exec_type == "bash":
            self._run_bash(ctx, code)

    def _resolve_code(self, ctx: Context) -> str:
        """Inline code, the content of the uri script file, or - with script= - the evaluated
        expression itself (its value IS the code, e.g. a <variable string=\"...__var__...\"> DDL)."""
        if self._statement.uri:
            try:
                return read_resource_bytes(ctx.root.descriptor_dir / self._statement.uri).decode(
                    ctx.root.default_encoding
                )
            except FileNotFoundError as error:
                raise task_config_error(
                    code=IssueCode.TASK_EXECUTE_SCRIPT_NOT_FOUND,
                    script_name=Path(self._statement.uri).name,
                    location=DescriptorLocation("execute", attribute="uri"),
                ) from error
        if self._statement.script is not None:
            value = ctx.evaluate_python_expression(self._statement.script)
            if not isinstance(value, str):
                raise task_config_error(
                    code=IssueCode.TASK_EXPRESSION_EVAL_FAILED,
                    expr=f"execute.script={self._statement.script!r}",
                    error=f"must evaluate to a string of {self._statement.type} code, got {type(value).__name__}",
                    location=DescriptorLocation("execute", attribute="script"),
                )
            return value
        return self._statement.code or ""

    def _run_sql(self, ctx: Context, content: str, interpolate: bool = True) -> None:
        # f-string interpolation so inline SQL may reference descriptor variables (e.g. {table}).
        if interpolate:
            escaped_text = content.replace("'", "\\'").replace('"', '\\"')
            evaluated_content = ctx.evaluate_python_expression(f"f'''{escaped_text}'''")
            if not isinstance(evaluated_content, str):
                raise TypeError("Interpolated SQL must evaluate to a string")
            content = evaluated_content
        target = self._statement.target
        try:
            if target is None:
                raise KeyError(target)
            client = ctx.root.clients[target]
        except KeyError as error:
            raise task_config_error(
                code=IssueCode.TASK_EXECUTE_CLIENT_NOT_FOUND,
                client_id=target if target is not None else "(none)",
                location=DescriptorLocation("execute", attribute="target"),
            ) from error
        execute_sql_script(cast(SqlScriptClient, client), content)

    def _run_bash(self, ctx: Context, code: str) -> None:
        """Run a shell command. VERBATIM — no variable interpolation, so no generated data flows into the
        shell (no command injection). Non-deterministic: a deliberate escape hatch for environment side
        effects (file prep, external tools), NOT for producing the generated data values."""
        task_warning(code=IssueCode.EXECUTE_BASH_NONDETERMINISTIC)
        result = subprocess.run(  # noqa: S602,S603
            ["bash", "-c", code],
            cwd=ctx.root.descriptor_dir,
            capture_output=True,
            encoding=ctx.root.default_encoding,
            check=False,
        )
        if result.returncode != 0:
            raise task_config_error(
                code=IssueCode.TASK_EXECUTE_BASH_FAILED,
                exit_code=result.returncode,
                detail=result.stderr.strip() or f"exit {result.returncode}",
                location=DescriptorLocation("execute"),
            )

    def _eval_python(self, ctx: Context, python_code: str) -> None:
        """Evaluate inline/uri Python. Multi-line blocks work once dedented, but a malformed block yields a
        raw IndentationError/SyntaxError — turn that into a DATAMIMIC error that says what to do instead."""
        try:
            updated_ns = ctx.root.eval_namespace(self._normalize_python(python_code))
        except SyntaxError as e:  # IndentationError is a SyntaxError
            src = self._statement.uri or "inline code"
            raise task_config_error(
                code=IssueCode.TASK_EXPRESSION_EVAL_FAILED,
                expr=f"execute.python={src!r}",
                error=f"could not be parsed: {e.msg} (line {e.lineno}); use valid, consistently-indented Python",
                location=DescriptorLocation("execute"),
            ) from e
        ctx.root.namespace.update(updated_ns)
        if isinstance(ctx, GenIterContext) and updated_ns:
            ctx.current_variables.update(updated_ns)

    @staticmethod
    def _normalize_python(code: str) -> str:
        """Make XML-embedded Python parseable: tabs->spaces, drop blank first/last lines, then dedent the
        common leading indentation (relative block indentation is preserved)."""
        lines = code.replace("\t", "    ").splitlines()
        while lines and not lines[0].strip():
            lines.pop(0)
        while lines and not lines[-1].strip():
            lines.pop()
        return textwrap.dedent("\n".join(lines))

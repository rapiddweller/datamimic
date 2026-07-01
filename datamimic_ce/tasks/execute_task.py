# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import subprocess  # noqa: S404
import textwrap

from datamimic_ce.contexts.context import Context
from datamimic_ce.contexts.geniter_context import GenIterContext
from datamimic_ce.logger import logger
from datamimic_ce.statements.execute_statement import ExecuteStatement
from datamimic_ce.tasks.task import SetupSubTask

# One-time nudge: shell execution is a deliberate escape hatch for side effects, not data generation.
_bash_warned = False


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
            self._run_sql(ctx, code)
        elif exec_type == "bash":
            self._run_bash(ctx, code)

    def _resolve_code(self, ctx: Context) -> str:
        """Inline code, or the content of the uri script file (relative to the descriptor dir)."""
        if self._statement.uri:
            return (ctx.root.descriptor_dir / self._statement.uri).read_text()
        return self._statement.code or ""

    def _run_sql(self, ctx: Context, content: str) -> None:
        # f-string interpolation so the SQL may reference descriptor variables (e.g. {table}).
        escaped_text = content.replace("'", "\\'").replace('"', '\\"')
        evaluated_content = ctx.evaluate_python_expression(f"f'''{escaped_text}'''")
        ctx.root.clients[self._statement.target].execute_sql_script(evaluated_content)

    def _run_bash(self, ctx: Context, code: str) -> None:
        """Run a shell command. VERBATIM — no variable interpolation, so no generated data flows into the
        shell (no command injection). Non-deterministic: a deliberate escape hatch for environment side
        effects (file prep, external tools), NOT for producing the generated data values."""
        global _bash_warned
        if not _bash_warned:
            _bash_warned = True
            logger.warning(
                "<execute type='bash'> runs a shell command — this breaks DATAMIMIC's "
                "determinism/reproducibility. Use it for environment side effects, not data generation."
            )
        result = subprocess.run(  # noqa: S602,S603
            ["bash", "-c", code],
            cwd=ctx.root.descriptor_dir,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(f"<execute type='bash'> failed (exit {result.returncode}): {result.stderr.strip()}")

    def _eval_python(self, ctx: Context, python_code: str) -> None:
        """Evaluate inline/uri Python. Multi-line blocks work once dedented, but a malformed block yields a
        raw IndentationError/SyntaxError — turn that into a DATAMIMIC error that says what to do instead."""
        try:
            updated_ns = ctx.root.eval_namespace(self._normalize_python(python_code))
        except SyntaxError as e:  # IndentationError is a SyntaxError
            src = self._statement.uri or "inline code"
            raise ValueError(
                f"<execute type='python'> ({src}) could not be parsed: {e.msg} (line {e.lineno}). Inline Python "
                f"must be valid, consistently-indented code — for a real block, keep control flow in "
                f"<while>/<condition> and put complex logic in a .py file referenced via uri=."
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

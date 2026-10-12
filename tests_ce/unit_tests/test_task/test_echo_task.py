# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import xml.etree.ElementTree as ET
from unittest.mock import MagicMock, patch

from datamimic_ce.engine.dsl.parsers.flow.commands.echo_parser import EchoParser
from datamimic_ce.engine.dsl.statements.flow.commands.echo_statement import EchoStatement
from datamimic_ce.engine.runtime.contexts.context import Context
from datamimic_ce.engine.runtime.tasks.flow.commands.echo_task import EchoTask


class TestEchoTask:
    def test_echo_parser_empty_tag(self):
        element = ET.fromstring("<echo/>")
        parser = EchoParser(element, {})
        statement = parser.parse()
        assert isinstance(statement, EchoStatement)
        assert statement.value is None

    def test_echo_parser_empty_body(self):
        element = ET.fromstring("<echo></echo>")
        parser = EchoParser(element, {})
        statement = parser.parse()
        assert isinstance(statement, EchoStatement)
        assert statement.value is None

    def test_echo_parser_whitespace(self):
        element = ET.fromstring("<echo>   </echo>")
        parser = EchoParser(element, {})
        statement = parser.parse()
        assert isinstance(statement, EchoStatement)
        assert statement.value == "   "

    def test_echo_parser_text_and_placeholder(self):
        element = ET.fromstring("<echo>Hello {name}</echo>")
        parser = EchoParser(element, {})
        statement = parser.parse()
        assert isinstance(statement, EchoStatement)
        assert statement.value == "Hello {name}"

    @patch("datamimic_ce.engine.runtime.tasks.flow.commands.echo_task.logger")
    def test_execute_none_value(self, mock_logger):
        ctx = MagicMock(spec=Context)
        task = EchoTask(EchoStatement(None))
        task.execute(ctx)
        mock_logger.debug.assert_called_once_with("Echo - ")
        ctx.evaluate_python_expression.assert_not_called()

    @patch("datamimic_ce.engine.runtime.tasks.flow.commands.echo_task.logger")
    def test_execute_empty_string(self, mock_logger):
        ctx = MagicMock(spec=Context)
        task = EchoTask(EchoStatement(""))
        task.execute(ctx)
        mock_logger.debug.assert_called_once_with("Echo - ")
        ctx.evaluate_python_expression.assert_not_called()

    @patch("datamimic_ce.engine.runtime.tasks.flow.commands.echo_task.logger")
    def test_execute_whitespace_string(self, mock_logger):
        ctx = MagicMock(spec=Context)
        task = EchoTask(EchoStatement("   "))
        task.execute(ctx)
        mock_logger.debug.assert_called_once_with("Echo -    ")
        ctx.evaluate_python_expression.assert_not_called()

    @patch("datamimic_ce.engine.runtime.tasks.flow.commands.echo_task.logger")
    def test_execute_plain_text(self, mock_logger):
        ctx = MagicMock(spec=Context)
        task = EchoTask(EchoStatement("Simple message"))
        task.execute(ctx)
        mock_logger.debug.assert_called_once_with("Echo - Simple message")
        ctx.evaluate_python_expression.assert_not_called()

    @patch("datamimic_ce.engine.runtime.tasks.flow.commands.echo_task.logger")
    def test_execute_interpolation(self, mock_logger):
        ctx = MagicMock(spec=Context)
        ctx.evaluate_python_expression.return_value = "Hello World"
        task = EchoTask(EchoStatement("Hello {name}"))
        task.execute(ctx)
        ctx.evaluate_python_expression.assert_called_once_with("f'Hello {name}'")
        mock_logger.debug.assert_called_once_with("Echo - Hello World")

    @patch("datamimic_ce.engine.runtime.tasks.flow.commands.echo_task.logger")
    def test_execute_interpolation_with_quotes(self, mock_logger):
        ctx = MagicMock(spec=Context)
        ctx.evaluate_python_expression.return_value = 'User: "Alice" / \'Admin\''
        task = EchoTask(EchoStatement('User: "{user}" / \'{role}\''))
        task.execute(ctx)
        ctx.evaluate_python_expression.assert_called_once_with("f'User: \\\"{user}\\\" / \\\'{role}\\\''")
        mock_logger.debug.assert_called_once_with('Echo - User: "Alice" / \'Admin\'')

    @patch("datamimic_ce.engine.runtime.tasks.flow.commands.echo_task.logger")
    def test_execute_failing_placeholder(self, mock_logger):
        ctx = MagicMock(spec=Context)
        ctx.evaluate_python_expression.side_effect = Exception("name 'unknown_var' is not defined")
        task = EchoTask(EchoStatement("Hello {unknown_var}"))
        task.execute(ctx)
        mock_logger.warning.assert_called_once_with(
            "Echo - Hello {unknown_var} (placeholder not evaluated: name 'unknown_var' is not defined)"
        )

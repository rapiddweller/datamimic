# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pathlib import Path

import pytest

from datamimic_ce.engine.runtime.tasks.flow.commands.echo_task import logger as echo_logger
from datamimic_ce.interfaces.python.data_mimic_test import DataMimicTest


class TestEcho:
    _test_dir = Path(__file__).resolve().parent

    def test_simple_echo(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="simple_echo.xml")
        test_engine.test_with_timer()

    def test_scripted_echo(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="scripted_echo.xml")
        test_engine.test_with_timer()

    def test_scripted_echo_mp(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="scripted_echo_mp.xml")
        test_engine.test_with_timer()

    def test_variable_echo(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="variable_echo.xml")
        test_engine.test_with_timer()

    @pytest.mark.parametrize(
        ("setup_content", "expected_log"),
        [
            ("<echo/>", "Echo - "),
            ("<echo></echo>", "Echo - "),
            ("<echo>  \n </echo>", "Echo -   \n "),
            (
                '<generate name="before" count="1" target=""><key name="name" constant="Ada"/>'
                '<echo>He said \'{name}\' and "{name}"</echo></generate>',
                'Echo - He said \'Ada\' and "Ada"',
            ),
        ],
        ids=("self-closing-empty", "explicit-empty", "whitespace", "quoted-placeholder"),
    )
    def test_echo_text_logs_and_continues(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        setup_content: str,
        expected_log: str,
    ) -> None:
        (tmp_path / "datamimic.xml").write_text(
            f'<setup>{setup_content}<generate name="after" count="1" target="">'
            '<key name="v" constant="ok"/></generate></setup>',
            encoding="utf-8",
        )
        logged: list[str] = []
        monkeypatch.setattr(echo_logger, "debug", logged.append)
        engine = DataMimicTest(tmp_path, "datamimic.xml", capture_test_result=True)

        engine.test_with_timer()

        assert expected_log in logged
        assert engine.capture_result()["after"] == [{"v": "ok"}]

    def test_empty_echo(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="empty_echo.xml")
        test_engine.test_with_timer()

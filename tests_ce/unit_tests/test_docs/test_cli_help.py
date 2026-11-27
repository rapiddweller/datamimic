# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

import pytest
import typer

from datamimic_ce.interfaces.cli import app


def assert_cli_help(commands) -> None:
    authoring = commands["authoring"].commands
    assert all(command.help and command.help.strip() for command in authoring.values())
    for name in ("run", "init"):
        options = [param for param in commands[name].params if isinstance(param, typer.core.TyperOption)]
        assert options
        assert all(option.help and option.help.strip() for option in options)
    assert authoring["run"].help.splitlines()[0] != authoring["dry-run"].help.splitlines()[0]


def test_cli_command_and_option_help_is_declared() -> None:
    assert_cli_help(typer.main.get_command(app).commands)


@pytest.mark.parametrize("kind", ["command", "option"])
def test_cli_help_check_rejects_blank_help(kind: str) -> None:
    commands = typer.main.get_command(app).commands
    if kind == "command":
        commands["authoring"].commands["version"].help = " "
    else:
        commands["run"].params[1].help = " "
    with pytest.raises(AssertionError):
        assert_cli_help(commands)

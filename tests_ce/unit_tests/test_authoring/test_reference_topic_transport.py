# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.

"""CLI and MCP project one typed reference-topic vocabulary."""

import pytest
from typer.testing import CliRunner

from datamimic_ce.authoring.reference import ReferenceTopic
from datamimic_ce.cli import app
from datamimic_ce.mcp.models import ReferenceArgs
from datamimic_ce.mcp.server import reference_impl

_TOPIC_NAMES = {
    ReferenceTopic.ELEMENT: "generate",
    ReferenceTopic.ENTITIES: "Person",
    ReferenceTopic.RULES: "DM315",
}


@pytest.mark.parametrize("topic", list(ReferenceTopic))
def test_every_reference_topic_has_cli_and_mcp_transport_parity(topic: ReferenceTopic) -> None:
    name = _TOPIC_NAMES.get(topic)
    args = ReferenceArgs(topic=topic, name=name)
    assert args.topic is topic

    mcp_result = reference_impl(args)
    assert mcp_result["ok"] is True
    assert mcp_result["content"]

    command = ["reference", topic.value]
    if name is not None:
        command.append(name)
    cli_result = CliRunner().invoke(app, command)
    assert cli_result.exit_code == 0, cli_result.stdout
    assert cli_result.stdout.strip()


def test_reference_args_uses_the_canonical_topic_type_directly() -> None:
    assert ReferenceArgs.model_fields["topic"].annotation is ReferenceTopic

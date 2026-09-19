# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.

"""CLI and MCP project one typed reference-topic vocabulary."""

import pytest
from typer.testing import CliRunner

from datamimic_ce.authoring.contracts import AuthoringReferenceCategory, ReferenceRequest, ReferenceTopic
from datamimic_ce.authoring.service import reference
from datamimic_ce.cli import app

_TOPIC_NAMES = {
    ReferenceTopic.ELEMENT: "generate",
    ReferenceTopic.ENTITIES: "Person",
    ReferenceTopic.RULES: "DM315",
}


@pytest.mark.parametrize("topic", list(ReferenceTopic))
def test_every_reference_topic_has_cli_and_service_parity(topic: ReferenceTopic) -> None:
    name = _TOPIC_NAMES.get(topic)
    args = ReferenceRequest(topic=topic, name=name)
    assert args.topic is topic

    result = reference(args)
    assert result.ok is True
    assert result.content

    command = ["reference", topic.value]
    if name is not None:
        command.append(name)
    cli_result = CliRunner().invoke(app, command)
    assert cli_result.exit_code == 0, cli_result.stdout
    assert cli_result.stdout.strip()


def test_reference_request_uses_the_canonical_topic_type_directly() -> None:
    assert ReferenceRequest.model_fields["topic"].annotation is ReferenceTopic


@pytest.mark.parametrize("category", list(AuthoringReferenceCategory))
def test_every_authoring_reference_category_has_cli_and_service_parity(
    category: AuthoringReferenceCategory,
) -> None:
    request = ReferenceRequest(topic=ReferenceTopic.AUTHORING, category=category)
    result = reference(request)
    assert result.ok is True
    assert result.category is category
    assert result.content

    cli_result = CliRunner().invoke(app, ["reference", "authoring", "--category", category.value])
    assert cli_result.exit_code == 0, cli_result.stdout
    assert cli_result.stdout.strip()

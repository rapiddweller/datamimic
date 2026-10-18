"""CLI discovery uses the public typed application catalog."""

import json

import pytest
from typer.testing import CliRunner

from datamimic_ce.authoring import create_authoring_application
from datamimic_ce.authoring.domain.capabilities import CapabilityDomain
from datamimic_ce.authoring.domain.requests import ReferenceRequest, ReferenceTopic
from datamimic_ce.interfaces.cli import app


@pytest.mark.parametrize("topic", list(ReferenceTopic))
def test_every_reference_topic_has_cli_and_service_parity(topic: ReferenceTopic) -> None:
    result = create_authoring_application().reference(ReferenceRequest(topic=topic))
    cli_result = CliRunner().invoke(app, ["authoring", "reference", "--topic", topic.value])
    assert cli_result.exit_code == 0, cli_result.stdout
    assert json.loads(cli_result.stdout) == result.model_dump(mode="json", exclude_none=True)


def test_reference_request_uses_the_canonical_topic_type_directly() -> None:
    assert ReferenceRequest.model_fields["topic"].annotation is ReferenceTopic


@pytest.mark.parametrize("domain", list(CapabilityDomain))
def test_every_capability_domain_has_cli_and_service_parity(domain: CapabilityDomain) -> None:
    application = create_authoring_application()
    names = application.capabilities().capability_names(domain)
    assert names, domain
    result = application.capability(domain, names[0])
    cli_result = CliRunner().invoke(app, ["authoring", "capability", "--domain", domain.value, "--name", names[0]])
    assert cli_result.exit_code == 0, cli_result.stdout
    assert json.loads(cli_result.stdout) == result.model_dump(mode="json", exclude_none=True)

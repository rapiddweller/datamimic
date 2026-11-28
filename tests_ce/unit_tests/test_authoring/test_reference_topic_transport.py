"""CLI discovery uses the public typed application catalog."""

import json

import pytest
from typer.testing import CliRunner

from datamimic_ce.authoring import create_authoring_application
from datamimic_ce.authoring.domain.capabilities import CapabilityDomain
from datamimic_ce.authoring.domain.reference import ReferenceNotFound
from datamimic_ce.authoring.domain.requests import ReferenceRequest, ReferenceTopic
from datamimic_ce.interfaces.cli import app


@pytest.mark.parametrize("topic", list(ReferenceTopic))
def test_every_reference_topic_has_cli_and_service_parity(topic: ReferenceTopic) -> None:
    result = create_authoring_application().reference(ReferenceRequest(topic=topic))
    cli_result = CliRunner().invoke(app, ["authoring", "reference", "--topic", topic.value])
    assert cli_result.exit_code == 0, cli_result.stdout
    assert json.loads(cli_result.stdout) == result.model_dump(mode="json")


_UNKNOWN_NAME_HINTS = {
    ReferenceTopic.OVERVIEW: "The overview topic has no named entries.",
    ReferenceTopic.ASSEMBLY: "No matching assembly.",
    ReferenceTopic.RULES: "No matching rule.",
    ReferenceTopic.EXPECTATIONS: "No matching expectation.",
    ReferenceTopic.EXAMPLES: "No matching example.",
    ReferenceTopic.LEARNING: "No matching learning resource.",
}


@pytest.mark.parametrize("topic", list(ReferenceTopic))
def test_unknown_reference_name_is_a_typed_miss_on_every_transport(topic: ReferenceTopic) -> None:
    """Was ok=true with the text 'No matching ...' as content; a caller had to match the text."""
    application = create_authoring_application()
    result = application.reference(ReferenceRequest(topic=topic, name="bogus"))
    assert isinstance(result, ReferenceNotFound)
    assert (result.ok, result.error, result.topic, result.name) == (False, "reference_not_found", topic, "bogus")
    assert result.content == _UNKNOWN_NAME_HINTS[topic]
    expected = () if topic == ReferenceTopic.OVERVIEW else application.reference_names(topic)
    assert result.available_names == expected
    assert (topic == ReferenceTopic.OVERVIEW) or expected
    for name in result.available_names:
        assert application.reference(ReferenceRequest(topic=topic, name=name)).ok

    cli = CliRunner().invoke(app, ["authoring", "reference", "--topic", topic.value, "--name", "bogus"])
    assert cli.exit_code == 1, cli.stdout
    assert json.loads(cli.stdout) == result.model_dump(mode="json")


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
    assert json.loads(cli_result.stdout) == result.model_dump(mode="json")

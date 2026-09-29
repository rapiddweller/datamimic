"""State-machine transition grammar lives in the transition model."""

import pytest
from pydantic import ValidationError

from datamimic_ce.authoring.domain.schema import build_schema_index
from datamimic_ce.engine.dsl.model.registry import get_model_class
from datamimic_ce.engine.dsl.model.setup.generators.transition_model import TransitionModel
from datamimic_ce.engine.dsl.parsers.input.xml import parse_xml_source
from datamimic_ce.engine.dsl.parsers.setup.state_machine_parser import StateMachineParser
from datamimic_ce.engine.dsl.vocabulary.constants.element_constants import EL_TRANSITION


def _parse_transition(attributes: str):
    element = parse_xml_source(f'<state-machine id="lifecycle"><transition {attributes}/></state-machine>')
    return StateMachineParser(element, {}).parse()


def test_transition_model_is_the_registry_schema_source() -> None:
    model = get_model_class(EL_TRANSITION)

    assert model is TransitionModel
    assert {field.alias or name for name, field in model.model_fields.items()} == {"from", "to", "weight"}
    assert set(build_schema_index().get(EL_TRANSITION).attributes) == {"from", "to", "weight"}


def test_parser_uses_transition_model_for_default_and_explicit_weight() -> None:
    element = parse_xml_source(
        """
        <state-machine id="lifecycle">
            <transition from="open" to="paid"/>
            <transition from="paid" to="shipped" weight="0.75"/>
        </state-machine>
        """
    )

    statement = StateMachineParser(element, {}).parse()

    assert statement.rules == [("open", "paid", 1.0), ("paid", "shipped", 0.75)]


def test_whitespace_endpoint_is_an_open_state_name() -> None:
    transition = TransitionModel.model_validate({"from": "   ", "to": "paid"})

    assert transition.source == "   "
    assert _parse_transition('from="   " to="paid"').rules == [("   ", "paid", 1.0)]


@pytest.mark.parametrize(
    "attributes",
    [
        'to="paid"',
        'from="" to="paid"',
        'from="open"',
        'from="open" to=""',
        'from="open" to="paid" unexpected="value"',
        'from="open" to="paid" weight="not-a-number"',
        'from="open" to="paid" weight="0"',
        'from="open" to="paid" weight="-1"',
        'from="open" to="paid" weight="nan"',
    ],
)
def test_parser_rejects_invalid_transitions_at_the_model_boundary(attributes: str) -> None:
    child = parse_xml_source(f"<transition {attributes}/>")
    with pytest.raises(ValidationError):
        TransitionModel.model_validate(child.attrib)
    with pytest.raises(ValueError):
        _parse_transition(attributes)

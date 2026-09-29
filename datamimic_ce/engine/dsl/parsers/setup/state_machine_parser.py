# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.engine.dsl.model.setup.state_machine_model import StateMachineModel
from datamimic_ce.engine.dsl.model.setup.transition_model import TransitionModel
from datamimic_ce.engine.dsl.parsers.base.statement_parser import StatementParser
from datamimic_ce.engine.dsl.parsers.input.xml import XmlElement, xml_tag
from datamimic_ce.engine.dsl.statements.setup.state_machine_statement import StateMachineStatement
from datamimic_ce.engine.dsl.vocabulary.constants.element_constants import EL_COMMENT, EL_STATE_MACHINE, EL_TRANSITION


class StateMachineParser(StatementParser):
    """Parse a <state-machine> element (id/start + <transition> children) into a
    StateMachineStatement."""

    def __init__(self, element: XmlElement, properties: dict):
        super().__init__(element, properties, valid_element_tag=EL_STATE_MACHINE)

    def parse(self) -> StateMachineStatement:
        model = self.validate_attributes(StateMachineModel)
        rules = []
        for child in self._element:
            if child.tag == EL_COMMENT:
                continue
            if xml_tag(child) != EL_TRANSITION:
                raise ValueError(f"<state-machine> only accepts <transition> children, got <{xml_tag(child)}>")
            transition = TransitionModel(**child.attrib)
            rules.append((transition.source, transition.target, transition.weight))
        if not rules:
            raise ValueError(f"<state-machine> '{model.id}' needs at least one <transition>")
        return StateMachineStatement(name=model.id, start=model.start, rules=rules)

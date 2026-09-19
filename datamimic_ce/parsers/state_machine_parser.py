# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from xml.etree.ElementTree import Element

from datamimic_ce.constants.attribute_constants import ATTR_FROM, ATTR_TO, ATTR_WEIGHT
from datamimic_ce.constants.element_constants import EL_COMMENT, EL_STATE_MACHINE, EL_TRANSITION
from datamimic_ce.model.state_machine_model import StateMachineModel
from datamimic_ce.parsers.statement_parser import StatementParser
from datamimic_ce.statements.state_machine_statement import StateMachineStatement


class StateMachineParser(StatementParser):
    """Parse a <state-machine> element (id/start + <transition> children) into a
    StateMachineStatement."""

    def __init__(self, element: Element, properties: dict):
        super().__init__(element, properties, valid_element_tag=EL_STATE_MACHINE)

    def parse(self) -> StateMachineStatement:
        model = self.validate_attributes(StateMachineModel)
        rules = []
        for child in self._element:
            if child.tag == EL_COMMENT:
                continue
            if child.tag != EL_TRANSITION:
                raise ValueError(f"<state-machine> only accepts <transition> children, got <{child.tag}>")
            attrs = child.attrib
            extra = set(attrs) - {ATTR_FROM, ATTR_TO, ATTR_WEIGHT}
            if extra:
                raise ValueError(f"<transition> got invalid attribute(s) {sorted(extra)}, expects from/to/weight")
            src, tgt = attrs.get(ATTR_FROM), attrs.get(ATTR_TO)
            if not src or not tgt:
                raise ValueError("<transition> requires both 'from' and 'to'")
            try:
                weight = float(attrs[ATTR_WEIGHT]) if ATTR_WEIGHT in attrs else 1.0
            except ValueError as e:
                raise ValueError(f"<transition {src}->{tgt}> has invalid weight '{attrs[ATTR_WEIGHT]}'") from e
            rules.append((src, tgt, weight))
        if not rules:
            raise ValueError(f"<state-machine> '{model.id}' needs at least one <transition>")
        return StateMachineStatement(name=model.id, start=model.start, rules=rules)

# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.domains.common.literal_generators.state_transition_generator import Rule
from datamimic_ce.statements.statement import Statement


class StateMachineStatement(Statement):
    """A named <state-machine> definition: an id, an optional start state, and the
    list of weighted (from, to, weight) transitions."""

    def __init__(self, name: str, start: str | None, rules: list[Rule]):
        self._name = name
        self._start = start
        self._rules = rules

    @property
    def name(self) -> str | None:
        return self._name

    @property
    def start(self) -> str | None:
        return self._start

    @property
    def rules(self) -> list[Rule]:
        return self._rules

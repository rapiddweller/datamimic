# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.contexts.setup_context import SetupContext
from datamimic_ce.domains.common.literal_generators.state_transition_generator import StateMachineDef
from datamimic_ce.statements.state_machine_statement import StateMachineStatement
from datamimic_ce.tasks.task import SetupSubTask


class StateMachineTask(SetupSubTask):
    """Register a <state-machine> definition under its id, so each
    ``generator="<id>"`` reference builds its own stateful StateTransitionGenerator."""

    def __init__(self, statement: StateMachineStatement):
        self._statement = statement

    @property
    def statement(self) -> StateMachineStatement:
        return self._statement

    def execute(self, ctx: SetupContext):
        ctx.root.generators[self._statement.name] = StateMachineDef(
            rules=tuple(self._statement.rules), start=self._statement.start
        )

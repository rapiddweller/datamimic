# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.engine.dsl.model.flow.commands.assert_model import AssertModel
from datamimic_ce.engine.dsl.statements.base.statement import Statement

# Whole-value ``{name}`` is replaced by a property, possibly a secret, when the runtime parses the descriptor; ``__``
# is the interpolation mark of string and pattern. A message with neither mark is the literal text of the file.
_INTERPOLATION_MARKS = ("{", "}", "__")


class AssertStatement(Statement):
    def __init__(self, model: AssertModel, line: int | None, raw_message: str | None):
        super().__init__(None, None)
        self._condition = model.condition
        # model.message is already resolved from the properties; the raw text decides what a failure may show.
        self._message = self.literal_message(raw_message)
        self._message_hidden = bool(raw_message) and self._message is None
        # Build finds the failed assert by its line: two asserts in one step otherwise share one path.
        self._line = line

    @staticmethod
    def literal_message(raw: str | None) -> str | None:
        """The raw message attribute when it is literal author text, else None. Only the raw attribute text can prove
        a message literal: the resolved value of ``{name}`` has no braces. Build applies the same rule."""
        return raw if raw and not any(mark in raw for mark in _INTERPOLATION_MARKS) else None

    @property
    def condition(self) -> str:
        return self._condition

    @property
    def message(self) -> str | None:
        """The literal message, or None when the assert has none or its message can hold a property value."""
        return self._message

    @property
    def message_hidden(self) -> bool:
        return self._message_hidden

    @property
    def line(self) -> int | None:
        return self._line

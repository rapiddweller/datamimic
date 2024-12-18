# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.statements.statement import Statement


class EchoStatement(Statement):
    def __init__(self, value: str | None):
        super().__init__(None, None)
        self._value = value

    @property
    def value(self):
        return self._value

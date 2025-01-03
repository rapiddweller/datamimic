# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from datamimic_ce.model.array_model import ArrayModel
from datamimic_ce.statements.statement import Statement


class ArrayStatement(Statement):
    def __init__(self, model: ArrayModel):
        super().__init__(model.name, None)
        self._count = model.count
        self._type = model.type
        self._script = model.script

    @property
    def type(self) -> str | None:
        return self._type

    @property
    def count(self) -> int | None:
        return self._count

    @property
    def script(self) -> str | None:
        return self._script

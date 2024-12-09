# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/


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
    def script(self) -> str:
        return self._script

# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/

from datamimic_ce.model.execute_model import ExecuteModel
from datamimic_ce.statements.statement import Statement


class ExecuteStatement(Statement):
    def __init__(self, model: ExecuteModel):
        self._uri = model.uri
        self._target = model.target

    @property
    def uri(self):
        return self._uri

    @property
    def target(self):
        return self._target

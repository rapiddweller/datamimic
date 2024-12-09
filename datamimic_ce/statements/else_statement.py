# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/

from datamimic_ce.model.else_model import ElseModel
from datamimic_ce.statements.composite_statement import CompositeStatement
from datamimic_ce.statements.statement import Statement


class ElseStatement(Statement):
    def __init__(self, model: ElseModel, parent_stmt: CompositeStatement):
        super().__init__(name=None, parent_stmt=parent_stmt)

# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from datamimic_ce.model.if_model import IfModel
from datamimic_ce.statements.composite_statement import CompositeStatement


class IfStatement(CompositeStatement):
    def __init__(self, model: IfModel, parent_stmt: CompositeStatement):
        super().__init__(name=None, parent_stmt=parent_stmt)
        self._condition = model.condition

    @property
    def condition(self) -> str:
        return self._condition

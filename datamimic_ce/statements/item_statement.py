# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.model.item_model import ItemModel
from datamimic_ce.statements.composite_statement import CompositeStatement


class ItemStatement(CompositeStatement):
    def __init__(self, model: ItemModel):
        super().__init__(name=None, parent_stmt=None)
        self._condition = model.condition

    @property
    def condition(self):
        return self._condition

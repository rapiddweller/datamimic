# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/

from datamimic_ce.model.item_model import ItemModel
from datamimic_ce.statements.composite_statement import CompositeStatement


class ItemStatement(CompositeStatement):
    def __init__(self, model: ItemModel):
        super().__init__(name=None, parent_stmt=None)
        self._condition = model.condition

    @property
    def condition(self):
        return self._condition

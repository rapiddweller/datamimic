# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/

from datamimic_ce.model.list_model import ListModel
from datamimic_ce.statements.composite_statement import CompositeStatement


class ListStatement(CompositeStatement):
    def __init__(self, model: ListModel):
        super().__init__(model.name, None)
        self._converter = model.converter

    @property
    def converter(self):
        return self._converter

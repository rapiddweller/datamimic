# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.model.list_model import ListModel
from datamimic_ce.statements.composite_statement import CompositeStatement


class ListStatement(CompositeStatement):
    def __init__(self, model: ListModel):
        super().__init__(model.name, None)
        self._converter = model.converter

    @property
    def converter(self):
        return self._converter

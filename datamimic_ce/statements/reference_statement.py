# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.model.reference_model import ReferenceModel
from datamimic_ce.statements.statement import Statement


class ReferenceStatement(Statement):
    def __init__(self, model: ReferenceModel):
        super().__init__(model.name, None)
        self._source = model.source
        self._source_type = model.source_type
        self._source_key = model.source_key
        self._unique = model.unique

    @property
    def source(self):
        return self._source

    @property
    def source_type(self):
        return self._source_type

    @property
    def source_key(self):
        return self._source_key

    @property
    def unique(self):
        return self._unique

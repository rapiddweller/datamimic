# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/

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

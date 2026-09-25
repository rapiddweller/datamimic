# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.engine.dsl.model.include_model import IncludeModel
from datamimic_ce.engine.dsl.statements.statement import Statement


class IncludeStatement(Statement):
    def __init__(self, model: IncludeModel):
        super().__init__(None, None)
        self._uri: str = model.uri

    @property
    def uri(self) -> str:
        return self._uri

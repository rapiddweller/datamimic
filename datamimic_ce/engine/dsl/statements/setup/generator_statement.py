# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.engine.dsl.model.setup.generators.generator_model import GeneratorModel
from datamimic_ce.engine.dsl.statements.base.statement import Statement


class GeneratorStatement(Statement):
    def __init__(self, model: GeneratorModel):
        self._name: str = model.name
        self._generator = model.generator

    @property
    def name(self) -> str:
        return self._name

    @property
    def generator(self) -> str:
        return self._generator

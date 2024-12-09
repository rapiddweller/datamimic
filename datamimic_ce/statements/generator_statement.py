# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/

from datamimic_ce.model.generator_model import GeneratorModel
from datamimic_ce.statements.statement import Statement


class GeneratorStatement(Statement):
    def __init__(self, model: GeneratorModel):
        self._name = model.name
        self._generator = model.generator

    @property
    def name(self):
        return self._name

    @property
    def generator(self):
        return self._generator

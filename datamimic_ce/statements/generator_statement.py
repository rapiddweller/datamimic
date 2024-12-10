# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

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

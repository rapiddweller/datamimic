# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from datamimic_ce.model.ml_train_model import MLTrainModel
from datamimic_ce.statements.statement import Statement


class MLTrainStatement(Statement):
    def __init__(self, model: MLTrainModel):
        self._name = model.name
        self._source = model.source
        self._type = model.type
        self._mode = model.mode
        self._maxTrainingTime = model.maxTrainingTime
        self._separator = model.separator

    @property
    def name(self) -> str | None:
        return self._name

    @property
    def source(self) -> str:
        return self._source

    @property
    def type(self) -> str | None:
        return self._type

    @property
    def mode(self) -> str | None:
        return self._mode

    @property
    def maxTrainingTime(self) -> str | None:
        return self._maxTrainingTime

    @property
    def separator(self) -> str | None:
        return self._separator

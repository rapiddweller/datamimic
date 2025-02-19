# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from xml.etree.ElementTree import Element

from datamimic_ce.constants.element_constants import EL_ML_TRAIN
from datamimic_ce.model.ml_train_model import MLTrainModel
from datamimic_ce.parsers.statement_parser import StatementParser
from datamimic_ce.statements.ml_train_statement import MLTrainStatement
from datamimic_ce.utils.base_class_factory_util import BaseClassFactoryUtil


class MLTrainParser(StatementParser):
    """
    Parse element "ml-train" to MLTrainStatement
    """

    def __init__(
        self,
        class_factory_util: BaseClassFactoryUtil,
        element: Element,
        properties: dict,
    ):
        super().__init__(
            element,
            properties,
            valid_element_tag=EL_ML_TRAIN,
            class_factory_util=class_factory_util,
        )

    def parse(self, **kwargs) -> MLTrainStatement:
        """
        Parse element "ml-train" to MLTrainStatement
        :return:
        """
        return MLTrainStatement(self.validate_attributes(MLTrainModel))

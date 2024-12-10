# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.statements.if_statement import IfStatement
from datamimic_ce.tasks.if_else_base_task import IfElseBaseTask
from datamimic_ce.utils.base_class_factory_util import BaseClassFactoryUtil


class IfTask(IfElseBaseTask):
    def __init__(self, statement: IfStatement, class_factory_util: BaseClassFactoryUtil):
        super().__init__(statement, class_factory_util)

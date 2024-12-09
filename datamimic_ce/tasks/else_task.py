# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/

from datamimic_ce.statements.else_statement import ElseStatement
from datamimic_ce.tasks.if_else_base_task import IfElseBaseTask
from datamimic_ce.utils.base_class_factory_util import BaseClassFactoryUtil


class ElseTask(IfElseBaseTask):
    def __init__(self, statement: ElseStatement, class_factory_util: BaseClassFactoryUtil):
        super().__init__(statement, class_factory_util)

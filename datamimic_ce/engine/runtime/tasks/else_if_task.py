# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.engine.dsl.api import ElseIfStatement
from datamimic_ce.engine.runtime.tasks.if_else_base_task import IfElseBaseTask


class ElseIfTask(IfElseBaseTask):
    def __init__(self, statement: ElseIfStatement):
        super().__init__(statement)

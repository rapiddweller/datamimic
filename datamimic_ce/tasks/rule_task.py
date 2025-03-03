# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.contexts.geniter_context import GenIterContext
from datamimic_ce.contexts.setup_context import SetupContext
from datamimic_ce.statements.item_statement import ItemStatement
from datamimic_ce.tasks.element_task import ElementTask
from datamimic_ce.tasks.task import Task
from datamimic_ce.utils.base_class_factory_util import BaseClassFactoryUtil


class RuleTask(Task):
    def __init__(
        self,
        ctx: SetupContext,
        statement: ItemStatement,
        class_factory_util: BaseClassFactoryUtil,
    ):
        self._statement = statement
        self._class_factory_util = class_factory_util

    @property
    def statement(self) -> ItemStatement:
        return self._statement

    def execute(self, parent_context: GenIterContext):
        """
        Change datas base on condition in element "rule"
        :param parent_context:
        :return:
        """
        pass

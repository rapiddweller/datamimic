# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com
import copy
import itertools

from datamimic_ce.contexts.context import SAFE_GLOBALS, DotableDict
from datamimic_ce.data_sources.data_source_pagination import DataSourcePagination
from datamimic_ce.statements.rule_statement import RuleStatement
from datamimic_ce.statements.source_constraints_statement import ConstraintsStatement
from datamimic_ce.tasks.task import Task


class ConstraintsTask(Task):
    def __init__(self, statement: ConstraintsStatement):
        self._statement = statement

    @property
    def statement(self) -> ConstraintsStatement:
        return self._statement

    def execute(self, source_data, pagination: DataSourcePagination | None = None, cyclic: bool | None = False) -> list:
        filter_data = list(source_data)
        # If source is empty, return empty list
        if len(filter_data) == 0:
            return []

        for i in range(len(filter_data) - 1, -1, -1):  # Iterate from last to first
            data_dict = copy.deepcopy(filter_data[i])

            for key, value in data_dict.items():
                if isinstance(value, dict):
                    data_dict[key] = DotableDict(value)

            for child_stmt in self.statement.sub_statements:
                if isinstance(child_stmt, RuleStatement):
                    if_condition = eval(child_stmt.if_rule, SAFE_GLOBALS, data_dict)
                    if isinstance(if_condition, bool) and if_condition:
                        else_condition = eval(child_stmt.then_rule, SAFE_GLOBALS, data_dict)
                        if isinstance(else_condition, bool) and else_condition is False:
                            del filter_data[i]  # remove data that not meet then_rule
                            break
        # If filtered data is empty, return empty list
        if len(filter_data) == 0:
            return []

        if pagination is None:
            start_idx = 0
            end_idx = len(filter_data)
        else:
            start_idx = pagination.skip
            end_idx = pagination.skip + pagination.limit
        # Get cyclic data from filtered data source
        if cyclic:
            iterator = itertools.cycle(filter_data)
            return [copy.deepcopy(ele) for ele in itertools.islice(iterator, start_idx, end_idx)]
        else:
            return list(itertools.islice(filter_data, start_idx, end_idx))

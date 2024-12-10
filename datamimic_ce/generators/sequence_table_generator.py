# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import sys

from datamimic_ce.contexts.context import Context
from datamimic_ce.contexts.geniter_context import GenIterContext
from datamimic_ce.data_sources.data_source_pagination import DataSourcePagination
from datamimic_ce.generators.generator import Generator
from datamimic_ce.statements.key_statement import KeyStatement
from datamimic_ce.statements.variable_statement import VariableStatement


class SequenceTableGenerator(Generator):
    """
    Generate sequential number set
    """

    def __init__(self, context: Context, stmt: KeyStatement | VariableStatement):
        self._stmt = stmt
        self._context = context
        self._source_name = stmt.database
        rdbms_client = context.root.clients.get(self._source_name)
        root_gen_stmt = self._stmt.get_root_generate_statement()
        self._start = rdbms_client.get_current_sequence_number(
            table_name=root_gen_stmt.type, col_name=self._stmt.name
        ) - int(root_gen_stmt.count)
        self._current = None
        self._end = None

    def pre_execute(self, context):
        """
        Increase the sequence number in the database
        :param context:
        :return:
        """
        root_gen_stmt = self._stmt.get_root_generate_statement()
        rdbms_client = context.root.clients.get(self._source_name)
        rdbms_client.increase_sequence_number(
            table_name=root_gen_stmt.type,
            col_name=self._stmt.name,
            count=root_gen_stmt.count,
        )

    def add_pagination(self, pagination: DataSourcePagination | None = None):
        """
        Add mp pagination to the generator
        :param pagination:
        :return:
        """
        if pagination is None:
            self._end = sys.maxsize
            self._current = self._start + 1
            return
        self._start = self._start + pagination.skip
        self._end = self._start + pagination.limit
        self._current = self._start

    def generate(self, ctx: GenIterContext) -> int:
        """
        Generate current number of sequence
        :return:
        """
        result = self._current
        self._current += 1

        if self._current > self._end:
            raise StopIteration("Generator reached the end")

        return result

# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from datamimic_ce.data_sources.data_source_pagination import DataSourcePagination
from datamimic_ce.generators.generator import Generator


class IncrementGenerator(Generator):
    """
    Generate sequential number set
    """

    def __init__(self, start: int = 1, end: int = 9223372036854775807, step: int = 1):
        if step <= 0:
            raise ValueError("Step must be a positive integer.")
        self._start = start
        self._end = end
        self._current = start
        self._step = step

    def add_pagination(self, pagination: DataSourcePagination | None = None):
        if pagination is None:
            return
        self._start = self._start + pagination.skip
        self._end = min(self._end, self._start + pagination.limit)
        self._current = self._start

    def generate(self) -> int:
        """
        Generate current number of sequence
        :return:
        """
        result = self._current
        self._current += self._step

        if self._current > self._end:
            raise StopIteration("Generator reached the end")

        return result

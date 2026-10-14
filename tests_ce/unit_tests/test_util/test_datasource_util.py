# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


import random
import subprocess
import sys
import textwrap
from pathlib import Path

from datamimic_ce.engine.io.api import DataSourcePagination
from datamimic_ce.engine.io.data_sources.selection import get_shuffled_data_with_cyclic


def test_shuffled_iterable_inputs_terminate_and_preserve_seeded_windows():
    # Run out of process so an exhausted one-shot input cannot hang the suite.
    subprocess.run(
        [
            sys.executable,
            "-c",
            textwrap.dedent(
                """
                from datamimic_ce.engine.io.api import DataSourcePagination
                from datamimic_ce.engine.io.data_sources.selection import get_shuffled_data_with_cyclic

                cases = [
                    (None, False, [3, 1, 0, 2]),
                    (DataSourcePagination(1, 2), False, [1, 0]),
                    (DataSourcePagination(3, 5), False, [2]),
                    (DataSourcePagination(3, 8), True, [2, 0, 2, 3, 1, 0, 1, 2]),
                    (DataSourcePagination(4, 2), False, []),
                    (DataSourcePagination(0, 0), True, []),
                ]
                for factory in (list, tuple, iter, lambda rows: (row for row in rows)):
                    for page, cyclic, expected in cases:
                        actual = get_shuffled_data_with_cyclic(factory([0, 1, 2, 3]), page, cyclic, 7)
                        assert actual == expected, (factory, actual, expected)
                        assert get_shuffled_data_with_cyclic(factory([]), page, cyclic, 7) == []
                rows = [0, 1, 2, 3]
                assert get_shuffled_data_with_cyclic(rows, None, False, 7) == [3, 1, 0, 2]
                assert rows == [0, 1, 2, 3]

                from pathlib import Path
                from tempfile import TemporaryDirectory
                from datamimic_ce.engine.runtime.api import create_run_session
                from datamimic_ce.engine.runtime.contracts import RunRequest

                with TemporaryDirectory() as directory:
                    descriptor = Path(directory) / "main.xml"
                    descriptor.write_text(
                        '<setup rngSeed="7"><generate name="rows" count="4">'
                        '<variable name="item" source="(value for value in [0, 1, 2, 3])"/>'
                        '<key name="value" type="int" script="item"/></generate></setup>',
                        encoding="utf-8",
                    )
                    request = RunRequest(descriptor_path=descriptor, test_mode=True)
                    captured = create_run_session(request).execute().captured
                    assert sorted(row["value"] for row in captured["rows"]) == [0, 1, 2, 3]
                    assert create_run_session(request).execute().captured == captured
                """
            ),
        ],
        check=True,
        timeout=15,
    )


class TestDataSourceUtil:
    _test_dir = Path(__file__).resolve().parent

    def test_small_page_len(self):
        """
        Test random distribution having page_len smaller than source_len
        :return:
        """
        page_start = 3
        page_end = 279
        page_step = 15
        page_len = page_end - page_start + 1
        source_len = 500
        source_data = list(range(source_len))
        pagination_list = [
            DataSourcePagination(skip, min(page_step, page_end + 1 - skip))
            for skip in range(page_start, page_end + 1, page_step)
        ]
        cyclic = False
        seed = random.randint(0, 100)
        print()
        assert len(get_shuffled_data_with_cyclic(source_data, pagination_list[0], cyclic, seed)) == page_step
        checking_list = []
        for pagination in pagination_list:
            shuffled_list = get_shuffled_data_with_cyclic(source_data, pagination, cyclic, seed)
            checking_list.extend(shuffled_list)
        assert len(set(checking_list)) == page_len
        assert len(checking_list) == page_len

    def test_large_page_len(self):
        """
        Test random distribution having page_len larger than source_len
        :return:
        """
        page_start = 2
        page_end = 1642
        page_step = 18
        page_end - page_start + 1
        source_len = 200
        source_data = list(range(source_len))
        pagination_list = [
            DataSourcePagination(skip, min(page_step, page_end + 1 - skip))
            for skip in range(page_start, page_end + 1, page_step)
        ]
        cyclic = False
        seed = random.randint(0, 100)
        print()
        assert len(get_shuffled_data_with_cyclic(source_data, pagination_list[0], cyclic, seed)) == page_step
        checking_list = []
        for pagination in pagination_list:
            shuffled_list = get_shuffled_data_with_cyclic(source_data, pagination, cyclic, seed)
            checking_list.extend(shuffled_list)
        assert len(set(checking_list)) == source_len - page_start
        assert len(checking_list) == source_len - page_start

    def test_small_page_len_cyclic(self):
        """
        Test random distribution having page_len smaller than source_len
        :return:
        """
        page_start = 2
        page_end = 379
        page_step = 19
        page_len = page_end - page_start + 1
        source_len = 700
        source_data = list(range(source_len))
        pagination_list = [
            DataSourcePagination(skip, min(page_step, page_end + 1 - skip))
            for skip in range(page_start, page_end + 1, page_step)
        ]
        cyclic = True
        seed = random.randint(0, 100)
        print()
        assert len(get_shuffled_data_with_cyclic(source_data, pagination_list[0], cyclic, seed)) == page_step
        checking_list = []
        for pagination in pagination_list:
            shuffled_list = get_shuffled_data_with_cyclic(source_data, pagination, cyclic, seed)
            checking_list.extend(shuffled_list)
        assert len(set(checking_list)) == page_len
        assert len(checking_list) == page_len

    def test_large_page_len_cyclic(self):
        """
        Test random distribution having page_len larger than source_len
        :return:
        """
        page_start = 5
        page_end = 2642
        page_step = 18
        page_len = page_end - page_start + 1
        source_len = 300
        source_data = list(range(source_len))
        pagination_list = [
            DataSourcePagination(skip, min(page_step, page_end + 1 - skip))
            for skip in range(page_start, page_end + 1, page_step)
        ]
        cyclic = True
        seed = random.randint(0, 100)
        print()
        assert len(get_shuffled_data_with_cyclic(source_data, pagination_list[0], cyclic, seed)) == page_step
        checking_list = []
        for pagination in pagination_list:
            shuffled_list = get_shuffled_data_with_cyclic(source_data, pagination, cyclic, seed)
            checking_list.extend(shuffled_list)
        assert len(set(checking_list)) == source_len
        assert len(checking_list) == page_len

    def test_small_source_len_cyclic(self):
        """
        Test random distribution having source_len smaller than page_len
        :return:
        """
        page_start = 5
        page_end = 2642
        page_step = 18
        page_len = page_end - page_start + 1
        source_len = 3
        source_data = list(range(source_len))
        pagination_list = [
            DataSourcePagination(skip, min(page_step, page_end + 1 - skip))
            for skip in range(page_start, page_end + 1, page_step)
        ]
        cyclic = True
        seed = random.randint(0, 100)
        print()
        assert len(get_shuffled_data_with_cyclic(source_data, pagination_list[0], cyclic, seed)) == page_step
        checking_list = []
        for pagination in pagination_list:
            shuffled_list = get_shuffled_data_with_cyclic(source_data, pagination, cyclic, seed)
            checking_list.extend(shuffled_list)
        assert len(set(checking_list)) == source_len
        assert len(checking_list) == page_len

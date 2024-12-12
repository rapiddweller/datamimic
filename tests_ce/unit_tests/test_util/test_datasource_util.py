# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


import random
from pathlib import Path

from datamimic_ce.data_sources.data_source_pagination import DataSourcePagination
from datamimic_ce.data_sources.data_source_util import DataSourceUtil


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
        assert (
            len(DataSourceUtil.get_shuffled_data_with_cyclic(source_data, pagination_list[0], cyclic, seed))
            == page_step
        )
        checking_list = []
        for pagination in pagination_list:
            shuffled_list = DataSourceUtil.get_shuffled_data_with_cyclic(source_data, pagination, cyclic, seed)
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
        assert (
            len(DataSourceUtil.get_shuffled_data_with_cyclic(source_data, pagination_list[0], cyclic, seed))
            == page_step
        )
        checking_list = []
        for pagination in pagination_list:
            shuffled_list = DataSourceUtil.get_shuffled_data_with_cyclic(source_data, pagination, cyclic, seed)
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
        assert (
            len(DataSourceUtil.get_shuffled_data_with_cyclic(source_data, pagination_list[0], cyclic, seed))
            == page_step
        )
        checking_list = []
        for pagination in pagination_list:
            shuffled_list = DataSourceUtil.get_shuffled_data_with_cyclic(source_data, pagination, cyclic, seed)
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
        assert (
            len(DataSourceUtil.get_shuffled_data_with_cyclic(source_data, pagination_list[0], cyclic, seed))
            == page_step
        )
        checking_list = []
        for pagination in pagination_list:
            shuffled_list = DataSourceUtil.get_shuffled_data_with_cyclic(source_data, pagination, cyclic, seed)
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
        assert (
            len(DataSourceUtil.get_shuffled_data_with_cyclic(source_data, pagination_list[0], cyclic, seed))
            == page_step
        )
        checking_list = []
        for pagination in pagination_list:
            shuffled_list = DataSourceUtil.get_shuffled_data_with_cyclic(source_data, pagination, cyclic, seed)
            checking_list.extend(shuffled_list)
        assert len(set(checking_list)) == source_len
        assert len(checking_list) == page_len

# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from datamimic_ce.engine.dsl.vocabulary.product_identity import capture_product_name
from datamimic_ce.engine.io.contracts import Exporter


class TestResultExporter(Exporter):
    """
    Capture GenIterTask result for testing
    """

    __test__ = False  # name starts with "Test" — tell pytest this is not a test class

    def __init__(self) -> None:
        self._storage: dict[str, list[object]] = {}

    def consume(self, product: tuple) -> None:
        """
        Write data into storage
        :param product:
        :return:
        """
        name, data, *_ = product
        name = capture_product_name(name)
        self._storage[name] = self._storage.get(name, []) + data

    def get_result(self) -> dict[str, list[object]]:
        """
        Capture data from storage

        :return:
        """
        return self._storage

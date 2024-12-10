# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from datamimic_ce.exporters.exporter import Exporter


class TestResultExporter(Exporter):
    """
    Capture GenIterTask result for testing
    """

    def __init__(self):
        self._storage = {}

    def consume(self, product: tuple) -> None:
        """
        Write data into storage
        :param product:
        :return:
        """
        name, data, *_ = product
        name = name.split("|", 1)[-1].strip() if "|" in name else name
        self._storage[name] = self._storage.get(name, []) + data

    def get_result(self) -> dict[str, list[dict]]:
        """
        Capture data from storage

        :return:
        """
        return self._storage

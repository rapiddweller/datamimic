# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.exporters.exporter import Exporter


class ConsoleExporter(Exporter):
    """
    Print data to console
    """

    def consume(self, product: tuple):
        """ "
        Print data to console
        """
        print()
        name = product[0]
        data = product[1]
        for row in data:
            print(f"{name}: {row}")

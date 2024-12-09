# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/

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

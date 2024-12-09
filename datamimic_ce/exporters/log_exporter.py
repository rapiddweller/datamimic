# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/

from datamimic_ce.exporters.exporter import Exporter
from datamimic_ce.logger import logger


class LogExporter(Exporter):
    """
    Put data to logger
    """

    # Limit the amount of data to be print
    MAX_ITEM_TO_LOG: int = 100

    def consume(self, product: tuple):
        """ "
        Put data to logger
        """
        name = product[0]
        data = product[1]

        logger.info(f"{ self.__class__.__name__ } - Start")
        for row in data[: self.MAX_ITEM_TO_LOG]:
            logger.info(f"{name}: {row}")

        if len(data) > self.MAX_ITEM_TO_LOG:
            logger.info(f"{self.__class__.__name__} {name}: {len(data) - self.MAX_ITEM_TO_LOG} rows are not printed")
            logger.info(
                f"{self.__class__.__name__} has a default limit of {self.MAX_ITEM_TO_LOG} items.For larger datasets, consider using other exporter such as CSV or TXT."
            )

        logger.info(f"{ self.__class__.__name__ } - Close")

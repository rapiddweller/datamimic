# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/

import random

from datamimic_ce.generators.generator import Generator
from datamimic_ce.logger import logger


class DepartmentNameGenerator(Generator):
    def __init__(self, locale: str | None = "en") -> None:
        # Default department data (en)
        self._department_data = [
            "Accounting",
            "Human Resources",
            "Sales",
            "Marketing",
            "IT",
            "Manufacturing",
            "Logistics",
            "Legal",
        ]
        sp_locale = ("de", "en")
        if locale == "de":
            self._department_data = [
                "Accounting",
                "Human Resources",
                "Vertrieb",
                "Marketing",
                "IT",
                "Logistik",
                "Recht",
            ]
        elif locale not in sp_locale:
            logger.info(f"Department name does not support locale '{locale}'. Change to department_en data")

    def generate(self) -> str:
        return random.choice(self._department_data)

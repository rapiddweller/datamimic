# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

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

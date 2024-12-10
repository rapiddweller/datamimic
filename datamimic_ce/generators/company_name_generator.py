# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import random

from datamimic_ce.generators.generator import Generator


class CompanyNameGenerator(Generator):
    def __init__(self) -> None:
        self._tech_1 = [
            "Auto",
            "Bit",
            "Book",
            "Click",
            "Code",
            "Compu",
            "Cyber",
            "Data",
            "Digi",
            "Dyna",
            "Free",
            "Giga",
            "Home",
            "Hot",
            "Info",
            "Link",
            "Micro",
            "Mind",
            "My",
            "Nano",
            "Object",
            "Power",
            "Real",
            "Silicon",
            "Smart",
            "Solar",
            "Tech",
            "Tele",
            "Trade",
            "Venture",
            "Web",
            "Wire",
            "Your",
        ]
        self._tech_2 = [
            "Base",
            "Bit",
            "Bot",
            "Box",
            "Card",
            "Cast",
            "City",
            "Com",
            "Direct",
            "Flash",
            "Forge",
            "Mart",
            "Net",
            "ology",
            "Point",
            "Quest",
            "Scape",
            "Scout",
            "Serve",
            "Set",
            "Shop",
            "Space",
            "Sphere",
            "Soft",
            "Star",
            "Station",
            "Systems",
            "Tech",
            "Vision",
            "Ware",
            "Wire",
            "Works",
            "World",
            "Zone",
        ]

    def generate(self) -> str:
        return f"{random.choice(self._tech_1)}{random.choice(self._tech_2)}"

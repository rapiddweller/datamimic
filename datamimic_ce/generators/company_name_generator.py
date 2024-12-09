# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/

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

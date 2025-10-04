# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import random

from datamimic_ce.domains.domain_core.base_literal_generator import BaseLiteralGenerator


class CompanyNameGenerator(BaseLiteralGenerator):
    def __init__(self, rng: random.Random | None = None) -> None:
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
        self._rng: random.Random = rng or random.Random()

    def generate(self) -> str:
        return f"{self._rng.choice(self._tech_1)}{self._rng.choice(self._tech_2)}"

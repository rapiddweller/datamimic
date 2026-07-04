"""Custom components for the python-seam showcase. Loaded into the descriptor
context by <execute uri="script/components.scr.py"/>; afterwards the classes are
addressable in the DSL as generator="MaskedPanGenerator()" and
converter="RiskBucketConverter()"."""

import random

from datamimic_ce.converter.converter import Converter
from datamimic_ce.domains.domain_core.base_literal_generator import BaseLiteralGenerator


class MaskedPanGenerator(BaseLiteralGenerator):
    """A PCI-style masked card number: first six and last four digits visible."""

    def generate(self) -> str:
        bin_prefix = random.choice(["411111", "510510", "340000"])
        last4 = f"{random.randint(0, 9999):04d}"
        return f"{bin_prefix}******{last4}"


class RiskBucketConverter(Converter):
    """Map a numeric credit limit onto a reporting bucket."""

    def convert(self, value: int) -> str:
        if value >= 10000:
            return "high"
        if value >= 3000:
            return "medium"
        return "low"

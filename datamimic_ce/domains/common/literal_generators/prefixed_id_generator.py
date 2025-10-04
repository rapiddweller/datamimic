# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.domains.common.literal_generators.string_generator import StringGenerator
from datamimic_ce.domains.domain_core.base_literal_generator import BaseLiteralGenerator


class PrefixedIdGenerator(BaseLiteralGenerator):
    """
    Generate an ID composed of a prefix and a regex-defined body.

    Examples:
    - prefix="DOC", body_pattern="[0-9A-F]{8}", separator="-" -> "DOC-5A3EF0C1"
    - prefix="ORD", body_pattern="[A-Z0-9]{8}", separator=""  -> "ORD7ZG2QH4C"
    """

    def __init__(self, prefix: str, body_pattern: str, separator: str = "-") -> None:
        self._prefix = prefix
        self._body_pattern = body_pattern
        self._sep = separator

    def generate(self) -> str:
        body = StringGenerator.rnd_str_from_regex(self._body_pattern)
        return f"{self._prefix}{self._sep}{body}"

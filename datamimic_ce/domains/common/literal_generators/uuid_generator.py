# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import uuid

from datamimic_ce.domain_core.base_literal_generator import BaseLiteralGenerator


class UUIDGenerator(BaseLiteralGenerator):
    """
    Generate an uuid (v4 by default)
    """

    def generate(self) -> str:
        """
        Returns: a uuidv4 as string
        """
        return str(uuid.uuid4())

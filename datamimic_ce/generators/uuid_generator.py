# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/

import uuid

from datamimic_ce.generators.generator import Generator


class UUIDGenerator(Generator):
    """
    Generate an uuid (v4 by default)
    """

    def generate(self) -> str:
        """
        Returns: a uuidv4 as string
        """
        return str(uuid.uuid4())

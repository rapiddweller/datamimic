# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from abc import ABC, abstractmethod
from typing import Any


class Generator(ABC):
    @abstractmethod
    def generate(self) -> Any:
        """
        Generate data and set this value to current product
        :param ctx:
        :return:
        """

# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from abc import ABC, abstractmethod


class BaseLiteralGenerator(ABC):
    """
    Base class for all literal generators (only generate literal values)
    """

    # Generators are cached in the root context by default. Set
    # ``cache_in_root = False`` in subclasses to opt out of global caching.
    cache_in_root: bool = True

    @abstractmethod
    def generate(self):
        """
        Generate a random literal value.
        """
        raise NotImplementedError("Subclasses must implement this method")

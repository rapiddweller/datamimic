# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from abc import ABC, abstractmethod


class BaseLiteralGenerator(ABC):
    """
    Base class for all literal generators (only generate literal values)
    """

    @abstractmethod
    def generate(self):
        """
        Generate a random literal value.
        """
        raise NotImplementedError("Subclasses must implement this method")


class BaseLiteralGenerator:
    """Base generator for literal values following specific distributions.

    This class provides mechanisms to generate primitive data types according to
    configured probability distributions.
    """

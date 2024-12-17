# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from abc import ABC, abstractmethod


class Credential(ABC):
    """
    Abstract base class for credentials.

    This class serves as a base class for different types of credentials.
    It inherits from Python's built-in ABC (Abstract Base Class) module,
    which allows the creation of abstract base classes.
    """

    @abstractmethod
    def check_credentials(self):
        """
        Check the credentials.

        This method should be implemented by subclasses to check the credentials.
        """

    @abstractmethod
    def get_credentials(self):
        """
        Returns the credentials.

        This method should be implemented by subclasses to return the credentials.
        """
